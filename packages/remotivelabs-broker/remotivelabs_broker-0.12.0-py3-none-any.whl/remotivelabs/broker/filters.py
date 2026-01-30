"""
It is possible to filter frames and signals using filter predicates. A filter predicate is any callable that takes a
`FrameInfo` or `SignalInfo` object and returns a boolean indicating whether the object matches the filter criteria.

All filters have an `exclude` flag to indicate whether matches should be excluded (`True`) or
included (`False`, default). Filters are callable and can be passed to Python built-in functions that
expect a predicate, such as `filter()`, `any()`, or `all()`. The snippet below shows examples
using `filter()`:

Filter Strategy:

    The `filter_recursive()` function applies frame and signal filters with context-dependent behavior.
    Frame filtering determines eligibility, then signal filtering applies differently based on frame
    inclusion: included frames start with all signals (exclude-only), excluded frames require explicit
    signal inclusion. Exclusion filters always take priority over inclusion filters.

Examples:

```python
.. include:: ./_docs/snippets/filters.py
```

"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol, Sequence, TypeGuard, Union, overload, runtime_checkable

from remotivelabs.broker.frame import FrameInfo
from remotivelabs.broker.signal import SignalInfo


@runtime_checkable
class FrameFilterPredicate(Protocol):
    @property
    def exclude(self) -> bool: ...

    @property
    def type(self) -> Literal["frame", "any"]: ...

    def __call__(self, info: FrameInfo) -> bool: ...


@runtime_checkable
class SignalFilterPredicate(Protocol):
    @property
    def exclude(self) -> bool: ...

    @property
    def type(self) -> Literal["signal", "any"]: ...

    def __call__(self, info: SignalInfo) -> bool: ...


# Public filter types
FilterLike = Union[FrameFilterPredicate, SignalFilterPredicate]


def is_frame_filter(filter: object) -> TypeGuard[FrameFilterPredicate]:
    # A filter is a frame filter if it has type "frame" or "any",
    # and it can be called with FrameInfo
    return hasattr(filter, "type") and getattr(filter, "type", None) in ("frame", "any")


def is_signal_filter(filter: object) -> TypeGuard[SignalFilterPredicate]:
    # A filter is a signal filter if it has type "signal" or "any",
    # and it can be called with SignalInfo
    return hasattr(filter, "type") and getattr(filter, "type", None) in ("signal", "any")


def is_filter(obj: object) -> TypeGuard[FilterLike]:
    return hasattr(obj, "type") and getattr(obj, "type", None) in ("frame", "signal", "any")


@dataclass(frozen=True)
class AllFramesFilter:
    exclude: bool = False
    type: Literal["frame"] = "frame"

    def __call__(self, info: FrameInfo) -> bool:  # noqa: ARG002
        return not self.exclude


@dataclass(frozen=True)
class FrameFilter:
    frame_name: str
    exclude: bool = False
    type: Literal["frame"] = "frame"

    def __call__(self, info: FrameInfo) -> bool:
        matches = info.name == self.frame_name
        return not matches if self.exclude else matches


@dataclass(frozen=True)
class SignalFilter:
    signal_name: str
    exclude: bool = False
    type: Literal["signal"] = "signal"

    def __call__(self, info: SignalInfo) -> bool:
        matches = info.name == self.signal_name
        return not matches if self.exclude else matches


@dataclass(frozen=True)
class ReceiverFilter:
    ecu_name: str
    exclude: bool = False
    type: Literal["any"] = "any"

    @overload
    def __call__(self, info: FrameInfo) -> bool: ...

    @overload
    def __call__(self, info: SignalInfo) -> bool: ...

    def __call__(self, info: FrameInfo | SignalInfo) -> bool:
        if isinstance(info, FrameInfo):
            receivers = set(info.receiver)
            receivers.update(r for sig in info.signals.values() for r in sig.receiver)
            matches = self.ecu_name in receivers
        elif isinstance(info, SignalInfo):
            matches = self.ecu_name in info.receiver
        else:
            matches = False

        return not matches if self.exclude else matches


@dataclass(frozen=True)
class SenderFilter:
    ecu_name: str
    exclude: bool = False
    type: Literal["any"] = "any"

    @overload
    def __call__(self, info: FrameInfo) -> bool: ...

    @overload
    def __call__(self, info: SignalInfo) -> bool: ...

    def __call__(self, info: FrameInfo | SignalInfo) -> bool:
        if isinstance(info, FrameInfo):
            senders = set(info.sender)
            senders.update(s for sig in info.signals.values() for s in sig.sender)
            matches = self.ecu_name in senders
        elif isinstance(info, SignalInfo):
            matches = self.ecu_name in info.sender
        else:
            matches = False

        return not matches if self.exclude else matches


def apply_frame_filters(frame_info: FrameInfo, frame_filters: Sequence[FrameFilterPredicate]) -> FrameInfo | None:
    include_filters = [f for f in frame_filters if not f.exclude]
    exclude_filters = [f for f in frame_filters if f.exclude]

    # Check exclusions first (they have priority)
    frame_excluded = any(not f(frame_info) for f in exclude_filters)
    if frame_excluded:
        return None

    # And then inclusions
    if any(f(frame_info) for f in include_filters):
        return frame_info

    # No match, no inclusion
    return None


def apply_signal_filters(
    signal_infos: Sequence[SignalInfo], signal_filters: Sequence[SignalFilterPredicate], include_by_default: bool
) -> list[SignalInfo]:
    include_filters = [f for f in signal_filters if not f.exclude]
    exclude_filters = [f for f in signal_filters if f.exclude]

    included_signals = []
    for signal_info in signal_infos:
        # Check exclusion filters first (they have priority)
        is_excluded = any(not f(signal_info) for f in exclude_filters)
        if is_excluded:
            continue

        # Handle inclusion logic
        if include_by_default:
            # Include unless explicitly excluded (already handled above)
            included_signals.append(signal_info)
        else:
            # Must be explicitly included by an inclusion filter
            is_included = any(f(signal_info) for f in include_filters)
            if is_included:
                included_signals.append(signal_info)

    return included_signals


def filter_recursive(frame_info: FrameInfo, filters: Sequence[FilterLike]) -> FrameInfo | None:
    """
    Apply filters to a FrameInfo and return filtered result or None.

    Filter Strategy:
        Frame filtering determines if the frame should be considered at all.
        Signal filtering then determines which signals to include, with behavior
        depending on frame inclusion:
        - Frame included: Include all signals except those explicitly excluded
        - Frame excluded: Only include signals that are explicitly included
        - No filters: Returns None (nothing to subscribe to)

    Exclusion Priority:
        Exclusion filters (exclude=True) always take priority over inclusion filters
        for both frames and signals.

    Returns: Filtered FrameInfo with matching signals, or None if no matches
    """
    frame_filters = [f for f in filters if is_frame_filter(f)]
    signal_filters = [f for f in filters if is_signal_filter(f)]

    # If we have no filters, there is nothing to subscribe to
    if not frame_filters and not signal_filters:
        return None

    # Check if frame passes frame filters
    # If frame filters exist, frame must pass at least one include filter AND not be excluded
    frame_included = bool(apply_frame_filters(frame_info, frame_filters))

    # If frame is excluded and we have no signal filters, exclude entirely
    if not frame_included and not signal_filters:
        return None

    # If frame is included and no signal filters, include all signals
    if frame_included and not signal_filters:
        return frame_info

    # Apply signal filters
    # If frame is included, start with all signals and apply exclusions (include_by_default=True)
    # If frame is excluded, only include signals that are explicitly included (include_by_default=False)
    included_signals = apply_signal_filters(list(frame_info.signals.values()), signal_filters, include_by_default=frame_included)
    if not included_signals:
        # No signals match, exclude the whole frame
        return None

    # Return frame with filtered signals
    return FrameInfo(
        name=frame_info.name,
        namespace=frame_info.namespace,
        sender=frame_info.sender,
        receiver=frame_info.receiver,
        signals={sig.name: sig for sig in included_signals},
        cycle_time_millis=frame_info.cycle_time_millis,
    )
