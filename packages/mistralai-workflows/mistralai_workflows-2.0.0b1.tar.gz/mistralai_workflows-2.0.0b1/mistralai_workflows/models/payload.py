import base64
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class EncodedPayloadOptions(StrEnum):
    OFFLOADED = "offloaded"
    ENCRYPTED = "encrypted"
    PARTIALLY_ENCRYPTED = "encrypted-partial"


class WorkflowContext(BaseModel):
    namespace: str
    execution_id: str
    parent_workflow_exec_id: str | None = None
    root_workflow_exec_id: str | None = None


class EncodedPayload(BaseModel):
    context: WorkflowContext
    encoding_options: list[EncodedPayloadOptions] = Field(description="The encoding of the payload", default=[])
    payload: bytes = Field(description="The encoded payload")


class EncryptableFieldTypes(StrEnum):
    STRING = "__encrypted_str__"


class EncryptedStrField(BaseModel):
    field_type: Literal[EncryptableFieldTypes.STRING] = EncryptableFieldTypes.STRING
    data: str


class NetworkEncodedBase(BaseModel):
    b64payload: str = Field(description="The encoded payload")
    encoding_options: list[EncodedPayloadOptions] = Field(description="The encoding of the payload", default=[])


class PayloadMetadataKeys(StrEnum):
    ENCODING = "encoding"
    ENCODING_ORIGINAL = "encoding-orig"
    NAMESPACE = "namespace"
    EXECUTION_ID = "execution_id"
    PARENT_WORKFLOW_EXEC_ID = "parent_workflow_exec_id"
    ROOT_WORKFLOW_EXEC_ID = "root_workflow_exec_id"
    EMPTY_PAYLOAD = "empty_payload"
    ENCODING_OPTIONS = "encoding_options"

    IS_UNENCODED_MEMO = "is_unencoded_memo"


class NetworkEncodedInput(NetworkEncodedBase):
    empty: bool = Field(description="Whether the payload is empty", default=False)

    def to_encoded_payload(self, namespace: str, execution_id: str) -> EncodedPayload:
        return EncodedPayload(
            payload=base64.b64decode(self.b64payload),
            encoding_options=self.encoding_options,
            context=WorkflowContext(
                namespace=namespace,
                execution_id=execution_id,
            ),
        )

    @staticmethod
    def from_encoded_payload(encoded_payload: EncodedPayload) -> "NetworkEncodedInput":
        return NetworkEncodedInput(
            b64payload=base64.b64encode(encoded_payload.payload).decode("utf-8"),
            encoding_options=encoded_payload.encoding_options,
        )

    @staticmethod
    def from_data(data: bytes, encoding_options: list[EncodedPayloadOptions]) -> "NetworkEncodedInput":
        return NetworkEncodedInput(
            b64payload=base64.b64encode(data).decode("utf-8"),
            encoding_options=encoding_options,
        )


class NetworkEncodedResult(NetworkEncodedBase):
    @staticmethod
    def from_encoded_payload(encoded_payload: EncodedPayload) -> "NetworkEncodedResult":
        return NetworkEncodedResult(
            b64payload=base64.b64encode(encoded_payload.payload).decode("utf-8"),
            encoding_options=encoded_payload.encoding_options,
        )

    def get_payload(self) -> bytes:
        return base64.b64decode(self.b64payload)


class PayloadWithContext(BaseModel):
    """Format of payloads sent through temporal server"""

    context: WorkflowContext
    payload: Any
    empty: bool = False
