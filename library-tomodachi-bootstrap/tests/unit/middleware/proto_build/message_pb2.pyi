"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""
import builtins
import google.protobuf.descriptor
import google.protobuf.message
import sys

if sys.version_info >= (3, 8):
    import typing as typing_extensions
else:
    import typing_extensions

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing_extensions.final
class MessageWithCorrelationId(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    EVENT_ID_FIELD_NUMBER: builtins.int
    CORRELATION_ID_FIELD_NUMBER: builtins.int
    event_id: builtins.str
    correlation_id: builtins.str
    def __init__(
        self,
        *,
        event_id: builtins.str = ...,
        correlation_id: builtins.str = ...,
    ) -> None: ...
    def ClearField(
        self, field_name: typing_extensions.Literal["correlation_id", b"correlation_id", "event_id", b"event_id"]
    ) -> None: ...  # noqa # pylint: disable=line-too-long

global___MessageWithCorrelationId = MessageWithCorrelationId

@typing_extensions.final
class MessageWithoutCorrelationId(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    EVENT_ID_FIELD_NUMBER: builtins.int
    event_id: builtins.str
    def __init__(
        self,
        *,
        event_id: builtins.str = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["event_id", b"event_id"]) -> None: ...

global___MessageWithoutCorrelationId = MessageWithoutCorrelationId