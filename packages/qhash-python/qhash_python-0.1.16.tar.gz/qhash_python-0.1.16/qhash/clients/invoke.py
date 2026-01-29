from typing import Union
from qhash.clients.protos.invoker_api_pb2 import (
    InvokeRequest,
    InvokeResponse,
)
from qhash.connections import ConnectionConfig, UserAuthInfo, ClientAuthInfo


def invoke(
    client_cfg: ConnectionConfig,
    request: InvokeRequest,
    auth: Union[UserAuthInfo, ClientAuthInfo, None] = None,
) -> InvokeResponse:
    if auth is None:
        auth = client_cfg.auth

    return client_cfg.deployment_client.Invoke(
        request,
        metadata=auth,
    )
