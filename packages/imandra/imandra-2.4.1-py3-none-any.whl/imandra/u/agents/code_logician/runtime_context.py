import uuid
from dataclasses import asdict, dataclass, field
from typing import Any

from langgraph.config import get_config


@dataclass
class ContextSchema:
    thread_id: str = field(default_factory=lambda: f"thread_{str(uuid.uuid4())[:8]}")
    cache_prompt: bool = True
    refactoring_min_lines: int = 50
    use_batch_refactoring: bool = True
    fdb_n_conversion_examples: int = 5
    fdb_correction_n_api_reference_query: int = 2
    fdb_correction_n_api_reference_per_query: int = 5
    fdb_correction_n_suggestion_per_error: int = 3
    fdb_correction_n_error_to_search: int = 2

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def get_imandra_api_key() -> str | None:
    """Get the API key from auth"""
    try:
        config = get_config()
        user_config = config.get("configurable", {}).get("langgraph_auth_user", {})
        return user_config.get("imandra_api_key")
    except RuntimeError as e:
        if str(e) == "Called get_config outside of a runnable context":
            return None
        raise e
