"""Explicit CT2 completion gate for future CT3 consumers."""

from cat_treaty.ct2_models import (
    InuringCompletionStatus,
    InuringWaterfallResult,
)


_ELIGIBLE_STATUSES = frozenset(
    {
        InuringCompletionStatus.COMPLETE,
        InuringCompletionStatus.COMPLETE_NO_INURING_COVERS,
    }
)


def require_ct3_eligible_waterfall(
    result: InuringWaterfallResult,
) -> InuringWaterfallResult:
    """Accept only a completed CT2 waterfall, never a raw loss substitute."""

    if not isinstance(result, InuringWaterfallResult):
        raise TypeError(
            "CT3 requires a completed InuringWaterfallResult; raw gross or "
            "subject loss is not eligible"
        )
    if result.completion_status not in _ELIGIBLE_STATUSES:
        raise ValueError("CT2 waterfall is not complete")
    return result
