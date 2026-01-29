from typing import Union
from qhash.clients.protos.talk_api_pb2 import (
    CreateBulkPhoneCallRequest,
    CreateBulkPhoneCallResponse,
    CreatePhoneCallRequest,
    CreatePhoneCallResponse,
)
from qhash.connections import ConnectionConfig, UserAuthInfo, ClientAuthInfo


def create_phone_call(
    client_cfg: ConnectionConfig,
    request: CreatePhoneCallRequest,
    auth: Union[UserAuthInfo, ClientAuthInfo, None] = None,
) -> CreatePhoneCallResponse:
    if auth is None:
        auth = client_cfg.auth
    return client_cfg.conversation_client.CreatePhoneCall(
        request,
        metadata=auth,
    )


def create_bulk_phone_call(
    client_cfg: ConnectionConfig,
    request: CreateBulkPhoneCallRequest,
    auth: Union[UserAuthInfo, ClientAuthInfo, None] = None,
) -> CreateBulkPhoneCallResponse:
    if auth is None:
        auth = client_cfg.auth
    return client_cfg.conversation_client.CreateBulkPhoneCall(
        request,
        metadata=auth,
    )
