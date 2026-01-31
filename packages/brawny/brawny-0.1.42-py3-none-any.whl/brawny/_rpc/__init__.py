"""RPC core built from small pieces.

EndpointPool orders endpoints deterministically.
Caller executes a single call against one endpoint.
call_with_retries composes pool + caller + RetryPolicy.
ReadClient and BroadcastClient call the retry helper directly.
Logs emit one rpc.attempt event per attempt with fixed fields.
request_id is injected for tests; production can use a UUID.
"""

from brawny._rpc.errors import (
    RPCError,
    RPCFatalError,
    RPCRecoverableError,
    RPCRetryableError,
    RPCTransient,
    RPCRateLimited,
    RPCPermanent,
    RPCDecode,
    RpcErrorKind,
    RpcErrorInfo,
    classify_rpc_error,
    classify_error,
)
from brawny._rpc.clients import ReadClient, BroadcastClient
from brawny._rpc.pool import EndpointPool
from brawny._rpc.caller import Caller
from brawny._rpc.retry import call_with_retries
from brawny._rpc.context import (
    get_job_context,
    get_intent_budget_context,
    reset_job_context,
    reset_intent_budget_context,
    set_job_context,
    set_intent_budget_context,
)

__all__ = [
    "ReadClient",
    "BroadcastClient",
    "EndpointPool",
    "Caller",
    "call_with_retries",
    "RPCError",
    "RPCFatalError",
    "RPCRecoverableError",
    "RPCRetryableError",
    "RPCTransient",
    "RPCRateLimited",
    "RPCPermanent",
    "RPCDecode",
    "RpcErrorKind",
    "RpcErrorInfo",
    "classify_rpc_error",
    "classify_error",
    "get_job_context",
    "get_intent_budget_context",
    "reset_job_context",
    "reset_intent_budget_context",
    "set_job_context",
    "set_intent_budget_context",
]
