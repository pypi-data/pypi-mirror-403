from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class EntryContextCounts(_message.Message):
    __slots__ = ()
    ATTEMPTS_FIELD_NUMBER: _ClassVar[int]
    WATCHED_FIELD_NUMBER: _ClassVar[int]
    attempts: int
    watched: int
    def __init__(self, attempts: _Optional[int] = ..., watched: _Optional[int] = ...) -> None: ...

class SelectCounts(_message.Message):
    __slots__ = ()
    TOTAL_SELECTS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_SELECTS_AND_WATCHED_FIELD_NUMBER: _ClassVar[int]
    TOTAL_BROWSED_FIELD_NUMBER: _ClassVar[int]
    total_selects: int
    total_selects_and_watched: int
    total_browsed: int
    def __init__(self, total_selects: _Optional[int] = ..., total_selects_and_watched: _Optional[int] = ..., total_browsed: _Optional[int] = ...) -> None: ...

class EntryContextPWatched(_message.Message):
    __slots__ = ()
    AUTOPLAY_FIELD_NUMBER: _ClassVar[int]
    SEL_THUMB_FIELD_NUMBER: _ClassVar[int]
    CHOOSE_NEXT_FIELD_NUMBER: _ClassVar[int]
    CH_SWTCH_FIELD_NUMBER: _ClassVar[int]
    LAUNCH_FIRST_IN_SESSION_FIELD_NUMBER: _ClassVar[int]
    autoplay: EntryContextCounts
    sel_thumb: EntryContextCounts
    choose_next: EntryContextCounts
    ch_swtch: EntryContextCounts
    launch_first_in_session: EntryContextCounts
    def __init__(self, autoplay: _Optional[_Union[EntryContextCounts, _Mapping]] = ..., sel_thumb: _Optional[_Union[EntryContextCounts, _Mapping]] = ..., choose_next: _Optional[_Union[EntryContextCounts, _Mapping]] = ..., ch_swtch: _Optional[_Union[EntryContextCounts, _Mapping]] = ..., launch_first_in_session: _Optional[_Union[EntryContextCounts, _Mapping]] = ...) -> None: ...

class PositionPSelect(_message.Message):
    __slots__ = ()
    FIRST_POS_FIELD_NUMBER: _ClassVar[int]
    SECOND_POS_FIELD_NUMBER: _ClassVar[int]
    THIRD_POS_FIELD_NUMBER: _ClassVar[int]
    REST_POS_FIELD_NUMBER: _ClassVar[int]
    first_pos: SelectCounts
    second_pos: SelectCounts
    third_pos: SelectCounts
    rest_pos: SelectCounts
    def __init__(self, first_pos: _Optional[_Union[SelectCounts, _Mapping]] = ..., second_pos: _Optional[_Union[SelectCounts, _Mapping]] = ..., third_pos: _Optional[_Union[SelectCounts, _Mapping]] = ..., rest_pos: _Optional[_Union[SelectCounts, _Mapping]] = ...) -> None: ...

class BrowsedDebiasedPositionPSelects(_message.Message):
    __slots__ = ()
    UP_TO_4_BROWSED_FIELD_NUMBER: _ClassVar[int]
    ALL_BROWSED_FIELD_NUMBER: _ClassVar[int]
    up_to_4_browsed: PositionPSelect
    all_browsed: PositionPSelect
    def __init__(self, up_to_4_browsed: _Optional[_Union[PositionPSelect, _Mapping]] = ..., all_browsed: _Optional[_Union[PositionPSelect, _Mapping]] = ...) -> None: ...

class StreamPSelect(_message.Message):
    __slots__ = ()
    VERSION_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    version: int
    data: BrowsedDebiasedPositionPSelects
    def __init__(self, version: _Optional[int] = ..., data: _Optional[_Union[BrowsedDebiasedPositionPSelects, _Mapping]] = ...) -> None: ...

class StreamPWatched(_message.Message):
    __slots__ = ()
    VERSION_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    version: int
    data: EntryContextPWatched
    def __init__(self, version: _Optional[int] = ..., data: _Optional[_Union[EntryContextPWatched, _Mapping]] = ...) -> None: ...

class UserPWatched(_message.Message):
    __slots__ = ()
    VERSION_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    version: int
    data: EntryContextPWatched
    def __init__(self, version: _Optional[int] = ..., data: _Optional[_Union[EntryContextPWatched, _Mapping]] = ...) -> None: ...

class UserPersonalizingPWatched(_message.Message):
    __slots__ = ()
    class DataEntry(_message.Message):
        __slots__ = ()
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: EntryContextPWatched
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[EntryContextPWatched, _Mapping]] = ...) -> None: ...
    VERSION_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    version: int
    data: _containers.MessageMap[str, EntryContextPWatched]
    def __init__(self, version: _Optional[int] = ..., data: _Optional[_Mapping[str, EntryContextPWatched]] = ...) -> None: ...

class UserPSelect(_message.Message):
    __slots__ = ()
    VERSION_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    version: int
    data: BrowsedDebiasedPositionPSelects
    def __init__(self, version: _Optional[int] = ..., data: _Optional[_Union[BrowsedDebiasedPositionPSelects, _Mapping]] = ...) -> None: ...

class UserPersonalizingPSelect(_message.Message):
    __slots__ = ()
    class DataEntry(_message.Message):
        __slots__ = ()
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: BrowsedDebiasedPositionPSelects
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[BrowsedDebiasedPositionPSelects, _Mapping]] = ...) -> None: ...
    VERSION_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    version: int
    data: _containers.MessageMap[str, BrowsedDebiasedPositionPSelects]
    def __init__(self, version: _Optional[int] = ..., data: _Optional[_Mapping[str, BrowsedDebiasedPositionPSelects]] = ...) -> None: ...

class StreamSimilarityScores(_message.Message):
    __slots__ = ()
    class DataEntry(_message.Message):
        __slots__ = ()
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    VERSION_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    version: int
    data: _containers.ScalarMap[str, float]
    def __init__(self, version: _Optional[int] = ..., data: _Optional[_Mapping[str, float]] = ...) -> None: ...
