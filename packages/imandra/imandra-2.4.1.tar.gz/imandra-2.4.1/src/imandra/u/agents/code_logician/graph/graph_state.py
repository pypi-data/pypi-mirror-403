from __future__ import annotations

import json
import textwrap
from collections.abc import AsyncIterator
from dataclasses import asdict
from pathlib import Path
from typing import Any, Never, Self, assert_never, cast

from langchain_core.runnables.config import RunnableConfig
from langgraph.graph.state import CompiledStateGraph
from langgraph.pregel.remote import RemoteGraph
from langgraph.types import Command as LGCommand
from pydantic import BaseModel, Field, field_validator
from rich.console import ConsoleRenderable

from ..base import (
    FormalizationState,
)
from ..command import (
    Command,
    InitStateCommand,
    RootCommand,
)
from ..runtime_context import ContextSchema
from ..task import Interaction


class GraphState(BaseModel):
    """
    Graph state of Code Logician
    """

    steps: list[Interaction] = Field(
        default_factory=list, description="Commands and their trajectories"
    )
    step_i: int | None = Field(default=None, description="Index of the current step")
    info: dict = Field(
        default_factory=dict, description="Internal information shared between nodes"
    )

    @property
    def last_fstate(self) -> FormalizationState | None:
        """Return the last formalization state"""
        last_fstate = None
        for step in self.steps:
            if step.last_fstate is not None:
                last_fstate = step.last_fstate
        return last_fstate

    @field_validator("steps", mode="after")
    @classmethod
    def last_fstate_cannot_be_later_than_the_first_pending_step(
        cls, steps: list[Interaction]
    ) -> list[Interaction]:
        step_i = next(
            (
                i
                for i, step in enumerate(steps)
                if step.task is not None and step.task.status == "pending"
            ),
            None,
        )
        if step_i is None:
            return steps

        for step in steps[step_i + 1 :]:
            if step.last_fstate is not None:
                raise ValueError(
                    "Last fstate cannot be later than the first pending step"
                )
        return steps

    def add_commands(
        self,
        commands: Command | list[Command],
    ) -> Self:
        """Return a new GraphState with the added commands"""

        def normalize_command(cmd: Command) -> RootCommand:
            """Normalize a Command to RootCommand"""
            if isinstance(cmd, RootCommand):
                return cmd
            else:
                return RootCommand(root=cmd)

        match commands:
            case command if isinstance(command, Command):
                new_steps = [
                    *self.steps,
                    Interaction(command=normalize_command(command)),
                ]
                update = {"steps": new_steps}
            case list() as commands:
                new_steps = [
                    *self.steps,
                    *[Interaction(command=normalize_command(cmd)) for cmd in commands],
                ]
                update = {"steps": new_steps}
            case _:
                raise ValueError(f"Invalid command: {commands}")
        return self.__class__.model_validate(self.model_dump() | update)

    def init_with_file(self, file_path: str, src_lang: str) -> GraphState:
        content = Path(file_path).read_text()
        steps = [
            Interaction(
                command=RootCommand(
                    root=InitStateCommand(
                        src_code=content,
                        src_lang=src_lang,
                    )
                )
            )
        ]
        return GraphState(steps=steps)

    async def stream(
        self,
        graph: CompiledStateGraph[GraphState, ContextSchema, GraphState, GraphState]
        | RemoteGraph,
        config: RunnableConfig | None = None,
        resume: LGCommand | None = None,
    ) -> AsyncIterator[dict[str, str] | tuple[Self, dict[str, Any] | None]]:
        """Stream the graph execution.

        Yields:
            - a dictionary of {"step_name": str} as intermediate progress
            - (GraphState, updates) as final result

        Example:
        ```python
        progress: dict[str, str] | None = None
        result: tuple[GraphState, dict[str, Any] | None] | None = None
        async for item in graph_state.stream(graph):
            if isinstance(item, dict):
                progress = item
                print(f"Progress: {progress}")
            elif isinstance(item, tuple):
                result = item
        assert result is not None
        assert progress is not None
        gs: GraphState
        gs, _ = result
        ```
        """
        config = _resolve_graph_config(graph, config)

        astream_kwargs: dict[str, Any] = {}
        if not isinstance(graph, RemoteGraph):
            assert "configurable" in config
            astream_kwargs["context"] = config["configurable"]

        if resume is None:
            inputs = json.loads(self.model_dump_json())
        else:
            inputs = resume

        values: dict[str, Any] | None = None
        updates: dict[str, Any] | None = None
        async for chunk in graph.astream(
            inputs,
            config=config,
            stream_mode=["values", "updates", "custom"],
            **astream_kwargs,
        ):
            mode, data = chunk
            match mode:
                case "custom":
                    data = cast(dict[str, str], data)
                    yield data
                case "values":
                    values = cast(dict[Any, Any], data)
                case "updates":
                    updates = cast(dict[str, Any], data)
                case _ as unreachable:
                    unreachable = cast(Never, unreachable)
                    assert_never(unreachable)
        gs = self.__class__.model_validate(values)

        if updates is not None and "__interrupt__" not in updates:
            updates = None
        yield (gs, updates)

    async def run(
        self,
        graph: CompiledStateGraph[GraphState, ContextSchema, GraphState, GraphState]
        | RemoteGraph,
        config: RunnableConfig | None = None,
        resume: LGCommand | None = None,
    ) -> tuple[Self, dict | None]:
        """Call the graph with the given config.

        Args:
            graph: The compiled graph or remote graph to execute
            config: Optional runnable configuration
            resume: Optional LangGraph Command to resume from an interrupt

        Returns:
            A tuple of (final_graph_state, interrupt_updates), where interrupt_updates
            is None if the graph completed without interruption, or a dict containing
            interrupt information if the graph was interrupted.
        """
        result: tuple[Self, dict[str, Any] | None] | None = None
        async for chunk in self.stream(graph, config, resume):
            if isinstance(chunk, tuple):
                result = chunk
        assert result is not None
        return result

    def __rich__(self) -> ConsoleRenderable:
        return Interaction.render_interactions_summary(self.steps)

    def __repr__(self):
        s = ""
        s += "Graph State:\n\n"
        s += f"{len(self.steps)} Steps\n\n"
        for i, step in enumerate(self.steps, 1):
            s += f"Step {i}:\n\n"
            s += textwrap.indent(step.__repr__(), "  ")
            s += "\n\n"
            s += "=" * 40 + "\n\n"

        return s


def _resolve_graph_config(
    graph: CompiledStateGraph[GraphState, ContextSchema, GraphState, GraphState]
    | RemoteGraph,
    config: RunnableConfig | None = None,
) -> RunnableConfig:
    """Resolve the graph config

    - Priority: user-provided > graph-bound > default
    """

    config = RunnableConfig(**(config or {}))
    runtime_context = config.get("configurable", {})

    default_runtime_context = asdict(ContextSchema())
    graph_bound_config = getattr(graph, "config", {}) or {}
    graph_bound_runtime_context = graph_bound_config.get("configurable", {})
    runtime_context = (
        default_runtime_context | graph_bound_runtime_context | runtime_context
    )
    config["configurable"] = runtime_context
    return config
