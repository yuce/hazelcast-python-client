from hazelcast.serialization.bits import *
from hazelcast.protocol.builtin import FixSizedTypesCodec
from hazelcast.protocol.client_message import OutboundMessage, REQUEST_HEADER_SIZE, create_initial_buffer
from hazelcast.protocol.builtin import StringCodec
from hazelcast.protocol.builtin import CodecUtil
from hazelcast.protocol.builtin import ListMultiFrameCodec

# hex: 0xFE1100
_REQUEST_MESSAGE_TYPE = 16650496
# hex: 0xFE1101
_RESPONSE_MESSAGE_TYPE = 16650497

_REQUEST_SESSION_ID_OFFSET = REQUEST_HEADER_SIZE
_REQUEST_JAR_ON_MEMBER_OFFSET = _REQUEST_SESSION_ID_OFFSET + UUID_SIZE_IN_BYTES
_REQUEST_INITIAL_FRAME_SIZE = _REQUEST_JAR_ON_MEMBER_OFFSET + BOOLEAN_SIZE_IN_BYTES


def encode_request(session_id, jar_on_member, file_name, sha256_hex, snapshot_name, job_name, main_class, job_parameters):
    buf = create_initial_buffer(_REQUEST_INITIAL_FRAME_SIZE, _REQUEST_MESSAGE_TYPE)
    FixSizedTypesCodec.encode_uuid(buf, _REQUEST_SESSION_ID_OFFSET, session_id)
    FixSizedTypesCodec.encode_boolean(buf, _REQUEST_JAR_ON_MEMBER_OFFSET, jar_on_member)
    StringCodec.encode(buf, file_name)
    StringCodec.encode(buf, sha256_hex)
    CodecUtil.encode_nullable(buf, snapshot_name, StringCodec.encode)
    CodecUtil.encode_nullable(buf, job_name, StringCodec.encode)
    CodecUtil.encode_nullable(buf, main_class, StringCodec.encode)
    ListMultiFrameCodec.encode(buf, job_parameters, StringCodec.encode, True)
    return OutboundMessage(buf, True)
