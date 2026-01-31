import base64
import hashlib
import json
import os
import urllib.parse
from typing import Any, Dict, List, Mapping, Tuple

import structlog
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from pydantic import BaseModel
from pydantic_core import from_json, to_json

from mistralai_workflows.core.config.config import (
    PayloadEncryptionConfig,
    PayloadEncryptionMode,
    PayloadOffloadingConfig,
)
from mistralai_workflows.core.storage.blob_storage import get_blob_storage
from mistralai_workflows.core.storage.blob_storage_impl import BlobNotFoundError
from mistralai_workflows.models import (
    EncodedPayloadOptions,
    EncryptableFieldTypes,
    NetworkEncodedInput,
    NetworkEncodedResult,
    PayloadMetadataKeys,
    WorkflowContext,
)

logger = structlog.get_logger(__name__)

CUSTOM_ENCODING_FORMAT = "json/wf_v1"


class PayloadEncodingException(Exception): ...


class PayloadDecryptionException(PayloadEncodingException): ...


class OffloadedPayloadData(BaseModel):
    key: str


def build_temporal_payload_metadata(
    context: WorkflowContext, encoding_options: list[EncodedPayloadOptions], empty_payload: bool = False
) -> Dict[str, bytes]:
    metadata: Dict[str, bytes] = {
        # Base encoding, mandatory for payload data converter to works properly
        PayloadMetadataKeys.ENCODING: CUSTOM_ENCODING_FORMAT.encode(),
        # Context
        PayloadMetadataKeys.NAMESPACE: context.namespace.encode(),
        PayloadMetadataKeys.EXECUTION_ID: context.execution_id.encode(),
        # "retention_ttl": str(encoded_payload.context.retention_ttl).encode(),
        # Encoding options
        PayloadMetadataKeys.ENCODING_OPTIONS: b",".join(option.value.encode() for option in encoding_options),
    }

    # Include root workflow exec ID if present (for sub-workflow lineage tracking)
    if context.root_workflow_exec_id:
        metadata[PayloadMetadataKeys.ROOT_WORKFLOW_EXEC_ID] = context.root_workflow_exec_id.encode()
    if context.parent_workflow_exec_id:
        metadata[PayloadMetadataKeys.PARENT_WORKFLOW_EXEC_ID] = context.parent_workflow_exec_id.encode()

    if empty_payload:
        metadata[PayloadMetadataKeys.EMPTY_PAYLOAD] = bytes(True)

    return metadata


def build_info_from_payload_metadata(
    metadata: Mapping[str, bytes],
) -> Tuple[WorkflowContext, list[EncodedPayloadOptions], bool]:
    # Extract root and parent workflow exec ID if present
    root_workflow_exec_id_bytes = metadata.get(PayloadMetadataKeys.ROOT_WORKFLOW_EXEC_ID)
    root_workflow_exec_id = root_workflow_exec_id_bytes.decode() if root_workflow_exec_id_bytes else None
    parent_workflow_exec_id_bytes = metadata.get(PayloadMetadataKeys.PARENT_WORKFLOW_EXEC_ID)
    parent_workflow_exec_id = parent_workflow_exec_id_bytes.decode() if parent_workflow_exec_id_bytes else None

    workflow_context = WorkflowContext(
        namespace=metadata.get(PayloadMetadataKeys.NAMESPACE, b"").decode(),
        execution_id=metadata.get(PayloadMetadataKeys.EXECUTION_ID, b"").decode(),
        root_workflow_exec_id=root_workflow_exec_id,
        parent_workflow_exec_id=parent_workflow_exec_id,
    )

    empty = bool(metadata.get(PayloadMetadataKeys.EMPTY_PAYLOAD))
    encoding_options: list[EncodedPayloadOptions] = []
    encoding_options_bytes = metadata.get(PayloadMetadataKeys.ENCODING_OPTIONS, None)
    if encoding_options_bytes:
        for option in encoding_options_bytes.split(b","):
            option_str = option.decode()
            try:
                encoding_options.append(EncodedPayloadOptions(option_str))
            except ValueError:
                raise PayloadEncodingException(f"Unknown encoding option {option_str}")
    return workflow_context, encoding_options, empty


