from .update_b50 import MaimaiDependencyError, MaimaiUpdateService, MessageRecaller, SgidFreshness, SyncResult, extract_sgid, get_service as _get_service, is_probable_sgid, is_version_at_least as _is_version_at_least, parse_version as _parse_version, recall_current_message as _recall_current_message, sgid_issued_at, sgwcmaid_update_handler, validate_sgid_for_one_time_use as _validate_sgid_for_one_time_use, validate_sgid_freshness

MIN_MAIMAI_PY = (1, 4, 2)
MIN_MAIMAI_FFI = (0, 7, 0)

__all__ = [
    "MaimaiDependencyError",
    "MaimaiUpdateService",
    "MessageRecaller",
    "SgidFreshness",
    "SyncResult",
    "extract_sgid",
    "is_probable_sgid",
    "sgid_issued_at",
    "sgwcmaid_update_handler",
    "validate_sgid_freshness",
]
