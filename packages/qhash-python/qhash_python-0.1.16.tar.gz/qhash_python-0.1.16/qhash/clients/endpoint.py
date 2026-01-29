from typing import Union
from qhash.clients.protos.endpoint_api_pb2 import (
    GetAllEndpointLogRequest,
    GetAllEndpointLogResponse,
    GetAllEndpointRequest,
    GetAllEndpointResponse,
    GetEndpointLogRequest,
    GetEndpointLogResponse,
    GetEndpointRequest,
    GetEndpointResponse,
)
from qhash.connections import ConnectionConfig, UserAuthInfo, ClientAuthInfo


def get_endpoint(
    client_cfg: ConnectionConfig,
    request: GetEndpointRequest,
    auth: Union[UserAuthInfo, ClientAuthInfo, None] = None,
) -> GetEndpointResponse:
    if auth is None:
        auth = client_cfg.auth

    return client_cfg.endpoint_client.GetEndpoint(
        request,
        metadata=auth,
    )


def get_all_endpoint(
    client_cfg: ConnectionConfig,
    request: GetAllEndpointRequest,
    auth: Union[UserAuthInfo, ClientAuthInfo, None] = None,
) -> GetAllEndpointResponse:
    if auth is None:
        auth = client_cfg.auth
    return client_cfg.endpoint_client.GetAllEndpoint(
        request,
        metadata=auth,
    )


def get_endpoint_log(
    client_cfg: ConnectionConfig,
    request: GetEndpointLogRequest,
    auth: Union[UserAuthInfo, ClientAuthInfo, None] = None,
) -> GetEndpointLogResponse:
    if auth is None:
        auth = client_cfg.auth

    return client_cfg.endpoint_client.GetEndpointLog(
        request,
        metadata=auth,
    )


def get_all_endpoint_log(
    client_cfg: ConnectionConfig,
    request: GetAllEndpointLogRequest,
    auth: Union[UserAuthInfo, ClientAuthInfo, None] = None,
) -> GetAllEndpointLogResponse:
    if auth is None:
        auth = client_cfg.auth
    return client_cfg.endpoint_client.GetAllEndpointLog(
        request,
        metadata=auth,
    )