class PayloadEncoder:
    """This class is in charge of payload encoding/decoding operations such as:
    - Blob storage offloading
    - Encryption
    """

    BLOB_STORAGE_KEY_PREFIX = "temporal-payload"
    _NONCE_SIZE = 12

    offloading_config: PayloadOffloadingConfig
    encryption_config: PayloadEncryptionConfig

    encryptor_main: AESGCM | None = None
    encryptor_secondary: AESGCM | None = None

    def __init__(
        self,
        offloading_config: PayloadOffloadingConfig,
        encryption_config: PayloadEncryptionConfig,
    ) -> None:
        self.offloading_config = offloading_config
        if self.offloading_config.enabled and not self.offloading_config.storage_config:
            raise PayloadEncodingException("Blob storage config is not set for temporal payload encoding")

        self.encryption_config = encryption_config
        if self.encryption_config.mode != PayloadEncryptionMode.NONE:
            main_key = self.encryption_config.main_key.get_secret_value() if self.encryption_config.main_key else None
            if not main_key:
                raise Exception("Encryption key is not set for temporal payload encoding")
            self.encryptor_main = AESGCM(bytes.fromhex(main_key))
            secondary_key_secret = self.encryption_config.secondary_key
            secondary_key = secondary_key_secret.get_secret_value() if secondary_key_secret else None
            if secondary_key:
                self.encryptor_secondary = AESGCM(bytes.fromhex(secondary_key))

    @staticmethod
    def blob_storage_key_prefix(context: WorkflowContext) -> str:
        return (
            f"{PayloadEncoder.BLOB_STORAGE_KEY_PREFIX}/{urllib.parse.quote(context.namespace)}/{context.execution_id}"
        )

    def _encrypt(self, data: bytes) -> bytes:
        assert self.encryptor_main, "Encryptor is not set"
        nonce = os.urandom(self._NONCE_SIZE)
        return nonce + self.encryptor_main.encrypt(nonce, data, None)

    def _decrypt(self, data: bytes) -> bytes:
        assert self.encryptor_main, "Encryptor is not set"
        try:
            return self.encryptor_main.decrypt(data[: self._NONCE_SIZE], data[self._NONCE_SIZE :], None)
        except InvalidTag as main_exc:
            if self.encryptor_secondary:
                logger.warning("Failed to decrypt payload with main key, trying secondary key")
                try:
                    return self.encryptor_secondary.decrypt(data[: self._NONCE_SIZE], data[self._NONCE_SIZE :], None)
                except InvalidTag:
                    pass
            logger.error("Could not decrypt payload", exc_info=main_exc)
            raise PayloadDecryptionException("Failed to decrypt payload")

    async def _handle_offloading(self, data: bytes, context: WorkflowContext | None) -> tuple[bytes, bool]:
        assert self.offloading_config.storage_config, "Blob storage config is not set for temporal payload encoding"

        if len(data) >= self.offloading_config.min_size_bytes:
            if not context:
                logger.error(
                    "Temporal payload offloading and the payload size exceed the threshold but no context was "
                    "provided. Cannot proceed with offloading...",
                )
                return data, False

            # Hash the content to have a uniq idempotent key for this payload
            blob_key = f"sha256:{hashlib.sha256(data).hexdigest()}"
            payload_key = f"{self.blob_storage_key_prefix(context)}/{blob_key}"
            async with get_blob_storage(self.offloading_config.storage_config) as blob_storage:
                blob = None
                try:
                    blob = await blob_storage.get_blob_properties(payload_key)
                except BlobNotFoundError:
                    pass

                if not blob:
                    logger.debug("Offloading payload", payload_key=payload_key)
                    await blob_storage.upload_blob(key=payload_key, content=data)
                else:
                    logger.debug("Offloaded payload exists already", payload_key=payload_key)

                data = OffloadedPayloadData(key=payload_key).model_dump_json().encode()
                return data, True
        return data, False

    @staticmethod
    def _extract_encrypted_fields(data: Any = None) -> list[dict[str, Any]]:
        encrypted_fields = []
        if isinstance(data, dict):
            if data.get("field_type") == EncryptableFieldTypes.STRING:
                return [data]
            for field_name, field_data in data.items():
                if isinstance(field_data, dict | list):
                    encrypted_fields.extend(PayloadEncoder._extract_encrypted_fields(field_data))
        elif isinstance(data, list):
            for item in data:
                encrypted_fields.extend(PayloadEncoder._extract_encrypted_fields(item))
        return encrypted_fields

    async def _partially_encrypt(self, data: bytes, decrypt: bool = False) -> tuple[bytes, bool]:
        try:
            obj = json.loads(data)
        except json.decoder.JSONDecodeError:
            return data, False

        encrypted_fields = self._extract_encrypted_fields(obj)
        for encrypted_field in encrypted_fields:
            if decrypt:
                encrypted_data = base64.b64decode(encrypted_field["data"])
                encrypted_field["data"] = self._decrypt(encrypted_data).decode()
            else:
                encrypted_data = self._encrypt(encrypted_field["data"].encode())
                encrypted_field["data"] = base64.b64encode(encrypted_data).decode()

        return json.dumps(obj).encode(), len(encrypted_fields) > 0

    async def encode_payload_content(
        self, data: bytes | str, context: WorkflowContext | None
    ) -> tuple[bytes, list[EncodedPayloadOptions]]:
        """Handle payload encoding:
        - Payload offloading (if context provided)
        - Encryption
        """
        if isinstance(data, str):
            data = data.encode()

        encoding_options = []

        if self.offloading_config.enabled:
            data, offloaded = await self._handle_offloading(data, context)
            if offloaded:
                encoding_options.append(EncodedPayloadOptions.OFFLOADED)

        if self.encryption_config.mode == PayloadEncryptionMode.FULL:
            data = self._encrypt(data)
            encoding_options.append(EncodedPayloadOptions.ENCRYPTED)
        elif (
            self.encryption_config.mode == PayloadEncryptionMode.PARTIAL
            and EncodedPayloadOptions.OFFLOADED not in encoding_options
        ):
            # Do not partially encrypt offloaded payload (fields not in the payload anymore)
            data, partially_encrypted = await self._partially_encrypt(data)
            if partially_encrypted:
                encoding_options.append(EncodedPayloadOptions.PARTIALLY_ENCRYPTED)

        return data, encoding_options

    async def decode_payload_content(self, data: bytes, encoding_options: List[EncodedPayloadOptions]) -> bytes:
        # Decode in the reverse order of encoding
        for option in reversed(encoding_options):
            if option == EncodedPayloadOptions.ENCRYPTED:
                data = self._decrypt(data)
            elif EncodedPayloadOptions.PARTIALLY_ENCRYPTED in encoding_options:
                data, _ = await self._partially_encrypt(data, decrypt=True)
            elif option == EncodedPayloadOptions.OFFLOADED:
                if not self.offloading_config.enabled or not self.offloading_config.storage_config:
                    raise PayloadEncodingException(
                        "Payload offloading is not enabled but an offloaded payload was received"
                    )
                async with get_blob_storage(self.offloading_config.storage_config) as blob_storage:
                    offloaded_payload_data = OffloadedPayloadData.model_validate_json(data)
                    data = await blob_storage.get_blob(offloaded_payload_data.key)
            else:
                raise PayloadEncodingException(f"Unknown decoding option: {option}")

        return data

    async def encode_network_input(self, data: Dict[str, Any] | None, context: WorkflowContext) -> NetworkEncodedInput:
        """This method MUST be called to format every payload send to Mistral Workflows control plane
        to ensure a proper encoding of the payload.
        """
        encoded_data, encoding_options = await self.encode_payload_content(to_json(data), context)
        network_input = NetworkEncodedInput.from_data(encoded_data, encoding_options)
        return network_input

    async def decode_network_result(self, data: Any) -> Any:
        """This method MUST be called to format every response payload from the Mistral Workflows control plane
        otherwise the payload will not be decoded, hence not usable.
        """

        try:
            network_encoded_payload = NetworkEncodedResult.model_validate(data)
        except ValueError:
            logger.warning("Network result is not a NetworkEncodedResult")
            return data

        byte_results = await self.decode_payload_content(
            network_encoded_payload.get_payload(), network_encoded_payload.encoding_options
        )
        try:
            return from_json(byte_results)
        except ValueError:
            logger.warning("Payload is not a valid json.")
            return byte_results  # Return as-is if JSON conversion fails

    def check_is_payload_encoded(self, data: Any) -> bool:
        """Check if the payload is encoded (offloaded or encrypted)"""
        try:
            NetworkEncodedResult.model_validate(data)
            return True
        except ValueError:
            return False


class TraceEncoder:
    def __init__(
        self,
        encryption_config: PayloadEncryptionConfig,
    ) -> None:
        self.encryption_config = encryption_config

    def encode_trace_data(self, data: str) -> str:
        if self.encryption_config.mode == PayloadEncryptionMode.FULL:
            return "**ENCRYPTED**"

        if self.encryption_config.mode == PayloadEncryptionMode.PARTIAL:
            try:
                obj = json.loads(data)
            except json.decoder.JSONDecodeError:
                return data
            encrypted_fields = PayloadEncoder._extract_encrypted_fields(obj)
            for encrypted_field in encrypted_fields:
                encrypted_field["data"] = "**ENCRYPTED**"
            return json.dumps(obj)

        return data
