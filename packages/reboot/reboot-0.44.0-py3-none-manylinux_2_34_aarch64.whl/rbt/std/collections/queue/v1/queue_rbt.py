# yapf: disable
# isort: skip_file
# ruff: noqa
# mypy: disable-error-code="func-returns-value"



# To not generate code where imported names might get shadowed when a user
# specifies some name in their proto file to be the same as one of our imported
# names, (for example: a request field named `uuid`) we bind all imports to
# names that are forbidden in 'proto' and therefore can never collide.

# Standard imports.
from __future__ import annotations as IMPORT_future_annotations

# The following MUST appear before the rest of the imports, since those imports
# may be invalid (broken) if the generated code is mismatched with the installed
# libraries.
import rebootdev.versioning as IMPORT_reboot_versioning
IMPORT_reboot_versioning.check_generated_code_compatible("0.44.0")

# ATTENTION: no types in this file should be imported with their unqualified
#            name (e.g. `from typing import Any`). That would cause clashes
#            with user-defined methods that have the same name. Use
#            fully-qualified names (e.g. `IMPORT_typing.Any`) instead.
import asyncio as IMPORT_asyncio
import builtins as IMPORT_builtins
import contextvars as IMPORT_contextvars
import dataclasses as IMPORT_dataclasses
import google.protobuf.descriptor as IMPORT_google_protobuf_descriptor
import google.protobuf.json_format as IMPORT_google_protobuf_json_format
import google.protobuf.message as IMPORT_google_protobuf_message
import grpc as IMPORT_grpc
import grpc_status._async as IMPORT_rpc_status_async
from grpc_status import rpc_status as IMPORT_rpc_status_sync
import json as IMPORT_json
import os as IMPORT_os
import traceback as IMPORT_traceback
import uuid as IMPORT_uuid
import pickle as IMPORT_pickle
import rebootdev as IMPORT_rebootdev
import log.log as IMPORT_log_log   # type: ignore[import]
import typing as IMPORT_typing
import rebootdev.aio.backoff as IMPORT_reboot_aio_backoff
import functools as IMPORT_functools
from abc import abstractmethod as IMPORT_abc_abstractmethod
from datetime import datetime as IMPORT_datetime_datetime
from datetime import timedelta as IMPORT_datetime_timedelta
from datetime import timezone as IMPORT_datetime_timezone
from google.protobuf import timestamp_pb2 as IMPORT_google_protobuf_timestamp_pb2
from google.protobuf import wrappers_pb2 as IMPORT_google_protobuf_wrappers_pb2
from google.protobuf.empty_pb2 import Empty as IMPORT_google_protobuf_empty_pb2_Empty
import rebootdev.aio.tracing as IMPORT_reboot_aio_tracing
from google.rpc import status_pb2 as IMPORT_google_rpc_status_pb2
from tzlocal import get_localzone as IMPORT_tzlocal_get_localzone
import rebootdev.aio.call as IMPORT_reboot_aio_call
import rebootdev.aio.caller_id as IMPORT_reboot_aio_caller_id
import rebootdev.aio.contexts as IMPORT_reboot_aio_contexts
import rebootdev.aio.headers as IMPORT_reboot_aio_headers
import rebootdev.aio.idempotency as IMPORT_reboot_aio_idempotency
import rebootdev.aio.internals.channel_manager as IMPORT_reboot_aio_internals_channel_manager
import rebootdev.aio.internals.middleware as IMPORT_reboot_aio_internals_middleware
import rebootdev.aio.internals.tasks_cache as IMPORT_reboot_aio_internals_tasks_cache
import rebootdev.aio.internals.tasks_dispatcher as IMPORT_reboot_aio_internals_tasks_dispatcher
import rebootdev.aio.placement as IMPORT_reboot_aio_placement
import rebootdev.aio.servicers as IMPORT_reboot_aio_servicers
import rebootdev.aio.state_managers as IMPORT_reboot_aio_state_managers
import rebootdev.aio.stubs as IMPORT_reboot_aio_stubs
import rebootdev.aio.tasks as IMPORT_reboot_aio_tasks
import rebootdev.aio.types as IMPORT_reboot_aio_types
import rebootdev.aio.external as IMPORT_reboot_aio_external
import rebootdev.aio.workflows as IMPORT_reboot_aio_workflows
import rebootdev.settings as IMPORT_reboot_settings
import rebootdev.nodejs.python as IMPORT_reboot_nodejs_python
from rebootdev.time import DateTimeWithTimeZone as IMPORT_reboot_time_DateTimeWithTimeZone
import rbt.v1alpha1 as IMPORT_rbt_v1alpha1
import rbt.v1alpha1.nodejs_pb2 as IMPORT_rbt_v1alpha1_nodejs_pb2
import google.protobuf.any_pb2 as IMPORT_google_protobuf_any_pb2
import sys as IMPORT_sys

# Additionally re-export all messages and enums from the pb2 module.
from rbt.std.collections.queue.v1.queue_pb2 import (
    DequeueRequest,
    DequeueResponse,
    EmptyRequest,
    EmptyResponse,
    EnqueueRequest,
    EnqueueResponse,
)

# User defined or referenced imports.
import google.protobuf.any_pb2
import google.protobuf.descriptor_pb2
import google.protobuf.struct_pb2
import rbt.std.collections.queue.v1.queue_pb2
import rbt.std.collections.queue.v1.queue_pb2_grpc
import rbt.std.item.v1.item_pb2
import rbt.v1alpha1.options_pb2

logger = IMPORT_log_log.get_logger(__name__)

# We won't validate Pydantic state models while they are under construction.
states_being_constructed: set[str] = set()

class Unset:
    pass

UNSET = Unset()



def QueueToProto(state: Queue.State, protobuf_state: rbt.std.collections.queue.v1.queue_pb2.Queue):
    pass

def QueueFromProto(
    state: rbt.std.collections.queue.v1.queue_pb2.Queue,
    is_initial_state: bool = False,
) -> Queue.State:
    return state
def QueueEnqueueResponseToProto(
    response: Queue.EnqueueResponse
) -> rbt.std.collections.queue.v1.queue_pb2.EnqueueResponse:
    return response

def QueueEnqueueResponseFromProto(
    response: rbt.std.collections.queue.v1.queue_pb2.EnqueueResponse
) -> Queue.EnqueueResponse:
    return response

def QueueEnqueueRequestToProto(
    request: Queue.EnqueueRequest
) -> rbt.std.collections.queue.v1.queue_pb2.EnqueueRequest:
    return request

def QueueEnqueueRequestFromProto(
    request: rbt.std.collections.queue.v1.queue_pb2.EnqueueRequest
) -> Queue.EnqueueRequest:
    return request

def QueueEnqueueRequestFromInputFields(
    value: IMPORT_typing.Optional[google.protobuf.struct_pb2.Value] | Unset,
    bytes: IMPORT_typing.Optional[bytes] | Unset,
    any: IMPORT_typing.Optional[google.protobuf.any_pb2.Any] | Unset,
    items: IMPORT_typing.Optional[IMPORT_typing.Iterable[rbt.std.item.v1.item_pb2.Item]] | Unset,
):
    assert Queue.EnqueueRequest is not None

    if not isinstance(value, Unset) and value is not None and not isinstance(
        value,
        google.protobuf.struct_pb2.Value,
    ):
        raise TypeError(
            f"Can not construct protobuf message of type "
            f"'rbt.std.collections.queue.v1.queue_pb2.EnqueueRequest': field 'value' is not "
            f"of required type 'google.protobuf.struct_pb2.Value'"
        )
    if not isinstance(bytes, Unset) and bytes is not None and not isinstance(
        bytes,
        IMPORT_builtins.bytes
    ):
        raise TypeError(
            f"Can not construct protobuf message of type "
            f"'rbt.std.collections.queue.v1.queue_pb2.EnqueueRequest': field 'bytes' is not "
            f"of required type 'bytes'"
        )
    if not isinstance(any, Unset) and any is not None and not isinstance(
        any,
        google.protobuf.any_pb2.Any,
    ):
        raise TypeError(
            f"Can not construct protobuf message of type "
            f"'rbt.std.collections.queue.v1.queue_pb2.EnqueueRequest': field 'any' is not "
            f"of required type 'google.protobuf.any_pb2.Any'"
        )
    if not isinstance(items, Unset) and items is not None and not isinstance(
        items,
        IMPORT_typing.Iterable,
    ):
        raise TypeError(
            f"Can not construct protobuf message of type "
            f"'rbt.std.collections.queue.v1.queue_pb2.EnqueueRequest': field 'items' is not "
            f"of required type 'typing.Iterable[rbt.std.item.v1.item_pb2.Item]'"
        )


    __args__: dict[str, IMPORT_typing.Any] = {}

    if not isinstance(value, Unset):
        __args__['value'] = value
    if not isinstance(bytes, Unset):
        __args__['bytes'] = bytes
    if not isinstance(any, Unset):
        __args__['any'] = any
    if not isinstance(items, Unset):
        __args__['items'] = items

    return Queue.EnqueueRequest(
        **__args__,
    )

def QueueDequeueResponseToProto(
    response: Queue.DequeueResponse
) -> rbt.std.collections.queue.v1.queue_pb2.DequeueResponse:
    return response

def QueueDequeueResponseFromProto(
    response: rbt.std.collections.queue.v1.queue_pb2.DequeueResponse
) -> Queue.DequeueResponse:
    return response

def QueueDequeueRequestToProto(
    request: Queue.DequeueRequest
) -> rbt.std.collections.queue.v1.queue_pb2.DequeueRequest:
    return request

def QueueDequeueRequestFromProto(
    request: rbt.std.collections.queue.v1.queue_pb2.DequeueRequest
) -> Queue.DequeueRequest:
    return request

def QueueDequeueRequestFromInputFields(
    bulk: IMPORT_typing.Optional[bool] | Unset,
    at_most: IMPORT_typing.Optional[int] | Unset,
):
    assert Queue.DequeueRequest is not None

    if not isinstance(bulk, Unset) and bulk is not None and not isinstance(
        bulk,
        bool,
    ):
        raise TypeError(
            f"Can not construct protobuf message of type "
            f"'rbt.std.collections.queue.v1.queue_pb2.DequeueRequest': field 'bulk' is not "
            f"of required type 'bool'"
        )
    if not isinstance(at_most, Unset) and at_most is not None and not isinstance(
        at_most,
        int,
    ):
        raise TypeError(
            f"Can not construct protobuf message of type "
            f"'rbt.std.collections.queue.v1.queue_pb2.DequeueRequest': field 'at_most' is not "
            f"of required type 'int'"
        )


    __args__: dict[str, IMPORT_typing.Any] = {}

    if not isinstance(bulk, Unset):
        __args__['bulk'] = bulk
    if not isinstance(at_most, Unset):
        __args__['at_most'] = at_most

    return Queue.DequeueRequest(
        **__args__,
    )

def QueueTryDequeueResponseToProto(
    response: Queue.TryDequeueResponse
) -> rbt.std.collections.queue.v1.queue_pb2.DequeueResponse:
    return response

def QueueTryDequeueResponseFromProto(
    response: rbt.std.collections.queue.v1.queue_pb2.DequeueResponse
) -> Queue.TryDequeueResponse:
    return response

def QueueTryDequeueRequestToProto(
    request: Queue.TryDequeueRequest
) -> rbt.std.collections.queue.v1.queue_pb2.DequeueRequest:
    return request

def QueueTryDequeueRequestFromProto(
    request: rbt.std.collections.queue.v1.queue_pb2.DequeueRequest
) -> Queue.TryDequeueRequest:
    return request

def QueueTryDequeueRequestFromInputFields(
    bulk: IMPORT_typing.Optional[bool] | Unset,
    at_most: IMPORT_typing.Optional[int] | Unset,
):
    assert Queue.TryDequeueRequest is not None

    if not isinstance(bulk, Unset) and bulk is not None and not isinstance(
        bulk,
        bool,
    ):
        raise TypeError(
            f"Can not construct protobuf message of type "
            f"'rbt.std.collections.queue.v1.queue_pb2.DequeueRequest': field 'bulk' is not "
            f"of required type 'bool'"
        )
    if not isinstance(at_most, Unset) and at_most is not None and not isinstance(
        at_most,
        int,
    ):
        raise TypeError(
            f"Can not construct protobuf message of type "
            f"'rbt.std.collections.queue.v1.queue_pb2.DequeueRequest': field 'at_most' is not "
            f"of required type 'int'"
        )


    __args__: dict[str, IMPORT_typing.Any] = {}

    if not isinstance(bulk, Unset):
        __args__['bulk'] = bulk
    if not isinstance(at_most, Unset):
        __args__['at_most'] = at_most

    return Queue.TryDequeueRequest(
        **__args__,
    )

def QueueEmptyResponseToProto(
    response: Queue.EmptyResponse
) -> rbt.std.collections.queue.v1.queue_pb2.EmptyResponse:
    return response

def QueueEmptyResponseFromProto(
    response: rbt.std.collections.queue.v1.queue_pb2.EmptyResponse
) -> Queue.EmptyResponse:
    return response

def QueueEmptyRequestToProto(
    request: Queue.EmptyRequest
) -> rbt.std.collections.queue.v1.queue_pb2.EmptyRequest:
    return request

def QueueEmptyRequestFromProto(
    request: rbt.std.collections.queue.v1.queue_pb2.EmptyRequest
) -> Queue.EmptyRequest:
    return request

def QueueEmptyRequestFromInputFields(
):
    assert Queue.EmptyRequest is not None



    __args__: dict[str, IMPORT_typing.Any] = {}


    return Queue.EmptyRequest(
        **__args__,
    )


############################ Legacy gRPC Servicers ############################
# This section is relevant (only) for servicers that implement a legacy gRPC
# service in a Reboot context. It is irrelevant to clients.

def MakeLegacyGrpcServiceable(
    # A legacy gRPC servicer type can't be more specific than `type`,
    # because legacy gRPC servicers (as generated by the gRPC `protoc`
    # plugin) do not share any common base class other than `object`.
    servicer_type: type
) -> IMPORT_reboot_aio_servicers.Serviceable:
    raise ValueError(f"Unknown legacy gRPC servicer type '{servicer_type}'")



############################ Reboot Servicer Middlewares ############################
# This section is relevant (only) for servicers implementing a Reboot servicer. It
# is irrelevant to clients, except for the fact that some clients are _also_ such
# servicers.

# For internal calls, we can use a magic token to bypass token verification and
# authorization checks. The token provides no auth information (e.g.,
# `context.auth is None`).
__internal_magic_token__: str = f'internal-{IMPORT_uuid.uuid4()}'

class QueueServicerMiddleware(IMPORT_reboot_aio_internals_middleware.Middleware):

    def __init__(
        self,
        *,
        servicer: QueueBaseServicer,
        application_id: IMPORT_reboot_aio_types.ApplicationId,
        server_id: IMPORT_reboot_aio_types.ServerId,
        state_manager: IMPORT_reboot_aio_state_managers.StateManager,
        placement_client: IMPORT_reboot_aio_placement.PlacementClient,
        channel_manager: IMPORT_reboot_aio_internals_channel_manager._ChannelManager,
        tasks_cache: IMPORT_reboot_aio_internals_tasks_cache.TasksCache,
        token_verifier: IMPORT_typing.Optional[IMPORT_rebootdev.aio.auth.token_verifiers.TokenVerifier],
        effect_validation: IMPORT_reboot_aio_contexts.EffectValidation,
        ready: IMPORT_asyncio.Event,
    ):
        super().__init__(
            application_id=application_id,
            server_id=server_id,
            state_type_name = IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue'),
            service_names = [
                IMPORT_reboot_aio_types.ServiceName("rbt.std.collections.queue.v1.QueueMethods"),
            ],
            placement_client=placement_client,
            channel_manager=channel_manager,
            effect_validation=effect_validation,
        )

        self._servicer = servicer
        self._state_manager = state_manager
        self.tasks_dispatcher = IMPORT_reboot_aio_internals_tasks_dispatcher.TasksDispatcher(
            application_id=application_id,
            dispatch=self.dispatch,
            tasks_cache=tasks_cache,
            ready=ready,
            complete_task=self._state_manager.complete_task,
        )

        # Store the type of each method's request so that stored requests can be
        # deserialized into the correct type.
        self.request_type_by_method_name: dict[str, type[IMPORT_google_protobuf_message.Message]] = {
            'Enqueue': rbt.std.collections.queue.v1.queue_pb2.EnqueueRequest,
            'Dequeue': rbt.std.collections.queue.v1.queue_pb2.DequeueRequest,
            'TryDequeue': rbt.std.collections.queue.v1.queue_pb2.DequeueRequest,
            'Empty': rbt.std.collections.queue.v1.queue_pb2.EmptyRequest,
        }

        # Get authorizer, if any, converting from a rule if necessary.
        def convert_authorizer_rule_if_necessary(
            authorizer_or_rule: IMPORT_typing.Optional[
                IMPORT_rebootdev.aio.auth.authorizers.Authorizer | IMPORT_rebootdev.aio.auth.authorizers.AuthorizerRule
            ]
        ) -> IMPORT_rebootdev.aio.auth.authorizers.Authorizer:

            # If no authorizer or rule is provided, return the default
            # authorizer which allows if app internal or allows if in
            # dev mode (and logs some warnings to help the user
            # realize where they are missing authorization).
            if authorizer_or_rule is None:
                return IMPORT_rebootdev.aio.auth.authorizers.DefaultAuthorizer(
                    'Queue'
                )

            if isinstance(authorizer_or_rule, IMPORT_rebootdev.aio.auth.authorizers.AuthorizerRule):
                return QueueAuthorizer(
                    _default=authorizer_or_rule
                )

            return authorizer_or_rule

        self._authorizer = convert_authorizer_rule_if_necessary(
            servicer.authorizer()
        )

        # Create token verifier.
        self._token_verifier: IMPORT_typing.Optional[IMPORT_rebootdev.aio.auth.token_verifiers.TokenVerifier] = (
            servicer.token_verifier() or token_verifier
        )

        # Since users specify errors as proto messages they can't raise them
        # directly - to do so they have to use the `Aborted` wrapper, which will
        # hold the original proto message. On errors we'll need to check whether
        # such wrappers hold a proto message for a specified error, so we can
        # avoid retrying tasks that complete with a specified error.
        self._specified_errors_by_service_method_name: dict[str, list[str]] = {
        }


    def add_to_server(self, server: IMPORT_grpc.aio.Server) -> None:
        rbt.std.collections.queue.v1.queue_pb2_grpc.add_QueueMethodsServicer_to_server(
            self, server
        )

    async def inspect(self, state_ref: IMPORT_reboot_aio_types.StateRef) -> IMPORT_typing.AsyncIterator[IMPORT_google_protobuf_message.Message]:
        """Implementation of `Middleware.inspect()`."""
        context = self.create_context(
            headers=IMPORT_reboot_aio_headers.Headers(
                application_id=self.application_id,
                state_ref=state_ref,
            ),
            state_type_name = IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue'),
            method="inspect",
            context_type=IMPORT_reboot_aio_contexts.ReaderContext,
        )

        async with self._state_manager.streaming_reader_idempotency_key(
            context,
            self._servicer.__state_type__,
            authorize=None,
        ) as states:
            async for (state, idempotency_key) in states:
                yield state

    async def react_query(
        self,
        headers: IMPORT_reboot_aio_headers.Headers,
        method: str,
        request_bytes: bytes,
    ) -> IMPORT_typing.AsyncIterator[tuple[IMPORT_typing.Optional[IMPORT_google_protobuf_message.Message], list[IMPORT_uuid.UUID]]]:
        """Returns the response of calling 'method' given a message
        deserialized from the provided 'request_bytes' for each state
        update that creates a different response.

        # The caller (react.py) should have already ensured that this server
        # is authoritative for this traffic.
        assert self.placement_client.server_for_actor(
            headers.application_id,
            headers.state_ref,
        ) == self._server_id

        NOTE: only unary reader methods are supported."""
        # Need to define these up here since we can only do that once.
        last_response: IMPORT_typing.Optional[IMPORT_google_protobuf_message.Message] = None
        aggregated_idempotency_keys: list[IMPORT_uuid.UUID] = []
        if method == 'Enqueue':
            # Invariant here is that users should not have called this
            # directly but only through code generated React
            # components which should not have been generated except
            # for valid method candidates.
            logger.warning(
                "Got a React query request with an invalid method name: "
                f"Method '{method}' is invalid for servicer Queue."
                "\n"
                "Do you have a browser tab open for an older version "
                "of this application, or for a different application all together?"
            )
            raise IMPORT_rebootdev.aio.aborted.SystemAborted(
                IMPORT_rbt_v1alpha1.errors_pb2.InvalidMethod(),
                message=
                    f"Method '{method}' is invalid"
            )
            yield  # Necessary for type checking.
        elif method == 'Dequeue':
            # Invariant here is that users should not have called this
            # directly but only through code generated React
            # components which should not have been generated except
            # for valid method candidates.
            logger.warning(
                "Got a React query request with an invalid method name: "
                f"Method '{method}' is invalid for servicer Queue."
                "\n"
                "Do you have a browser tab open for an older version "
                "of this application, or for a different application all together?"
            )
            raise IMPORT_rebootdev.aio.aborted.SystemAborted(
                IMPORT_rbt_v1alpha1.errors_pb2.InvalidMethod(),
                message=
                    f"Method '{method}' is invalid"
            )
            yield  # Necessary for type checking.
        elif method == 'TryDequeue':
            # Invariant here is that users should not have called this
            # directly but only through code generated React
            # components which should not have been generated except
            # for valid method candidates.
            logger.warning(
                "Got a React query request with an invalid method name: "
                f"Method '{method}' is invalid for servicer Queue."
                "\n"
                "Do you have a browser tab open for an older version "
                "of this application, or for a different application all together?"
            )
            raise IMPORT_rebootdev.aio.aborted.SystemAborted(
                IMPORT_rbt_v1alpha1.errors_pb2.InvalidMethod(),
                message=
                    f"Method '{method}' is invalid"
            )
            yield  # Necessary for type checking.
        elif method == 'Empty':

            context = self.create_context(
                headers=headers,
                state_type_name = IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue'),
                method='Empty',
                context_type=IMPORT_reboot_aio_contexts.ReaderContext,
            )

            with IMPORT_reboot_aio_tracing.span(
                state_name=f"{context.state_type_name}('{context.state_id}')",
                span_name="Empty() (reactively)",
                # The naming above matches Python, but not TypeScript.
                python_specific=True,
                level=IMPORT_reboot_aio_tracing.TraceLevel.CUSTOMER,
            ):
                context.auth = await self._maybe_verify_token(
                    headers=headers, method='Empty'
                )

                request = rbt.std.collections.queue.v1.queue_pb2.EmptyRequest()
                request.ParseFromString(request_bytes)

                async with self._state_manager.reactively(
                    context,
                    self._servicer.__state_type__,
                    authorize=self._maybe_authorize(
                        method_name='rbt.std.collections.queue.v1.QueueMethods.Empty',
                        headers=headers,
                        auth=context.auth,
                        request=request,
                    ),
                ) as states:
                    async for (state, idempotency_keys) in states:

                        aggregated_idempotency_keys.extend(idempotency_keys)

                        # Note: This does not do any defensive copying currently:
                        # see https://github.com/reboot-dev/respect/issues/2636.
                        @IMPORT_reboot_aio_internals_middleware.maybe_run_function_twice_to_validate_effects
                        async def run__Empty(validating_effects: bool) -> IMPORT_google_protobuf_message.Message:
                            return await self.__Empty(
                                context,
                                state,
                                request,
                                validating_effects=validating_effects,
                            )

                        response = await run__Empty()

                        if last_response != response:
                            yield (response, aggregated_idempotency_keys)
                            last_response = response
                        else:
                            yield (None, aggregated_idempotency_keys)

                        aggregated_idempotency_keys.clear()
        else:
            logger.warning(
                "Got a React query request with an invalid method name: "
                f"Method '{method}' is invalid for servicer Queue."
                "\n"
                "Do you have a browser tab open for an older version "
                "of this application, or for a different application all together?"
            )
            raise IMPORT_rebootdev.aio.aborted.SystemAborted(
                IMPORT_rbt_v1alpha1.errors_pb2.InvalidMethod(),
                message=
                    f"Method '{method}' not found"
            )
            yield  # Unreachable but necessary for mypy.

    async def react_mutate(
        self,
        headers: IMPORT_reboot_aio_headers.Headers,
        method: str,
        request_bytes: bytes,
    ) -> IMPORT_google_protobuf_message.Message:
        """Returns the response of calling 'method' given a message
        deserialized from the provided 'request_bytes'."""
        if method == 'Enqueue':
            request = rbt.std.collections.queue.v1.queue_pb2.EnqueueRequest()
            request.ParseFromString(request_bytes)

            # NOTE: we automatically retry mutations that come through
            # React when we get a `IMPORT_grpc.StatusCode.UNAVAILABLE` to
            # match the retry logic we do in the React code generated
            # to handle lack/loss of connectivity.
            #
            # TODO(benh): revisit this decision if we ever see reason
            # to call `react_mutate()` from any place other than where
            # we're executing React (e.g., browser, next.js server
            # component, etc).
            call_backoff = IMPORT_reboot_aio_backoff.Backoff()
            while True:
                # We make a full-fledged gRPC call, so that if this traffic
                # was misrouted (i.e. this server is not authoritative
                # for the state), it will now go to the right place. The
                # receiving middleware will handle things like effect
                # validation and so forth.
                assert headers.application_id is not None  # Guaranteed by `Headers`.
                stub = rbt.std.collections.queue.v1.queue_pb2_grpc.QueueMethodsStub(
                    self.channel_manager.get_channel_to(
                        self.placement_client.address_for_actor(
                            headers.application_id,
                            headers.state_ref,
                        )
                    )
                )
                call = stub.Enqueue(
                    request=request,
                    metadata=headers.to_grpc_metadata(),
                )
                try:
                    return await call
                except IMPORT_grpc.aio.AioRpcError as error:
                    if error.code() == IMPORT_grpc.StatusCode.UNAVAILABLE:
                        await call_backoff()
                        continue

                    # Reconstitute the error that the server threw, if it was a declared error.
                    status = await IMPORT_rpc_status_async.from_call(call)
                    if status is not None:
                        raise Queue.EnqueueAborted.from_status(
                            status
                        ) from None
                    raise Queue.EnqueueAborted.from_grpc_aio_rpc_error(
                        error
                     ) from None

        elif method == 'Dequeue':
            raise IMPORT_rebootdev.aio.aborted.SystemAborted(
                IMPORT_rbt_v1alpha1.errors_pb2.InvalidMethod(),
                message=
                f"Method 'Dequeue' can not be called via React (for now)"
            )
        elif method == 'TryDequeue':
            request = rbt.std.collections.queue.v1.queue_pb2.DequeueRequest()
            request.ParseFromString(request_bytes)

            # NOTE: we automatically retry mutations that come through
            # React when we get a `IMPORT_grpc.StatusCode.UNAVAILABLE` to
            # match the retry logic we do in the React code generated
            # to handle lack/loss of connectivity.
            #
            # TODO(benh): revisit this decision if we ever see reason
            # to call `react_mutate()` from any place other than where
            # we're executing React (e.g., browser, next.js server
            # component, etc).
            call_backoff = IMPORT_reboot_aio_backoff.Backoff()
            while True:
                # We make a full-fledged gRPC call, so that if this traffic
                # was misrouted (i.e. this server is not authoritative
                # for the state), it will now go to the right place. The
                # receiving middleware will handle things like effect
                # validation and so forth.
                assert headers.application_id is not None  # Guaranteed by `Headers`.
                stub = rbt.std.collections.queue.v1.queue_pb2_grpc.QueueMethodsStub(
                    self.channel_manager.get_channel_to(
                        self.placement_client.address_for_actor(
                            headers.application_id,
                            headers.state_ref,
                        )
                    )
                )
                call = stub.TryDequeue(
                    request=request,
                    metadata=headers.to_grpc_metadata(),
                )
                try:
                    return await call
                except IMPORT_grpc.aio.AioRpcError as error:
                    if error.code() == IMPORT_grpc.StatusCode.UNAVAILABLE:
                        await call_backoff()
                        continue

                    # Reconstitute the error that the server threw, if it was a declared error.
                    status = await IMPORT_rpc_status_async.from_call(call)
                    if status is not None:
                        raise Queue.TryDequeueAborted.from_status(
                            status
                        ) from None
                    raise Queue.TryDequeueAborted.from_grpc_aio_rpc_error(
                        error
                     ) from None

        elif method == 'Empty':
            # Invariant here is that users should not have called this
            # directly but only through code generated React
            # components which should not have been generated except
            # for valid method candidates.
            logger.warning(
                "Got a react mutate request with an invalid method name: "
                "Method 'Empty' is invalid for servicer Queue."
                "\n"
                "Do you have an old browser tab still open for an older version "
                "of this application, or a different application all together?"
            )
            raise IMPORT_rebootdev.aio.aborted.SystemAborted(
                IMPORT_rbt_v1alpha1.errors_pb2.InvalidMethod(),
                message=f"Method '{method}' is invalid"
            )
        else:
            logger.warning(
                "Got a react mutate request with an invalid method name: "
                f"Method '{method}' is invalid for servicer Queue."
                "\n"
                "Do you have an old browser tab still open for an older version "
                "of this application, or a different application all together?"
            )
            raise IMPORT_rebootdev.aio.aborted.SystemAborted(
                IMPORT_rbt_v1alpha1.errors_pb2.InvalidMethod(),
                message=
                    f"Method '{method}' not found"
            )

    async def dispatch(
        self,
        task: IMPORT_reboot_aio_tasks.TaskEffect,
        *,
        only_validate: bool = False,
        on_loop_iteration: IMPORT_reboot_aio_internals_tasks_dispatcher.OnLoopIterationCallable = (lambda iteration, next_iteration_schedule: None),
    ) -> IMPORT_reboot_aio_internals_tasks_dispatcher.TaskResponseOrStatus:
        """Dispatches the tasks to execute unless 'only_validate' is set to
        true, in which case just ensures that the task actually exists.
        Note that this function will be called *by* tasks_dispatcher; it will
        not itself call into tasks_dispatcher."""

        if 'Enqueue' == task.method_name:
            if only_validate:
                # TODO(benh): validate 'task.request' is correct type.
                return (rbt.std.collections.queue.v1.queue_pb2.EnqueueResponse(), None)

            # Use an inline method to create a new scope, so that we can use
            # variable names like `context` and `effects` in multiple branches
            # in this code (notably when there are multiple task types) without
            # hitting a mypy error that the variable's type is not consistent.
            async def run_Enqueue(
                context: IMPORT_reboot_aio_contexts.WorkflowContext,
                *,
                validating_effects: bool = False,
            ):
                async with self._state_manager.task_workflow(
                    context,
                    task,
                    on_loop_iteration=on_loop_iteration,
                    validating_effects=validating_effects,
                ) as complete:
                    try:
                        response = await (QueueWorkflowStub(
                            context=context,
                            state_ref=context._state_ref,
                        ).Enqueue(
                            QueueEnqueueRequestFromProto(IMPORT_typing.cast(rbt.std.collections.queue.v1.queue_pb2.EnqueueRequest, task.request)),
                            bearer_token=__internal_magic_token__,
                            idempotency=IMPORT_reboot_aio_idempotency.Idempotency(
                                alias=f'Task {IMPORT_uuid.UUID(bytes=task.task_id.task_uuid)}',
                            ),
                        ))
                        await complete(task, (response, None))
                        return (response, None)
                    except IMPORT_asyncio.CancelledError:
                        # Do not retry a task if it was cancelled by a caller.
                        if self.tasks_dispatcher.is_task_cancelled(task.task_id.task_uuid):
                            result = (
                                None,
                                IMPORT_rebootdev.aio.aborted.SystemAborted(
                                    IMPORT_rbt_v1alpha1.errors_pb2.Cancelled(),
                                ).to_status(),
                            )
                            await complete(task, result)
                            return result
                        else:
                            raise
                    except IMPORT_rebootdev.aio.aborted.Aborted as aborted:
                        error_type = f'{aborted.error.__class__.__module__}.{aborted.error.__class__.__qualname__}'
                        # Do not retry a task if the error was specified in the
                        # proto file.
                        if error_type in self._specified_errors_by_service_method_name.get('rbt.std.collections.queue.v1.QueueMethods.Enqueue', []):
                            result = (None, aborted.to_status())
                            await complete(task, result)
                            return result
                        raise


            return await run_Enqueue(
                self.create_context(
                    headers=IMPORT_reboot_aio_headers.Headers(
                        application_id=self.application_id,
                        state_ref=IMPORT_reboot_aio_types.StateRef(task.task_id.state_ref),
                    ),
                    state_type_name = IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue'),
                    method='Enqueue',
                    context_type=IMPORT_reboot_aio_contexts.WorkflowContext,
                    task=task,
                )
            )
        elif 'Dequeue' == task.method_name:
            if only_validate:
                # TODO(benh): validate 'task.request' is correct type.
                return (rbt.std.collections.queue.v1.queue_pb2.DequeueResponse(), None)

            # Use an inline method to create a new scope, so that we can use
            # variable names like `context` and `effects` in multiple branches
            # in this code (notably when there are multiple task types) without
            # hitting a mypy error that the variable's type is not consistent.
            async def run_Dequeue(
                context: IMPORT_reboot_aio_contexts.WorkflowContext,
                *,
                validating_effects: bool = False,
            ):
                async with self._state_manager.task_workflow(
                    context,
                    task,
                    on_loop_iteration=on_loop_iteration,
                    validating_effects=validating_effects,
                ) as complete:
                    try:
                        response = await self.__Dequeue(
                            context,
                            IMPORT_typing.cast(rbt.std.collections.queue.v1.queue_pb2.DequeueRequest, task.request),
                            validating_effects=validating_effects,
                        )
                        await complete(task, (response, None))
                        return (response, None)
                    except IMPORT_asyncio.CancelledError:
                        # Do not retry a task if it was cancelled by a caller.
                        if self.tasks_dispatcher.is_task_cancelled(task.task_id.task_uuid):
                            result = (
                                None,
                                IMPORT_rebootdev.aio.aborted.SystemAborted(
                                    IMPORT_rbt_v1alpha1.errors_pb2.Cancelled(),
                                ).to_status(),
                            )
                            await complete(task, result)
                            return result
                        else:
                            raise
                    except IMPORT_rebootdev.aio.aborted.Aborted as aborted:
                        error_type = f'{aborted.error.__class__.__module__}.{aborted.error.__class__.__qualname__}'
                        # Do not retry a task if the error was specified in the
                        # proto file.
                        if error_type in self._specified_errors_by_service_method_name.get('rbt.std.collections.queue.v1.QueueMethods.Dequeue', []):
                            result = (None, aborted.to_status())
                            await complete(task, result)
                            return result
                        raise

            @IMPORT_reboot_aio_internals_middleware.maybe_run_function_twice_to_validate_effects
            async def run_Dequeue_reactively(
                validating_effects: bool,
                context: IMPORT_reboot_aio_contexts.WorkflowContext,
            ):
                async with self._state_manager.reactively(
                    context,
                    self._servicer.__state_type__,
                    # Already authorized when we created the task.
                    authorize=None,
                ):
                    try:
                        # When we're validating effects we
                        # periodically timeout so that we can log
                        # that a workflow might be hung, i.e., the
                        # user has a bug.
                        task = IMPORT_asyncio.create_task(
                            run_Dequeue(
                                context,
                                validating_effects=validating_effects,
                            )
                        )
                        timeout = None if not validating_effects else 5  # seconds
                        while True:
                            done, pending = await IMPORT_asyncio.wait(
                                [task],
                                timeout=timeout,
                            )
                            # Check if we've timed out, which
                            # should only occur if we're
                            # validating effects.
                            if len(done) == 0:
                                assert validating_effects and timeout is not None
                                logger.warning(
                                    f'Still waiting for method Queue.Dequeue '
                                    'to complete after re-running to validate effects.'
                                )
                                timeout += 5  # seconds
                                continue
                            return task.result()
                    finally:
                        if not task.done():
                            task.cancel()
                            # Need to actually await the task so if
                            # there is an exception we don't get a
                            # warning logged that the exception was
                            # never retrieved, but we don't care about
                            # the exception because we're done with
                            # the task.
                            try:
                                await task
                            except:
                                pass

            return await run_Dequeue_reactively(
                self.create_context(
                    headers=IMPORT_reboot_aio_headers.Headers(
                        application_id=self.application_id,
                        state_ref=IMPORT_reboot_aio_types.StateRef(task.task_id.state_ref),
                        workflow_id=IMPORT_uuid.UUID(bytes=task.task_id.task_uuid),
                    ),
                    state_type_name = IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue'),
                    method='Dequeue',
                    context_type=IMPORT_reboot_aio_contexts.WorkflowContext,
                    task=task,
                )
            )
        elif 'TryDequeue' == task.method_name:
            if only_validate:
                # TODO(benh): validate 'task.request' is correct type.
                return (rbt.std.collections.queue.v1.queue_pb2.DequeueResponse(), None)

            # Use an inline method to create a new scope, so that we can use
            # variable names like `context` and `effects` in multiple branches
            # in this code (notably when there are multiple task types) without
            # hitting a mypy error that the variable's type is not consistent.
            async def run_TryDequeue(
                context: IMPORT_reboot_aio_contexts.WorkflowContext,
                *,
                validating_effects: bool = False,
            ):
                async with self._state_manager.task_workflow(
                    context,
                    task,
                    on_loop_iteration=on_loop_iteration,
                    validating_effects=validating_effects,
                ) as complete:
                    try:
                        response = await (QueueWorkflowStub(
                            context=context,
                            state_ref=context._state_ref,
                        ).TryDequeue(
                            QueueTryDequeueRequestFromProto(IMPORT_typing.cast(rbt.std.collections.queue.v1.queue_pb2.DequeueRequest, task.request)),
                            bearer_token=__internal_magic_token__,
                            idempotency=IMPORT_reboot_aio_idempotency.Idempotency(
                                alias=f'Task {IMPORT_uuid.UUID(bytes=task.task_id.task_uuid)}',
                            ),
                        ))
                        await complete(task, (response, None))
                        return (response, None)
                    except IMPORT_asyncio.CancelledError:
                        # Do not retry a task if it was cancelled by a caller.
                        if self.tasks_dispatcher.is_task_cancelled(task.task_id.task_uuid):
                            result = (
                                None,
                                IMPORT_rebootdev.aio.aborted.SystemAborted(
                                    IMPORT_rbt_v1alpha1.errors_pb2.Cancelled(),
                                ).to_status(),
                            )
                            await complete(task, result)
                            return result
                        else:
                            raise
                    except IMPORT_rebootdev.aio.aborted.Aborted as aborted:
                        error_type = f'{aborted.error.__class__.__module__}.{aborted.error.__class__.__qualname__}'
                        # Do not retry a task if the error was specified in the
                        # proto file.
                        if error_type in self._specified_errors_by_service_method_name.get('rbt.std.collections.queue.v1.QueueMethods.TryDequeue', []):
                            result = (None, aborted.to_status())
                            await complete(task, result)
                            return result
                        raise


            return await run_TryDequeue(
                self.create_context(
                    headers=IMPORT_reboot_aio_headers.Headers(
                        application_id=self.application_id,
                        state_ref=IMPORT_reboot_aio_types.StateRef(task.task_id.state_ref),
                    ),
                    state_type_name = IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue'),
                    method='TryDequeue',
                    context_type=IMPORT_reboot_aio_contexts.WorkflowContext,
                    task=task,
                )
            )
        elif 'Empty' == task.method_name:
            if only_validate:
                # TODO(benh): validate 'task.request' is correct type.
                return (rbt.std.collections.queue.v1.queue_pb2.EmptyResponse(), None)

            # Use an inline method to create a new scope, so that we can use
            # variable names like `context` and `effects` in multiple branches
            # in this code (notably when there are multiple task types) without
            # hitting a mypy error that the variable's type is not consistent.
            async def run_Empty(
                context: IMPORT_reboot_aio_contexts.WorkflowContext,
                *,
                validating_effects: bool = False,
            ):
                async with self._state_manager.task_workflow(
                    context,
                    task,
                    on_loop_iteration=on_loop_iteration,
                    validating_effects=validating_effects,
                ) as complete:
                    try:
                        response = await (QueueWorkflowStub(
                            context=context,
                            state_ref=context._state_ref,
                        ).Empty(
                            QueueEmptyRequestFromProto(IMPORT_typing.cast(rbt.std.collections.queue.v1.queue_pb2.EmptyRequest, task.request)),
                            bearer_token=__internal_magic_token__,
                        ))
                        await complete(task, (response, None))
                        return (response, None)
                    except IMPORT_asyncio.CancelledError:
                        # Do not retry a task if it was cancelled by a caller.
                        if self.tasks_dispatcher.is_task_cancelled(task.task_id.task_uuid):
                            result = (
                                None,
                                IMPORT_rebootdev.aio.aborted.SystemAborted(
                                    IMPORT_rbt_v1alpha1.errors_pb2.Cancelled(),
                                ).to_status(),
                            )
                            await complete(task, result)
                            return result
                        else:
                            raise
                    except IMPORT_rebootdev.aio.aborted.Aborted as aborted:
                        error_type = f'{aborted.error.__class__.__module__}.{aborted.error.__class__.__qualname__}'
                        # Do not retry a task if the error was specified in the
                        # proto file.
                        if error_type in self._specified_errors_by_service_method_name.get('rbt.std.collections.queue.v1.QueueMethods.Empty', []):
                            result = (None, aborted.to_status())
                            await complete(task, result)
                            return result
                        raise


            return await run_Empty(
                self.create_context(
                    headers=IMPORT_reboot_aio_headers.Headers(
                        application_id=self.application_id,
                        state_ref=IMPORT_reboot_aio_types.StateRef(task.task_id.state_ref),
                    ),
                    state_type_name = IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue'),
                    method='Empty',
                    context_type=IMPORT_reboot_aio_contexts.WorkflowContext,
                    task=task,
                )
            )

        # There are no tasks for this service.
        start_or_validate = "start" if not only_validate else "validate"
        raise RuntimeError(
            f"Attempted to {start_or_validate} task '{task.method_name}' "
            f"on 'Queue' which does not exist"
        )

    # Queue specific methods:
    async def __Enqueue(
        self,
        context: IMPORT_reboot_aio_contexts.TransactionContext,
        state: rbt.std.collections.queue.v1.queue_pb2.Queue,
        request: rbt.std.collections.queue.v1.queue_pb2.EnqueueRequest,
        *,
        validating_effects: bool,
    ) -> rbt.std.collections.queue.v1.queue_pb2.EnqueueResponse:
        try:
            typed_state: Queue.State = QueueFromProto(state, is_initial_state=(context.state_id in states_being_constructed))

            response = (
                await self._servicer._Enqueue(
                    context=context,
                    state=typed_state,
                    request=request
                )
            )


            QueueToProto(typed_state, state)

            IMPORT_reboot_aio_types.assert_type(
                response,
                [rbt.std.collections.queue.v1.queue_pb2.EnqueueResponse],
            )
            self.maybe_raise_effect_validation_retry(
                logger=logger,
                idempotency_manager=context,
                method_name='Queue.Enqueue',
                validating_effects=validating_effects,
                context=context,
            )
            return response
        except IMPORT_reboot_aio_contexts.RetryReactively:
            # Retrying reactively, just let this propagate.
            raise
        except IMPORT_reboot_aio_contexts.EffectValidationRetry:
            # Doing effect validation, just let this propagate.
            raise
        except IMPORT_rebootdev.aio.aborted.Aborted as aborted:
            # If the caller aborted due to a retryable error, just
            # propagate the aborted instead of propagating `Unknown`
            # so that a client can transparently retry.
            if IMPORT_rebootdev.aio.aborted.is_retryable(aborted):
                raise aborted
            # Log any _unhandled_ abort stack traces to make it
            # easier for debugging.
            #
            # NOTE: we don't log if we're a task as it will be logged
            # in `public/rebootdev/aio/internals/tasks_dispatcher.py` instead.
            aborted_type: IMPORT_typing.Optional[type] = None
            aborted_type = Queue.EnqueueAborted
            if isinstance(aborted, IMPORT_rebootdev.aio.aborted.SystemAborted):
                # Not logging when within `node` as we already log there.
                if IMPORT_reboot_nodejs_python.should_print_stacktrace():
                    logger.warning(
                        f"Unhandled (in 'rbt.std.collections.queue.v1.Queue.Enqueue') {aborted}; propagating as 'Unknown'\n" +
                        ''.join(IMPORT_traceback.format_exception(aborted))
                    )
                raise IMPORT_rebootdev.aio.aborted.SystemAborted(
                    IMPORT_rbt_v1alpha1.errors_pb2.Unknown(),
                    # TODO(benh): consider whether or not we want to
                    # include the 'package.service.method' which may
                    # get concatenated together forming a kind of
                    # "stack trace"; while it's super helpful for
                    # debugging, it does expose implementation
                    # information.
                    message=f"unhandled (in 'rbt.std.collections.queue.v1.Queue.Enqueue') {aborted}"
                )
            else:
                if (
                    aborted_type is not None and
                    not isinstance(aborted, aborted_type) and
                    aborted_type.is_declared_error(aborted.error)
                ):
                    # We propagate declared errors that might have
                    # come from another call, i.e., we might have an
                    # `Aborted` but not for this method but the
                    # `Aborted` that we have has an error that this
                    # method declared. This allows a developer to
                    # simply add the declared error to their `.proto`
                    # file rather than having to catch and re-raise
                    # the error with their own aborted type.
                    if context.task is None:
                        logger.warning(
                            f"Propagating unhandled but declared error (in 'rbt.std.collections.queue.v1.Queue.Enqueue') {aborted}"
                        )
                elif (
                    aborted_type is None or
                    not isinstance(aborted, aborted_type)
                ):
                    # Not logging when within `node` as we already log there.
                    if IMPORT_reboot_nodejs_python.should_print_stacktrace():
                        logger.warning(
                            f"Unhandled (in 'rbt.std.collections.queue.v1.Queue.Enqueue') {aborted}; propagating as 'Unknown'\n" +
                            ''.join(IMPORT_traceback.format_exception(aborted))
                        )
                    # If this wasn't a declared error than we
                    # propagate it as `Unknown`.
                    raise IMPORT_rebootdev.aio.aborted.SystemAborted(
                        IMPORT_rbt_v1alpha1.errors_pb2.Unknown(),
                        # TODO(benh): consider whether or not we want to
                        # include the 'package.service.method' which may
                        # get concatenated together forming a kind of
                        # "stack trace"; while it's super helpful for
                        # debugging, it does expose implementation
                        # information.
                        message=f"unhandled (in 'rbt.std.collections.queue.v1.Queue.Enqueue') {aborted}"
                    )

            raise
        except IMPORT_asyncio.CancelledError:
            # It's pretty normal for an RPC to be cancelled; it's not useful to
            # print a stack trace.
            raise
        except IMPORT_google_protobuf_message.DecodeError as decode_error:
            # We usually see this error when we are trying to construct a proto
            # message which is too deeply nested: protobuf has a limit of 100
            # nested messages. See the limits here:
            #   https://protobuf.dev/programming-guides/proto-limits/

            if IMPORT_reboot_nodejs_python.should_print_stacktrace():
                logger.warning(
                    "Unhandled (in 'rbt.std.collections.queue.v1.Queue.Enqueue') "
                    f"{type(decode_error).__name__}{': ' + str(decode_error) if len(str(decode_error)) > 0 else ''}; "
                    "This is usually caused by a deeply nested protobuf message, which is not supported by protobuf.\n"
                    "See the limits here: https://protobuf.dev/programming-guides/proto-limits/" +
                    ''.join(IMPORT_traceback.format_exception(decode_error))
                )
            raise IMPORT_rebootdev.aio.aborted.SystemAborted(
                IMPORT_rbt_v1alpha1.errors_pb2.Unknown(),
                message=f"unhandled (in 'rbt.std.collections.queue.v1.Queue.Enqueue') {decode_error}; "
                        "This is usually caused by a deeply nested protobuf message, which is not supported by protobuf.\n"
                        "See the limits here: https://protobuf.dev/programming-guides/proto-limits/"
            )
        except BaseException as exception:
            # Not logging when within `node` as we already log there.
            if IMPORT_reboot_nodejs_python.should_print_stacktrace():
                logger.warning(
                    "Unhandled (in 'rbt.std.collections.queue.v1.Queue.Enqueue') "
                    f"{type(exception).__name__}{': ' + str(exception) if len(str(exception)) > 0 else ''}; "
                    "propagating as 'Unknown'\n" +
                    ''.join(IMPORT_traceback.format_exception(exception))
                )
            raise IMPORT_rebootdev.aio.aborted.SystemAborted(
                IMPORT_rbt_v1alpha1.errors_pb2.Unknown(),
                # TODO(benh): consider whether or not we want to
                # include the 'package.service.method' which may
                # get concatenated together forming a kind of
                # "stack trace"; while it's super helpful for
                # debugging, it does expose implementation
                # information.
                message=f"unhandled (in 'rbt.std.collections.queue.v1.Queue.Enqueue') {type(exception).__name__}: {exception}"
            )
        finally:
            pass

    @IMPORT_reboot_aio_tracing.function_span(
        # We expect an `EffectValidationRetry` exception; that's not an error.
        set_status_on_exception=False
    )
    async def _Enqueue(
        self,
        request: rbt.std.collections.queue.v1.queue_pb2.EnqueueRequest,
        context: IMPORT_reboot_aio_contexts.TransactionContext,
        *,
        validating_effects: bool,
        grpc_context: IMPORT_typing.Optional[IMPORT_grpc.aio.ServicerContext] = None,
    ) -> rbt.std.collections.queue.v1.queue_pb2.EnqueueResponse:
        # Try to verify the token if a token verifier exists.
        context.auth = await self._maybe_verify_token(
            headers=context._headers, method='Enqueue'
        )

        # Check if we already have performed this mutation!
        #
        # We do this _before_ calling 'transactionally()' because
        # if this call is for a transaction method _and_ we've
        # already performed the transaction then we don't want to
        # become a transaction participant (again) we just want to
        # return the transaction's response.
        idempotent_mutation = await self._state_manager.check_for_idempotent_mutation(
            context
        )

        if idempotent_mutation is not None:
            response = rbt.std.collections.queue.v1.queue_pb2.EnqueueResponse()
            response.ParseFromString(idempotent_mutation.response)
            return response

        async with self._state_manager.transactionally(
            context,
            self.tasks_dispatcher,
            aborted_type=Queue.EnqueueAborted,
        ) as transaction:
            if transaction is not None:
                context.participants.add(
                    self._servicer.__state_type_name__, context._state_ref
                )
            assert transaction is not None
            async with self._state_manager.transaction(
                context,
                self._servicer.__state_type__,
                transaction,
                authorize=self._maybe_authorize(
                    method_name='rbt.std.collections.queue.v1.QueueMethods.Enqueue',
                    headers=context._headers,
                    auth=context.auth,
                    request=request,
                ),
                from_constructor=False,
                requires_constructor=False
            ) as (state, complete):

                response = await self.__Enqueue(
                    context,
                    state,
                    request,
                    validating_effects=validating_effects,
                )

                await complete(
                    IMPORT_reboot_aio_state_managers.Effects(
                        state=state,
                        response=response,
                    )
                )
                return response

    async def _schedule_Enqueue(
        self,
        *,
        request: rbt.std.collections.queue.v1.queue_pb2.EnqueueRequest,
        headers: IMPORT_reboot_aio_headers.Headers,
        grpc_context: IMPORT_grpc.aio.ServicerContext,
    ) -> tuple[IMPORT_reboot_aio_contexts.WriterContext, rbt.std.collections.queue.v1.queue_pb2.EnqueueResponse]:
        context: IMPORT_reboot_aio_contexts.WriterContext = self.create_context(
            headers=headers,
            state_type_name = IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue'),
            method='Enqueue',
            context_type=IMPORT_reboot_aio_contexts.WriterContext,
        )
        response = rbt.std.collections.queue.v1.queue_pb2.EnqueueResponse()

        # Check if we already have performed this schedule! Note that
        # we need to do this for all kinds of methods because this is
        # effectively a mutation (actually a `writer`, see below).
        #
        # We do this _before_ calling 'transactionally()' because
        # if this call is for a transaction method _and_ we've
        # already performed the transaction then we don't want to
        # become a transaction participant (again) we just want to
        # return the transaction's response.
        idempotent_mutation = await self._state_manager.check_for_idempotent_mutation(
            context
        )

        if idempotent_mutation is not None:
            response.ParseFromString(idempotent_mutation.response)

            # We should have only scheduled a single task!
            assert len(idempotent_mutation.task_ids) == 1
            assert grpc_context is not None
            grpc_context.set_trailing_metadata(
                grpc_context.trailing_metadata() +
                (
                    (
                        IMPORT_reboot_aio_headers.TASK_ID_UUID,
                        str(IMPORT_uuid.UUID(bytes=idempotent_mutation.task_ids[0].task_uuid))
                    ),
                )
            )

            return context, response

        async with self._state_manager.transactionally(
            context,
            self.tasks_dispatcher,
            aborted_type=Queue.EnqueueAborted,
        ) as transaction:
            if transaction is not None:
                context.participants.add(
                    self._servicer.__state_type_name__, context._state_ref
                )

            # Try to verify the token if a token verifier exists.
            context.auth = await self._maybe_verify_token(
                headers=headers, method='Enqueue'
            )

            async with self._state_manager.writer(
                context,
                self._servicer.__state_type__,
                self.tasks_dispatcher,
                transaction=transaction,
                authorize=self._maybe_authorize(
                    method_name='rbt.std.collections.queue.v1.QueueMethods.Enqueue',
                    headers=context._headers,
                    auth=context.auth,
                    request=request,
                ),
                from_constructor=False,
                requires_constructor=False
            ) as (state, writer):

                task = await QueueServicerTasks(
                    context=context,
                    state_ref=context._state_ref,
                ).Enqueue(
                    QueueEnqueueRequestFromProto(request),
                    schedule=context._headers.task_schedule,
                )

                effects = IMPORT_reboot_aio_state_managers.Effects(
                    response=response,
                    state=state,
                    tasks=[task],
                )

                assert effects.tasks is not None

                await writer.complete(effects)

                assert grpc_context is not None

                grpc_context.set_trailing_metadata(
                    grpc_context.trailing_metadata() +
                    (
                        (
                            IMPORT_reboot_aio_headers.TASK_ID_UUID,
                            str(IMPORT_uuid.UUID(bytes=task.task_id.task_uuid))
                        ),
                    )
                )

                return context, response

        return context, response


    # Entrypoint for non-reactive network calls (i.e. typical gRPC calls).
    async def Enqueue(
        self,
        request: rbt.std.collections.queue.v1.queue_pb2.EnqueueRequest,
        grpc_context: IMPORT_grpc.aio.ServicerContext,
    ) -> rbt.std.collections.queue.v1.queue_pb2.EnqueueResponse:
        headers = IMPORT_reboot_aio_headers.Headers.from_grpc_context(grpc_context)
        assert headers.application_id is not None  # Guaranteed by `Headers`.

        # Confirm whether this is the right server to be serving this
        # request.
        authoritative_server = self.placement_client.server_for_actor(
            headers.application_id,
            headers.state_ref,
        )
        if authoritative_server != self.server_id:
            # This is NOT the correct server. Fail.
            await grpc_context.abort(
                IMPORT_grpc.StatusCode.UNAVAILABLE,
                f"Server '{self.server_id}' is not authoritative for this "
                f"request; server '{authoritative_server}' is.",
            )
            raise  # Unreachable but necessary for mypy.

        @IMPORT_reboot_aio_internals_middleware.maybe_run_function_twice_to_validate_effects
        async def _run(
            validating_effects: bool,
        ) -> rbt.std.collections.queue.v1.queue_pb2.EnqueueResponse:
            context: IMPORT_typing.Optional[IMPORT_reboot_aio_contexts.Context] = None
            try:
                if headers.task_schedule is not None:
                    context, response = await self._schedule_Enqueue(
                        headers=headers,
                        request=request,
                        grpc_context=grpc_context,
                    )
                    return response

                context = self.create_context(
                    headers=headers,
                    state_type_name = IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue'),
                    method='Enqueue',
                    context_type=IMPORT_reboot_aio_contexts.TransactionContext,
                )
                assert context is not None

                return await self._Enqueue(
                    request,
                    context,
                    validating_effects=validating_effects,
                    grpc_context=grpc_context,
                )
            except IMPORT_reboot_aio_contexts.EffectValidationRetry:
                # Doing effect validation, just let this propagate.
                raise
            except IMPORT_rebootdev.aio.aborted.Aborted as aborted:
                status = IMPORT_rpc_status_sync.to_status(aborted.to_status())
                # Need to add transaction participants here because
                # calling `grpc_context.abort_with_status()` will
                # ignore any other trailing metadata. Only propagate
                # transaction participants metadata if the caller cares.
                # Callers that care are those that are themselves transactions.
                # It's important to not just send this information to everyone;
                # some clients can't tolerate trailers, see:
                #   https://github.com/reboot-dev/mono/issues/5081
                if context is not None and headers.transaction_ids is not None:
                    assert context.transaction_id is not None
                    status = status._replace(
                        trailing_metadata=status.trailing_metadata + context.participants.to_grpc_metadata()
                    )
                await grpc_context.abort_with_status(status)
                raise  # Unreachable but necessary for mypy.
            except IMPORT_asyncio.CancelledError:
                # It's pretty normal for an RPC to be cancelled; it's not useful to
                # print a stack trace.
                raise
            except BaseException as exception:
                # Print the exception stack trace for easier debugging. Note
                # that we don't include the stack trace in an error message
                # for the same reason that gRPC doesn't do so by default,
                # see https://github.com/grpc/grpc/issues/14897, but since this
                # should only get logged on the server side it is safe.
                logger.warning(
                    'Unhandled exception\n' +
                    ''.join(IMPORT_traceback.format_exc() if IMPORT_reboot_nodejs_python.should_print_stacktrace() else [f"{type(exception).__name__}: {exception}"])
                )

                # Re-raise the exception for gRPC to handle!
                #
                # TODO: gRPC will print a stack trace from this
                # exception which we don't want if we're executing via
                # Node.js.
                raise
            finally:
                # Propagate transaction participants, if the caller cares.
                # Callers that care are those that are themselves transactions.
                # It's important to not just send this information to everyone;
                # some clients can't tolerate trailers, see:
                #   https://github.com/reboot-dev/mono/issues/5081
                if context is not None and headers.transaction_ids is not None:
                    assert context.transaction_id is not None
                    grpc_context.set_trailing_metadata(
                        grpc_context.trailing_metadata() +
                        context.participants.to_grpc_metadata()
                    )

        with IMPORT_reboot_aio_tracing.context_from_headers(headers):
            return await _run()

    async def __Dequeue(
        self,
        context: IMPORT_reboot_aio_contexts.WorkflowContext,
        request: rbt.std.collections.queue.v1.queue_pb2.DequeueRequest,
        *,
        validating_effects: bool,
    ) -> rbt.std.collections.queue.v1.queue_pb2.DequeueResponse:
        try:
            # We should have an asyncio task and thus context per request,
            # let's confirm this assumption by making sure that
            # `__servicer__ is None`.
            assert self._servicer.__servicer__.get() is None
            self._servicer.__servicer__.set(self._servicer)
            response = (
                await self._servicer._Dequeue(
                    context=context,
                    request=request
                )
            )



            IMPORT_reboot_aio_types.assert_type(
                response,
                [rbt.std.collections.queue.v1.queue_pb2.DequeueResponse],
            )
            self.maybe_raise_effect_validation_retry(
                logger=logger,
                idempotency_manager=context,
                method_name='Queue.Dequeue',
                validating_effects=validating_effects,
                context=context,
            )
            return response
        except IMPORT_reboot_aio_contexts.RetryReactively:
            # Retrying reactively, just let this propagate.
            raise
        except IMPORT_reboot_aio_contexts.EffectValidationRetry:
            # Doing effect validation, just let this propagate.
            raise
        except IMPORT_rebootdev.aio.aborted.Aborted as aborted:
            # If the caller aborted due to a retryable error, just
            # propagate the aborted instead of propagating `Unknown`
            # so that a client can transparently retry.
            if IMPORT_rebootdev.aio.aborted.is_retryable(aborted):
                raise aborted
            # Log any _unhandled_ abort stack traces to make it
            # easier for debugging.
            #
            # NOTE: we don't log if we're a task as it will be logged
            # in `public/rebootdev/aio/internals/tasks_dispatcher.py` instead.
            aborted_type: IMPORT_typing.Optional[type] = None
            aborted_type = Queue.DequeueAborted
            if isinstance(aborted, IMPORT_rebootdev.aio.aborted.SystemAborted):
                # Not logging when within `node` as we already log there.
                if IMPORT_reboot_nodejs_python.should_print_stacktrace():
                    logger.warning(
                        f"Unhandled (in 'rbt.std.collections.queue.v1.Queue.Dequeue') {aborted}; propagating as 'Unknown'\n" +
                        ''.join(IMPORT_traceback.format_exception(aborted))
                    )
                raise IMPORT_rebootdev.aio.aborted.SystemAborted(
                    IMPORT_rbt_v1alpha1.errors_pb2.Unknown(),
                    # TODO(benh): consider whether or not we want to
                    # include the 'package.service.method' which may
                    # get concatenated together forming a kind of
                    # "stack trace"; while it's super helpful for
                    # debugging, it does expose implementation
                    # information.
                    message=f"unhandled (in 'rbt.std.collections.queue.v1.Queue.Dequeue') {aborted}"
                )
            else:
                if (
                    aborted_type is not None and
                    not isinstance(aborted, aborted_type) and
                    aborted_type.is_declared_error(aborted.error)
                ):
                    # We propagate declared errors that might have
                    # come from another call, i.e., we might have an
                    # `Aborted` but not for this method but the
                    # `Aborted` that we have has an error that this
                    # method declared. This allows a developer to
                    # simply add the declared error to their `.proto`
                    # file rather than having to catch and re-raise
                    # the error with their own aborted type.
                    if context.task is None:
                        logger.warning(
                            f"Propagating unhandled but declared error (in 'rbt.std.collections.queue.v1.Queue.Dequeue') {aborted}"
                        )
                elif (
                    aborted_type is None or
                    not isinstance(aborted, aborted_type)
                ):
                    # Not logging when within `node` as we already log there.
                    if IMPORT_reboot_nodejs_python.should_print_stacktrace():
                        logger.warning(
                            f"Unhandled (in 'rbt.std.collections.queue.v1.Queue.Dequeue') {aborted}; propagating as 'Unknown'\n" +
                            ''.join(IMPORT_traceback.format_exception(aborted))
                        )
                    # If this wasn't a declared error than we
                    # propagate it as `Unknown`.
                    raise IMPORT_rebootdev.aio.aborted.SystemAborted(
                        IMPORT_rbt_v1alpha1.errors_pb2.Unknown(),
                        # TODO(benh): consider whether or not we want to
                        # include the 'package.service.method' which may
                        # get concatenated together forming a kind of
                        # "stack trace"; while it's super helpful for
                        # debugging, it does expose implementation
                        # information.
                        message=f"unhandled (in 'rbt.std.collections.queue.v1.Queue.Dequeue') {aborted}"
                    )

            raise
        except IMPORT_asyncio.CancelledError:
            # It's pretty normal for an RPC to be cancelled; it's not useful to
            # print a stack trace.
            raise
        except IMPORT_google_protobuf_message.DecodeError as decode_error:
            # We usually see this error when we are trying to construct a proto
            # message which is too deeply nested: protobuf has a limit of 100
            # nested messages. See the limits here:
            #   https://protobuf.dev/programming-guides/proto-limits/

            if IMPORT_reboot_nodejs_python.should_print_stacktrace():
                logger.warning(
                    "Unhandled (in 'rbt.std.collections.queue.v1.Queue.Dequeue') "
                    f"{type(decode_error).__name__}{': ' + str(decode_error) if len(str(decode_error)) > 0 else ''}; "
                    "This is usually caused by a deeply nested protobuf message, which is not supported by protobuf.\n"
                    "See the limits here: https://protobuf.dev/programming-guides/proto-limits/" +
                    ''.join(IMPORT_traceback.format_exception(decode_error))
                )
            raise IMPORT_rebootdev.aio.aborted.SystemAborted(
                IMPORT_rbt_v1alpha1.errors_pb2.Unknown(),
                message=f"unhandled (in 'rbt.std.collections.queue.v1.Queue.Dequeue') {decode_error}; "
                        "This is usually caused by a deeply nested protobuf message, which is not supported by protobuf.\n"
                        "See the limits here: https://protobuf.dev/programming-guides/proto-limits/"
            )
        except BaseException as exception:
            # Not logging when within `node` as we already log there.
            if IMPORT_reboot_nodejs_python.should_print_stacktrace():
                logger.warning(
                    "Unhandled (in 'rbt.std.collections.queue.v1.Queue.Dequeue') "
                    f"{type(exception).__name__}{': ' + str(exception) if len(str(exception)) > 0 else ''}; "
                    "propagating as 'Unknown'\n" +
                    ''.join(IMPORT_traceback.format_exception(exception))
                )
            raise IMPORT_rebootdev.aio.aborted.SystemAborted(
                IMPORT_rbt_v1alpha1.errors_pb2.Unknown(),
                # TODO(benh): consider whether or not we want to
                # include the 'package.service.method' which may
                # get concatenated together forming a kind of
                # "stack trace"; while it's super helpful for
                # debugging, it does expose implementation
                # information.
                message=f"unhandled (in 'rbt.std.collections.queue.v1.Queue.Dequeue') {type(exception).__name__}: {exception}"
            )
        finally:
            self._servicer.__servicer__.set(None)
            pass


    async def _schedule_Dequeue(
        self,
        *,
        request: rbt.std.collections.queue.v1.queue_pb2.DequeueRequest,
        headers: IMPORT_reboot_aio_headers.Headers,
        grpc_context: IMPORT_grpc.aio.ServicerContext,
    ) -> tuple[IMPORT_reboot_aio_contexts.WriterContext, rbt.std.collections.queue.v1.queue_pb2.DequeueResponse]:
        context: IMPORT_reboot_aio_contexts.WriterContext = self.create_context(
            headers=headers,
            state_type_name = IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue'),
            method='Dequeue',
            context_type=IMPORT_reboot_aio_contexts.WriterContext,
        )
        response = rbt.std.collections.queue.v1.queue_pb2.DequeueResponse()

        # Check if we already have performed this schedule! Note that
        # we need to do this for all kinds of methods because this is
        # effectively a mutation (actually a `writer`, see below).
        #
        # We do this _before_ calling 'transactionally()' because
        # if this call is for a transaction method _and_ we've
        # already performed the transaction then we don't want to
        # become a transaction participant (again) we just want to
        # return the transaction's response.
        idempotent_mutation = await self._state_manager.check_for_idempotent_mutation(
            context
        )

        if idempotent_mutation is not None:
            response.ParseFromString(idempotent_mutation.response)

            # We should have only scheduled a single task!
            assert len(idempotent_mutation.task_ids) == 1
            assert grpc_context is not None
            grpc_context.set_trailing_metadata(
                grpc_context.trailing_metadata() +
                (
                    (
                        IMPORT_reboot_aio_headers.TASK_ID_UUID,
                        str(IMPORT_uuid.UUID(bytes=idempotent_mutation.task_ids[0].task_uuid))
                    ),
                )
            )

            return context, response

        async with self._state_manager.transactionally(
            context,
            self.tasks_dispatcher,
            aborted_type=Queue.DequeueAborted,
        ) as transaction:
            if transaction is not None:
                context.participants.add(
                    self._servicer.__state_type_name__, context._state_ref
                )

            # Try to verify the token if a token verifier exists.
            context.auth = await self._maybe_verify_token(
                headers=headers, method='Dequeue'
            )

            async with self._state_manager.writer(
                context,
                self._servicer.__state_type__,
                self.tasks_dispatcher,
                transaction=transaction,
                authorize=self._maybe_authorize(
                    method_name='rbt.std.collections.queue.v1.QueueMethods.Dequeue',
                    headers=context._headers,
                    auth=context.auth,
                    request=request,
                ),
                from_constructor=False,
                requires_constructor=False
            ) as (state, writer):

                task = await QueueServicerTasks(
                    context=context,
                    state_ref=context._state_ref,
                ).Dequeue(
                    QueueDequeueRequestFromProto(request),
                    schedule=context._headers.task_schedule,
                )

                effects = IMPORT_reboot_aio_state_managers.Effects(
                    response=response,
                    state=state,
                    tasks=[task],
                )

                assert effects.tasks is not None

                await writer.complete(effects)

                assert grpc_context is not None

                grpc_context.set_trailing_metadata(
                    grpc_context.trailing_metadata() +
                    (
                        (
                            IMPORT_reboot_aio_headers.TASK_ID_UUID,
                            str(IMPORT_uuid.UUID(bytes=task.task_id.task_uuid))
                        ),
                    )
                )

                return context, response

        return context, response


    # Entrypoint for non-reactive network calls (i.e. typical gRPC calls).
    async def Dequeue(
        self,
        request: rbt.std.collections.queue.v1.queue_pb2.DequeueRequest,
        grpc_context: IMPORT_grpc.aio.ServicerContext,
    ) -> rbt.std.collections.queue.v1.queue_pb2.DequeueResponse:
        headers = IMPORT_reboot_aio_headers.Headers.from_grpc_context(grpc_context)
        assert headers.application_id is not None  # Guaranteed by `Headers`.

        # Confirm whether this is the right server to be serving this
        # request.
        authoritative_server = self.placement_client.server_for_actor(
            headers.application_id,
            headers.state_ref,
        )
        if authoritative_server != self.server_id:
            # This is NOT the correct server. Fail.
            await grpc_context.abort(
                IMPORT_grpc.StatusCode.UNAVAILABLE,
                f"Server '{self.server_id}' is not authoritative for this "
                f"request; server '{authoritative_server}' is.",
            )
            raise  # Unreachable but necessary for mypy.

        @IMPORT_reboot_aio_internals_middleware.maybe_run_function_twice_to_validate_effects
        async def _run(
            validating_effects: bool,
        ) -> rbt.std.collections.queue.v1.queue_pb2.DequeueResponse:
            context: IMPORT_typing.Optional[IMPORT_reboot_aio_contexts.Context] = None
            try:
                # rebootdev.aio.contexts.WorkflowContext must be scheduled!
                assert headers.task_schedule is not None
                context, response = await self._schedule_Dequeue(
                    headers=headers,
                    request=request,
                    grpc_context=grpc_context,
                )
                return response

            except IMPORT_reboot_aio_contexts.EffectValidationRetry:
                # Doing effect validation, just let this propagate.
                raise
            except IMPORT_rebootdev.aio.aborted.Aborted as aborted:
                status = IMPORT_rpc_status_sync.to_status(aborted.to_status())
                # Need to add transaction participants here because
                # calling `grpc_context.abort_with_status()` will
                # ignore any other trailing metadata. Only propagate
                # transaction participants metadata if the caller cares.
                # Callers that care are those that are themselves transactions.
                # It's important to not just send this information to everyone;
                # some clients can't tolerate trailers, see:
                #   https://github.com/reboot-dev/mono/issues/5081
                if context is not None and headers.transaction_ids is not None:
                    assert context.transaction_id is not None
                    status = status._replace(
                        trailing_metadata=status.trailing_metadata + context.participants.to_grpc_metadata()
                    )
                await grpc_context.abort_with_status(status)
                raise  # Unreachable but necessary for mypy.
            except IMPORT_asyncio.CancelledError:
                # It's pretty normal for an RPC to be cancelled; it's not useful to
                # print a stack trace.
                raise
            except BaseException as exception:
                # Print the exception stack trace for easier debugging. Note
                # that we don't include the stack trace in an error message
                # for the same reason that gRPC doesn't do so by default,
                # see https://github.com/grpc/grpc/issues/14897, but since this
                # should only get logged on the server side it is safe.
                logger.warning(
                    'Unhandled exception\n' +
                    ''.join(IMPORT_traceback.format_exc() if IMPORT_reboot_nodejs_python.should_print_stacktrace() else [f"{type(exception).__name__}: {exception}"])
                )

                # Re-raise the exception for gRPC to handle!
                #
                # TODO: gRPC will print a stack trace from this
                # exception which we don't want if we're executing via
                # Node.js.
                raise
            finally:
                # Propagate transaction participants, if the caller cares.
                # Callers that care are those that are themselves transactions.
                # It's important to not just send this information to everyone;
                # some clients can't tolerate trailers, see:
                #   https://github.com/reboot-dev/mono/issues/5081
                if context is not None and headers.transaction_ids is not None:
                    assert context.transaction_id is not None
                    grpc_context.set_trailing_metadata(
                        grpc_context.trailing_metadata() +
                        context.participants.to_grpc_metadata()
                    )

        with IMPORT_reboot_aio_tracing.context_from_headers(headers):
            return await _run()

    async def __TryDequeue(
        self,
        context: IMPORT_reboot_aio_contexts.TransactionContext,
        state: rbt.std.collections.queue.v1.queue_pb2.Queue,
        request: rbt.std.collections.queue.v1.queue_pb2.DequeueRequest,
        *,
        validating_effects: bool,
    ) -> rbt.std.collections.queue.v1.queue_pb2.DequeueResponse:
        try:
            typed_state: Queue.State = QueueFromProto(state, is_initial_state=(context.state_id in states_being_constructed))

            response = (
                await self._servicer._TryDequeue(
                    context=context,
                    state=typed_state,
                    request=request
                )
            )


            QueueToProto(typed_state, state)

            IMPORT_reboot_aio_types.assert_type(
                response,
                [rbt.std.collections.queue.v1.queue_pb2.DequeueResponse],
            )
            self.maybe_raise_effect_validation_retry(
                logger=logger,
                idempotency_manager=context,
                method_name='Queue.TryDequeue',
                validating_effects=validating_effects,
                context=context,
            )
            return response
        except IMPORT_reboot_aio_contexts.RetryReactively:
            # Retrying reactively, just let this propagate.
            raise
        except IMPORT_reboot_aio_contexts.EffectValidationRetry:
            # Doing effect validation, just let this propagate.
            raise
        except IMPORT_rebootdev.aio.aborted.Aborted as aborted:
            # If the caller aborted due to a retryable error, just
            # propagate the aborted instead of propagating `Unknown`
            # so that a client can transparently retry.
            if IMPORT_rebootdev.aio.aborted.is_retryable(aborted):
                raise aborted
            # Log any _unhandled_ abort stack traces to make it
            # easier for debugging.
            #
            # NOTE: we don't log if we're a task as it will be logged
            # in `public/rebootdev/aio/internals/tasks_dispatcher.py` instead.
            aborted_type: IMPORT_typing.Optional[type] = None
            aborted_type = Queue.TryDequeueAborted
            if isinstance(aborted, IMPORT_rebootdev.aio.aborted.SystemAborted):
                # Not logging when within `node` as we already log there.
                if IMPORT_reboot_nodejs_python.should_print_stacktrace():
                    logger.warning(
                        f"Unhandled (in 'rbt.std.collections.queue.v1.Queue.TryDequeue') {aborted}; propagating as 'Unknown'\n" +
                        ''.join(IMPORT_traceback.format_exception(aborted))
                    )
                raise IMPORT_rebootdev.aio.aborted.SystemAborted(
                    IMPORT_rbt_v1alpha1.errors_pb2.Unknown(),
                    # TODO(benh): consider whether or not we want to
                    # include the 'package.service.method' which may
                    # get concatenated together forming a kind of
                    # "stack trace"; while it's super helpful for
                    # debugging, it does expose implementation
                    # information.
                    message=f"unhandled (in 'rbt.std.collections.queue.v1.Queue.TryDequeue') {aborted}"
                )
            else:
                if (
                    aborted_type is not None and
                    not isinstance(aborted, aborted_type) and
                    aborted_type.is_declared_error(aborted.error)
                ):
                    # We propagate declared errors that might have
                    # come from another call, i.e., we might have an
                    # `Aborted` but not for this method but the
                    # `Aborted` that we have has an error that this
                    # method declared. This allows a developer to
                    # simply add the declared error to their `.proto`
                    # file rather than having to catch and re-raise
                    # the error with their own aborted type.
                    if context.task is None:
                        logger.warning(
                            f"Propagating unhandled but declared error (in 'rbt.std.collections.queue.v1.Queue.TryDequeue') {aborted}"
                        )
                elif (
                    aborted_type is None or
                    not isinstance(aborted, aborted_type)
                ):
                    # Not logging when within `node` as we already log there.
                    if IMPORT_reboot_nodejs_python.should_print_stacktrace():
                        logger.warning(
                            f"Unhandled (in 'rbt.std.collections.queue.v1.Queue.TryDequeue') {aborted}; propagating as 'Unknown'\n" +
                            ''.join(IMPORT_traceback.format_exception(aborted))
                        )
                    # If this wasn't a declared error than we
                    # propagate it as `Unknown`.
                    raise IMPORT_rebootdev.aio.aborted.SystemAborted(
                        IMPORT_rbt_v1alpha1.errors_pb2.Unknown(),
                        # TODO(benh): consider whether or not we want to
                        # include the 'package.service.method' which may
                        # get concatenated together forming a kind of
                        # "stack trace"; while it's super helpful for
                        # debugging, it does expose implementation
                        # information.
                        message=f"unhandled (in 'rbt.std.collections.queue.v1.Queue.TryDequeue') {aborted}"
                    )

            raise
        except IMPORT_asyncio.CancelledError:
            # It's pretty normal for an RPC to be cancelled; it's not useful to
            # print a stack trace.
            raise
        except IMPORT_google_protobuf_message.DecodeError as decode_error:
            # We usually see this error when we are trying to construct a proto
            # message which is too deeply nested: protobuf has a limit of 100
            # nested messages. See the limits here:
            #   https://protobuf.dev/programming-guides/proto-limits/

            if IMPORT_reboot_nodejs_python.should_print_stacktrace():
                logger.warning(
                    "Unhandled (in 'rbt.std.collections.queue.v1.Queue.TryDequeue') "
                    f"{type(decode_error).__name__}{': ' + str(decode_error) if len(str(decode_error)) > 0 else ''}; "
                    "This is usually caused by a deeply nested protobuf message, which is not supported by protobuf.\n"
                    "See the limits here: https://protobuf.dev/programming-guides/proto-limits/" +
                    ''.join(IMPORT_traceback.format_exception(decode_error))
                )
            raise IMPORT_rebootdev.aio.aborted.SystemAborted(
                IMPORT_rbt_v1alpha1.errors_pb2.Unknown(),
                message=f"unhandled (in 'rbt.std.collections.queue.v1.Queue.TryDequeue') {decode_error}; "
                        "This is usually caused by a deeply nested protobuf message, which is not supported by protobuf.\n"
                        "See the limits here: https://protobuf.dev/programming-guides/proto-limits/"
            )
        except BaseException as exception:
            # Not logging when within `node` as we already log there.
            if IMPORT_reboot_nodejs_python.should_print_stacktrace():
                logger.warning(
                    "Unhandled (in 'rbt.std.collections.queue.v1.Queue.TryDequeue') "
                    f"{type(exception).__name__}{': ' + str(exception) if len(str(exception)) > 0 else ''}; "
                    "propagating as 'Unknown'\n" +
                    ''.join(IMPORT_traceback.format_exception(exception))
                )
            raise IMPORT_rebootdev.aio.aborted.SystemAborted(
                IMPORT_rbt_v1alpha1.errors_pb2.Unknown(),
                # TODO(benh): consider whether or not we want to
                # include the 'package.service.method' which may
                # get concatenated together forming a kind of
                # "stack trace"; while it's super helpful for
                # debugging, it does expose implementation
                # information.
                message=f"unhandled (in 'rbt.std.collections.queue.v1.Queue.TryDequeue') {type(exception).__name__}: {exception}"
            )
        finally:
            pass

    @IMPORT_reboot_aio_tracing.function_span(
        # We expect an `EffectValidationRetry` exception; that's not an error.
        set_status_on_exception=False
    )
    async def _TryDequeue(
        self,
        request: rbt.std.collections.queue.v1.queue_pb2.DequeueRequest,
        context: IMPORT_reboot_aio_contexts.TransactionContext,
        *,
        validating_effects: bool,
        grpc_context: IMPORT_typing.Optional[IMPORT_grpc.aio.ServicerContext] = None,
    ) -> rbt.std.collections.queue.v1.queue_pb2.DequeueResponse:
        # Try to verify the token if a token verifier exists.
        context.auth = await self._maybe_verify_token(
            headers=context._headers, method='TryDequeue'
        )

        # Check if we already have performed this mutation!
        #
        # We do this _before_ calling 'transactionally()' because
        # if this call is for a transaction method _and_ we've
        # already performed the transaction then we don't want to
        # become a transaction participant (again) we just want to
        # return the transaction's response.
        idempotent_mutation = await self._state_manager.check_for_idempotent_mutation(
            context
        )

        if idempotent_mutation is not None:
            response = rbt.std.collections.queue.v1.queue_pb2.DequeueResponse()
            response.ParseFromString(idempotent_mutation.response)
            return response

        async with self._state_manager.transactionally(
            context,
            self.tasks_dispatcher,
            aborted_type=Queue.TryDequeueAborted,
        ) as transaction:
            if transaction is not None:
                context.participants.add(
                    self._servicer.__state_type_name__, context._state_ref
                )
            assert transaction is not None
            async with self._state_manager.transaction(
                context,
                self._servicer.__state_type__,
                transaction,
                authorize=self._maybe_authorize(
                    method_name='rbt.std.collections.queue.v1.QueueMethods.TryDequeue',
                    headers=context._headers,
                    auth=context.auth,
                    request=request,
                ),
                from_constructor=False,
                requires_constructor=False
            ) as (state, complete):

                response = await self.__TryDequeue(
                    context,
                    state,
                    request,
                    validating_effects=validating_effects,
                )

                await complete(
                    IMPORT_reboot_aio_state_managers.Effects(
                        state=state,
                        response=response,
                    )
                )
                return response

    async def _schedule_TryDequeue(
        self,
        *,
        request: rbt.std.collections.queue.v1.queue_pb2.DequeueRequest,
        headers: IMPORT_reboot_aio_headers.Headers,
        grpc_context: IMPORT_grpc.aio.ServicerContext,
    ) -> tuple[IMPORT_reboot_aio_contexts.WriterContext, rbt.std.collections.queue.v1.queue_pb2.DequeueResponse]:
        context: IMPORT_reboot_aio_contexts.WriterContext = self.create_context(
            headers=headers,
            state_type_name = IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue'),
            method='TryDequeue',
            context_type=IMPORT_reboot_aio_contexts.WriterContext,
        )
        response = rbt.std.collections.queue.v1.queue_pb2.DequeueResponse()

        # Check if we already have performed this schedule! Note that
        # we need to do this for all kinds of methods because this is
        # effectively a mutation (actually a `writer`, see below).
        #
        # We do this _before_ calling 'transactionally()' because
        # if this call is for a transaction method _and_ we've
        # already performed the transaction then we don't want to
        # become a transaction participant (again) we just want to
        # return the transaction's response.
        idempotent_mutation = await self._state_manager.check_for_idempotent_mutation(
            context
        )

        if idempotent_mutation is not None:
            response.ParseFromString(idempotent_mutation.response)

            # We should have only scheduled a single task!
            assert len(idempotent_mutation.task_ids) == 1
            assert grpc_context is not None
            grpc_context.set_trailing_metadata(
                grpc_context.trailing_metadata() +
                (
                    (
                        IMPORT_reboot_aio_headers.TASK_ID_UUID,
                        str(IMPORT_uuid.UUID(bytes=idempotent_mutation.task_ids[0].task_uuid))
                    ),
                )
            )

            return context, response

        async with self._state_manager.transactionally(
            context,
            self.tasks_dispatcher,
            aborted_type=Queue.TryDequeueAborted,
        ) as transaction:
            if transaction is not None:
                context.participants.add(
                    self._servicer.__state_type_name__, context._state_ref
                )

            # Try to verify the token if a token verifier exists.
            context.auth = await self._maybe_verify_token(
                headers=headers, method='TryDequeue'
            )

            async with self._state_manager.writer(
                context,
                self._servicer.__state_type__,
                self.tasks_dispatcher,
                transaction=transaction,
                authorize=self._maybe_authorize(
                    method_name='rbt.std.collections.queue.v1.QueueMethods.TryDequeue',
                    headers=context._headers,
                    auth=context.auth,
                    request=request,
                ),
                from_constructor=False,
                requires_constructor=False
            ) as (state, writer):

                task = await QueueServicerTasks(
                    context=context,
                    state_ref=context._state_ref,
                ).TryDequeue(
                    QueueTryDequeueRequestFromProto(request),
                    schedule=context._headers.task_schedule,
                )

                effects = IMPORT_reboot_aio_state_managers.Effects(
                    response=response,
                    state=state,
                    tasks=[task],
                )

                assert effects.tasks is not None

                await writer.complete(effects)

                assert grpc_context is not None

                grpc_context.set_trailing_metadata(
                    grpc_context.trailing_metadata() +
                    (
                        (
                            IMPORT_reboot_aio_headers.TASK_ID_UUID,
                            str(IMPORT_uuid.UUID(bytes=task.task_id.task_uuid))
                        ),
                    )
                )

                return context, response

        return context, response


    # Entrypoint for non-reactive network calls (i.e. typical gRPC calls).
    async def TryDequeue(
        self,
        request: rbt.std.collections.queue.v1.queue_pb2.DequeueRequest,
        grpc_context: IMPORT_grpc.aio.ServicerContext,
    ) -> rbt.std.collections.queue.v1.queue_pb2.DequeueResponse:
        headers = IMPORT_reboot_aio_headers.Headers.from_grpc_context(grpc_context)
        assert headers.application_id is not None  # Guaranteed by `Headers`.

        # Confirm whether this is the right server to be serving this
        # request.
        authoritative_server = self.placement_client.server_for_actor(
            headers.application_id,
            headers.state_ref,
        )
        if authoritative_server != self.server_id:
            # This is NOT the correct server. Fail.
            await grpc_context.abort(
                IMPORT_grpc.StatusCode.UNAVAILABLE,
                f"Server '{self.server_id}' is not authoritative for this "
                f"request; server '{authoritative_server}' is.",
            )
            raise  # Unreachable but necessary for mypy.

        @IMPORT_reboot_aio_internals_middleware.maybe_run_function_twice_to_validate_effects
        async def _run(
            validating_effects: bool,
        ) -> rbt.std.collections.queue.v1.queue_pb2.DequeueResponse:
            context: IMPORT_typing.Optional[IMPORT_reboot_aio_contexts.Context] = None
            try:
                if headers.task_schedule is not None:
                    context, response = await self._schedule_TryDequeue(
                        headers=headers,
                        request=request,
                        grpc_context=grpc_context,
                    )
                    return response

                context = self.create_context(
                    headers=headers,
                    state_type_name = IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue'),
                    method='TryDequeue',
                    context_type=IMPORT_reboot_aio_contexts.TransactionContext,
                )
                assert context is not None

                return await self._TryDequeue(
                    request,
                    context,
                    validating_effects=validating_effects,
                    grpc_context=grpc_context,
                )
            except IMPORT_reboot_aio_contexts.EffectValidationRetry:
                # Doing effect validation, just let this propagate.
                raise
            except IMPORT_rebootdev.aio.aborted.Aborted as aborted:
                status = IMPORT_rpc_status_sync.to_status(aborted.to_status())
                # Need to add transaction participants here because
                # calling `grpc_context.abort_with_status()` will
                # ignore any other trailing metadata. Only propagate
                # transaction participants metadata if the caller cares.
                # Callers that care are those that are themselves transactions.
                # It's important to not just send this information to everyone;
                # some clients can't tolerate trailers, see:
                #   https://github.com/reboot-dev/mono/issues/5081
                if context is not None and headers.transaction_ids is not None:
                    assert context.transaction_id is not None
                    status = status._replace(
                        trailing_metadata=status.trailing_metadata + context.participants.to_grpc_metadata()
                    )
                await grpc_context.abort_with_status(status)
                raise  # Unreachable but necessary for mypy.
            except IMPORT_asyncio.CancelledError:
                # It's pretty normal for an RPC to be cancelled; it's not useful to
                # print a stack trace.
                raise
            except BaseException as exception:
                # Print the exception stack trace for easier debugging. Note
                # that we don't include the stack trace in an error message
                # for the same reason that gRPC doesn't do so by default,
                # see https://github.com/grpc/grpc/issues/14897, but since this
                # should only get logged on the server side it is safe.
                logger.warning(
                    'Unhandled exception\n' +
                    ''.join(IMPORT_traceback.format_exc() if IMPORT_reboot_nodejs_python.should_print_stacktrace() else [f"{type(exception).__name__}: {exception}"])
                )

                # Re-raise the exception for gRPC to handle!
                #
                # TODO: gRPC will print a stack trace from this
                # exception which we don't want if we're executing via
                # Node.js.
                raise
            finally:
                # Propagate transaction participants, if the caller cares.
                # Callers that care are those that are themselves transactions.
                # It's important to not just send this information to everyone;
                # some clients can't tolerate trailers, see:
                #   https://github.com/reboot-dev/mono/issues/5081
                if context is not None and headers.transaction_ids is not None:
                    assert context.transaction_id is not None
                    grpc_context.set_trailing_metadata(
                        grpc_context.trailing_metadata() +
                        context.participants.to_grpc_metadata()
                    )

        with IMPORT_reboot_aio_tracing.context_from_headers(headers):
            return await _run()

    async def __Empty(
        self,
        context: IMPORT_reboot_aio_contexts.ReaderContext,
        state: rbt.std.collections.queue.v1.queue_pb2.Queue,
        request: rbt.std.collections.queue.v1.queue_pb2.EmptyRequest,
        *,
        validating_effects: bool,
    ) -> rbt.std.collections.queue.v1.queue_pb2.EmptyResponse:
        try:
            typed_state: Queue.State = QueueFromProto(state, is_initial_state=(context.state_id in states_being_constructed))

            response = (
                await self._servicer._Empty(
                    context=context,
                    state=typed_state,
                    request=request
                )
            )


            QueueToProto(typed_state, state)

            IMPORT_reboot_aio_types.assert_type(
                response,
                [rbt.std.collections.queue.v1.queue_pb2.EmptyResponse],
            )
            self.maybe_raise_effect_validation_retry(
                logger=logger,
                idempotency_manager=context,
                method_name='Queue.Empty',
                validating_effects=validating_effects,
                context=context,
            )
            return response
        except IMPORT_reboot_aio_contexts.RetryReactively:
            # Retrying reactively, just let this propagate.
            raise
        except IMPORT_reboot_aio_contexts.EffectValidationRetry:
            # Doing effect validation, just let this propagate.
            raise
        except IMPORT_rebootdev.aio.aborted.Aborted as aborted:
            # If the caller aborted due to a retryable error, just
            # propagate the aborted instead of propagating `Unknown`
            # so that a client can transparently retry.
            if IMPORT_rebootdev.aio.aborted.is_retryable(aborted):
                raise aborted
            # Log any _unhandled_ abort stack traces to make it
            # easier for debugging.
            #
            # NOTE: we don't log if we're a task as it will be logged
            # in `public/rebootdev/aio/internals/tasks_dispatcher.py` instead.
            aborted_type: IMPORT_typing.Optional[type] = None
            aborted_type = Queue.EmptyAborted
            if isinstance(aborted, IMPORT_rebootdev.aio.aborted.SystemAborted):
                # Not logging when within `node` as we already log there.
                if IMPORT_reboot_nodejs_python.should_print_stacktrace():
                    logger.warning(
                        f"Unhandled (in 'rbt.std.collections.queue.v1.Queue.Empty') {aborted}; propagating as 'Unknown'\n" +
                        ''.join(IMPORT_traceback.format_exception(aborted))
                    )
                raise IMPORT_rebootdev.aio.aborted.SystemAborted(
                    IMPORT_rbt_v1alpha1.errors_pb2.Unknown(),
                    # TODO(benh): consider whether or not we want to
                    # include the 'package.service.method' which may
                    # get concatenated together forming a kind of
                    # "stack trace"; while it's super helpful for
                    # debugging, it does expose implementation
                    # information.
                    message=f"unhandled (in 'rbt.std.collections.queue.v1.Queue.Empty') {aborted}"
                )
            else:
                if (
                    aborted_type is not None and
                    not isinstance(aborted, aborted_type) and
                    aborted_type.is_declared_error(aborted.error)
                ):
                    # We propagate declared errors that might have
                    # come from another call, i.e., we might have an
                    # `Aborted` but not for this method but the
                    # `Aborted` that we have has an error that this
                    # method declared. This allows a developer to
                    # simply add the declared error to their `.proto`
                    # file rather than having to catch and re-raise
                    # the error with their own aborted type.
                    if context.task is None:
                        logger.warning(
                            f"Propagating unhandled but declared error (in 'rbt.std.collections.queue.v1.Queue.Empty') {aborted}"
                        )
                elif (
                    aborted_type is None or
                    not isinstance(aborted, aborted_type)
                ):
                    # Not logging when within `node` as we already log there.
                    if IMPORT_reboot_nodejs_python.should_print_stacktrace():
                        logger.warning(
                            f"Unhandled (in 'rbt.std.collections.queue.v1.Queue.Empty') {aborted}; propagating as 'Unknown'\n" +
                            ''.join(IMPORT_traceback.format_exception(aborted))
                        )
                    # If this wasn't a declared error than we
                    # propagate it as `Unknown`.
                    raise IMPORT_rebootdev.aio.aborted.SystemAborted(
                        IMPORT_rbt_v1alpha1.errors_pb2.Unknown(),
                        # TODO(benh): consider whether or not we want to
                        # include the 'package.service.method' which may
                        # get concatenated together forming a kind of
                        # "stack trace"; while it's super helpful for
                        # debugging, it does expose implementation
                        # information.
                        message=f"unhandled (in 'rbt.std.collections.queue.v1.Queue.Empty') {aborted}"
                    )

            raise
        except IMPORT_asyncio.CancelledError:
            # It's pretty normal for an RPC to be cancelled; it's not useful to
            # print a stack trace.
            raise
        except IMPORT_google_protobuf_message.DecodeError as decode_error:
            # We usually see this error when we are trying to construct a proto
            # message which is too deeply nested: protobuf has a limit of 100
            # nested messages. See the limits here:
            #   https://protobuf.dev/programming-guides/proto-limits/

            if IMPORT_reboot_nodejs_python.should_print_stacktrace():
                logger.warning(
                    "Unhandled (in 'rbt.std.collections.queue.v1.Queue.Empty') "
                    f"{type(decode_error).__name__}{': ' + str(decode_error) if len(str(decode_error)) > 0 else ''}; "
                    "This is usually caused by a deeply nested protobuf message, which is not supported by protobuf.\n"
                    "See the limits here: https://protobuf.dev/programming-guides/proto-limits/" +
                    ''.join(IMPORT_traceback.format_exception(decode_error))
                )
            raise IMPORT_rebootdev.aio.aborted.SystemAborted(
                IMPORT_rbt_v1alpha1.errors_pb2.Unknown(),
                message=f"unhandled (in 'rbt.std.collections.queue.v1.Queue.Empty') {decode_error}; "
                        "This is usually caused by a deeply nested protobuf message, which is not supported by protobuf.\n"
                        "See the limits here: https://protobuf.dev/programming-guides/proto-limits/"
            )
        except BaseException as exception:
            # Not logging when within `node` as we already log there.
            if IMPORT_reboot_nodejs_python.should_print_stacktrace():
                logger.warning(
                    "Unhandled (in 'rbt.std.collections.queue.v1.Queue.Empty') "
                    f"{type(exception).__name__}{': ' + str(exception) if len(str(exception)) > 0 else ''}; "
                    "propagating as 'Unknown'\n" +
                    ''.join(IMPORT_traceback.format_exception(exception))
                )
            raise IMPORT_rebootdev.aio.aborted.SystemAborted(
                IMPORT_rbt_v1alpha1.errors_pb2.Unknown(),
                # TODO(benh): consider whether or not we want to
                # include the 'package.service.method' which may
                # get concatenated together forming a kind of
                # "stack trace"; while it's super helpful for
                # debugging, it does expose implementation
                # information.
                message=f"unhandled (in 'rbt.std.collections.queue.v1.Queue.Empty') {type(exception).__name__}: {exception}"
            )
        finally:
            pass

    @IMPORT_reboot_aio_tracing.function_span(
        # We expect an `EffectValidationRetry` exception; that's not an error.
        set_status_on_exception=False
    )
    async def _Empty(
        self,
        request: rbt.std.collections.queue.v1.queue_pb2.EmptyRequest,
        context: IMPORT_reboot_aio_contexts.ReaderContext,
        *,
        validating_effects: bool,
        grpc_context: IMPORT_typing.Optional[IMPORT_grpc.aio.ServicerContext] = None,
    ) -> rbt.std.collections.queue.v1.queue_pb2.EmptyResponse:
        # Try to verify the token if a token verifier exists.
        context.auth = await self._maybe_verify_token(
            headers=context._headers, method='Empty'
        )


        async with self._state_manager.transactionally(
            context,
            self.tasks_dispatcher,
            aborted_type=Queue.EmptyAborted,
        ) as transaction:
            if transaction is not None:
                context.participants.add(
                    self._servicer.__state_type_name__, context._state_ref
                )
            authorizer = self._maybe_authorize(
                method_name='rbt.std.collections.queue.v1.QueueMethods.Empty',
                headers=context._headers,
                auth=context.auth,
                request=request,
            )
            async with self._state_manager.reader(
                context,
                self._servicer.__state_type__,
                authorize=authorizer,
            ) as state:
                response = await self.__Empty(
                    context,
                    state,
                    request,
                    validating_effects=validating_effects,
                )
                return response

    async def _schedule_Empty(
        self,
        *,
        request: rbt.std.collections.queue.v1.queue_pb2.EmptyRequest,
        headers: IMPORT_reboot_aio_headers.Headers,
        grpc_context: IMPORT_grpc.aio.ServicerContext,
    ) -> tuple[IMPORT_reboot_aio_contexts.WriterContext, rbt.std.collections.queue.v1.queue_pb2.EmptyResponse]:
        context: IMPORT_reboot_aio_contexts.WriterContext = self.create_context(
            headers=headers,
            state_type_name = IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue'),
            method='Empty',
            context_type=IMPORT_reboot_aio_contexts.WriterContext,
        )
        response = rbt.std.collections.queue.v1.queue_pb2.EmptyResponse()

        # Check if we already have performed this schedule! Note that
        # we need to do this for all kinds of methods because this is
        # effectively a mutation (actually a `writer`, see below).
        #
        # We do this _before_ calling 'transactionally()' because
        # if this call is for a transaction method _and_ we've
        # already performed the transaction then we don't want to
        # become a transaction participant (again) we just want to
        # return the transaction's response.
        idempotent_mutation = await self._state_manager.check_for_idempotent_mutation(
            context
        )

        if idempotent_mutation is not None:
            response.ParseFromString(idempotent_mutation.response)

            # We should have only scheduled a single task!
            assert len(idempotent_mutation.task_ids) == 1
            assert grpc_context is not None
            grpc_context.set_trailing_metadata(
                grpc_context.trailing_metadata() +
                (
                    (
                        IMPORT_reboot_aio_headers.TASK_ID_UUID,
                        str(IMPORT_uuid.UUID(bytes=idempotent_mutation.task_ids[0].task_uuid))
                    ),
                )
            )

            return context, response

        async with self._state_manager.transactionally(
            context,
            self.tasks_dispatcher,
            aborted_type=Queue.EmptyAborted,
        ) as transaction:
            if transaction is not None:
                context.participants.add(
                    self._servicer.__state_type_name__, context._state_ref
                )

            # Try to verify the token if a token verifier exists.
            context.auth = await self._maybe_verify_token(
                headers=headers, method='Empty'
            )

            async with self._state_manager.writer(
                context,
                self._servicer.__state_type__,
                self.tasks_dispatcher,
                transaction=transaction,
                authorize=self._maybe_authorize(
                    method_name='rbt.std.collections.queue.v1.QueueMethods.Empty',
                    headers=context._headers,
                    auth=context.auth,
                    request=request,
                ),
                from_constructor=False,
                requires_constructor=False
            ) as (state, writer):

                task = await QueueServicerTasks(
                    context=context,
                    state_ref=context._state_ref,
                ).Empty(
                    QueueEmptyRequestFromProto(request),
                    schedule=context._headers.task_schedule,
                )

                effects = IMPORT_reboot_aio_state_managers.Effects(
                    response=response,
                    state=state,
                    tasks=[task],
                )

                assert effects.tasks is not None

                await writer.complete(effects)

                assert grpc_context is not None

                grpc_context.set_trailing_metadata(
                    grpc_context.trailing_metadata() +
                    (
                        (
                            IMPORT_reboot_aio_headers.TASK_ID_UUID,
                            str(IMPORT_uuid.UUID(bytes=task.task_id.task_uuid))
                        ),
                    )
                )

                return context, response

        return context, response


    # Entrypoint for non-reactive network calls (i.e. typical gRPC calls).
    async def Empty(
        self,
        request: rbt.std.collections.queue.v1.queue_pb2.EmptyRequest,
        grpc_context: IMPORT_grpc.aio.ServicerContext,
    ) -> rbt.std.collections.queue.v1.queue_pb2.EmptyResponse:
        headers = IMPORT_reboot_aio_headers.Headers.from_grpc_context(grpc_context)
        assert headers.application_id is not None  # Guaranteed by `Headers`.

        # Confirm whether this is the right server to be serving this
        # request.
        authoritative_server = self.placement_client.server_for_actor(
            headers.application_id,
            headers.state_ref,
        )
        if authoritative_server != self.server_id:
            # This is NOT the correct server. Fail.
            await grpc_context.abort(
                IMPORT_grpc.StatusCode.UNAVAILABLE,
                f"Server '{self.server_id}' is not authoritative for this "
                f"request; server '{authoritative_server}' is.",
            )
            raise  # Unreachable but necessary for mypy.

        @IMPORT_reboot_aio_internals_middleware.maybe_run_function_twice_to_validate_effects
        async def _run(
            validating_effects: bool,
        ) -> rbt.std.collections.queue.v1.queue_pb2.EmptyResponse:
            context: IMPORT_typing.Optional[IMPORT_reboot_aio_contexts.Context] = None
            try:
                if headers.task_schedule is not None:
                    context, response = await self._schedule_Empty(
                        headers=headers,
                        request=request,
                        grpc_context=grpc_context,
                    )
                    return response

                context = self.create_context(
                    headers=headers,
                    state_type_name = IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue'),
                    method='Empty',
                    context_type=IMPORT_reboot_aio_contexts.ReaderContext,
                )
                assert context is not None

                return await self._Empty(
                    request,
                    context,
                    validating_effects=validating_effects,
                    grpc_context=grpc_context,
                )
            except IMPORT_reboot_aio_contexts.EffectValidationRetry:
                # Doing effect validation, just let this propagate.
                raise
            except IMPORT_rebootdev.aio.aborted.Aborted as aborted:
                status = IMPORT_rpc_status_sync.to_status(aborted.to_status())
                # Need to add transaction participants here because
                # calling `grpc_context.abort_with_status()` will
                # ignore any other trailing metadata. Only propagate
                # transaction participants metadata if the caller cares.
                # Callers that care are those that are themselves transactions.
                # It's important to not just send this information to everyone;
                # some clients can't tolerate trailers, see:
                #   https://github.com/reboot-dev/mono/issues/5081
                if context is not None and headers.transaction_ids is not None:
                    assert context.transaction_id is not None
                    status = status._replace(
                        trailing_metadata=status.trailing_metadata + context.participants.to_grpc_metadata()
                    )
                await grpc_context.abort_with_status(status)
                raise  # Unreachable but necessary for mypy.
            except IMPORT_asyncio.CancelledError:
                # It's pretty normal for an RPC to be cancelled; it's not useful to
                # print a stack trace.
                raise
            except BaseException as exception:
                # Print the exception stack trace for easier debugging. Note
                # that we don't include the stack trace in an error message
                # for the same reason that gRPC doesn't do so by default,
                # see https://github.com/grpc/grpc/issues/14897, but since this
                # should only get logged on the server side it is safe.
                logger.warning(
                    'Unhandled exception\n' +
                    ''.join(IMPORT_traceback.format_exc() if IMPORT_reboot_nodejs_python.should_print_stacktrace() else [f"{type(exception).__name__}: {exception}"])
                )

                # Re-raise the exception for gRPC to handle!
                #
                # TODO: gRPC will print a stack trace from this
                # exception which we don't want if we're executing via
                # Node.js.
                raise
            finally:
                # Propagate transaction participants, if the caller cares.
                # Callers that care are those that are themselves transactions.
                # It's important to not just send this information to everyone;
                # some clients can't tolerate trailers, see:
                #   https://github.com/reboot-dev/mono/issues/5081
                if context is not None and headers.transaction_ids is not None:
                    assert context.transaction_id is not None
                    grpc_context.set_trailing_metadata(
                        grpc_context.trailing_metadata() +
                        context.participants.to_grpc_metadata()
                    )

        with IMPORT_reboot_aio_tracing.context_from_headers(headers):
            return await _run()

    def _maybe_authorize(
        self,
        *,
        method_name: str,
        headers: IMPORT_reboot_aio_headers.Headers,
        auth: IMPORT_typing.Optional[IMPORT_rebootdev.aio.auth.Auth],
        request: IMPORT_typing.Optional[QueueRequestTypes] = None,
    ) -> IMPORT_typing.Optional[IMPORT_typing.Callable[[IMPORT_typing.Optional[QueueStateType]], IMPORT_typing.Awaitable[None]]]:
        """Returns a function to check authorization for the given method.

        Raises `PermissionDenied` in case Authorizer is present but the request
        is not authorized.
        """
        # To authorize internal calls, we use an internal magic token.
        if headers.bearer_token == __internal_magic_token__:
            return None

        assert self._authorizer is not None

        async def authorize(state: IMPORT_typing.Optional[QueueStateType]) -> None:
            # Create context for the authorizer. This is a `ReaderContext`
            # independently of the calling context.
            with self.use_context(
                headers=(
                    # Get headers suitable for doing authorization.
                    headers.copy_for_token_verification_and_authorization()
                ),
                state_type_name = IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue'),
                method=method_name,
                context_type=IMPORT_reboot_aio_contexts.ReaderContext,
            ) as context:
                context.auth = auth

                # Get the authorizer decision.
                authorization_decision = await self._authorizer.authorize(
                    method_name=method_name,
                    context=context,
                    state=state,
                    request=request,
                )

            # Enforce correct authorizer decision type.
            try:
                IMPORT_reboot_aio_types.assert_type(
                    authorization_decision,
                    [
                        IMPORT_rbt_v1alpha1.errors_pb2.Ok,
                        IMPORT_rbt_v1alpha1.errors_pb2.Unauthenticated,
                        IMPORT_rbt_v1alpha1.errors_pb2.PermissionDenied,
                    ]
                )
            except TypeError as e:
                # Retyping.cast the exception to provide more context.
                authorizer_type = f"{type(self._authorizer).__module__}.{type(self._authorizer).__name__}"
                raise TypeError(
                    f"Authorizer '{authorizer_type}' "
                    f"returned unexpected type '{type(authorization_decision).__name__}' "
                    f"for method '{method_name}' on "
                    f"`rbt.std.collections.queue.v1.Queue('{headers.state_ref.id}')`"
                ) from e

            # If the decision is not `True`, raise a `SystemAborted` with either a
            # `PermissionDenied` error (in case of `False`) or an `Unauthenticated`
            # error.
            if not isinstance(authorization_decision, IMPORT_rbt_v1alpha1.errors_pb2.Ok):
                if isinstance(authorization_decision, IMPORT_rbt_v1alpha1.errors_pb2.Unauthenticated):
                    logger.warning(
                        f"Unauthenticated call to '{method_name}' on "
                        f"`rbt.std.collections.queue.v1.Queue('{headers.state_ref.id}')`"
                    )

                raise IMPORT_rebootdev.aio.aborted.SystemAborted(
                    authorization_decision,
                    message=
                    f"You are not authorized to call '{method_name}' on "
                    f"`rbt.std.collections.queue.v1.Queue('{headers.state_ref.id}')`"
                )

        return authorize

    async def _maybe_verify_token(
        self,
        *,
        headers: IMPORT_reboot_aio_headers.Headers,
        method: str,
    ) -> IMPORT_typing.Optional[IMPORT_rebootdev.aio.auth.Auth]:
        """Verify the bearer token and if a token verifier is present.

        Returns the (optional) `rebootdev.aio.auth.Auth` object
        produced by the token verifier if the token can be verified.
        """
        if self._token_verifier is not None:
            if headers.bearer_token == __internal_magic_token__:
                return None

            with self.use_context(
                headers=(
                    # Get headers suitable for doing token verification.
                    headers.copy_for_token_verification_and_authorization()
                ),
                state_type_name = IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue'),
                method=method,
                context_type=IMPORT_reboot_aio_contexts.ReaderContext,
            ) as context:
                return await self._token_verifier.verify_token(
                    context=context,
                    token=headers.bearer_token,
                )

        return None


############################ Client Stubs ############################
# This section is relevant for clients accessing a Reboot service. Since
# servicers are themselves often clients also, this code is generated for
# them also.


class _QueueStub(IMPORT_reboot_aio_stubs.Stub):

    __state_type_name__ = IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue')

    def __init__(
        self,
        *,
        context: IMPORT_reboot_aio_contexts.Context | IMPORT_reboot_aio_external.ExternalContext,
        state_ref: IMPORT_reboot_aio_types.StateRef,
        bearer_token: IMPORT_typing.Optional[str] = None,
    ):
        # Within a Reboot context we do not pass on the caller's bearer token, as that might
        # have security implications - we cannot simply trust any service we are calling with
        # the user's credentials. Instead, the developer can rely on the default app-internal
        # auth, or override that and set an explicit bearer token.
        #
        # In the case of `ExternalContext`, however, its `bearer_token` was set specifically
        # by the developer for the purpose of making these calls.
        caller_id: IMPORT_typing.Optional[IMPORT_reboot_aio_caller_id.CallerID] = None
        if isinstance(context, IMPORT_reboot_aio_external.ExternalContext):
            # Note that only `ExternalContext` even has a `bearer_token` field.
            bearer_token = context.bearer_token
            # If the creator of the `ExternalContext` set an explicit caller ID, obey it.
            caller_id = context.caller_id
        else:
            caller_id = IMPORT_reboot_aio_caller_id.CallerID(
                application_id=context.application_id,
            )

        super().__init__(
            channel_manager=context.channel_manager,
            idempotency_manager=context,
            state_ref=state_ref,
            context=context if isinstance(context, IMPORT_reboot_aio_contexts.Context) else None,
            bearer_token=bearer_token,
            caller_id=caller_id,
        )

        # All the channels for all services of this state will go to the same
        # place, so we can just get a single channel and share it across all
        # stubs.
        channel = self._channel_manager.get_channel_to_state(
            self.__state_type_name__, state_ref
        )
        self._rbt_std_collections_queue_v1_queuemethods_stub = rbt.std.collections.queue.v1.queue_pb2_grpc.QueueMethodsStub(channel)


class QueueReaderStub(_QueueStub):

    def __init__(
        self,
        context: IMPORT_reboot_aio_contexts.ReaderContext | IMPORT_reboot_aio_contexts.WriterContext | IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
        *,
        state_ref: IMPORT_reboot_aio_types.StateRef,
        bearer_token: IMPORT_typing.Optional[str] = None,
    ):
        IMPORT_reboot_aio_types.assert_type(context, [IMPORT_reboot_aio_contexts.ReaderContext, IMPORT_reboot_aio_contexts.WriterContext, IMPORT_reboot_aio_contexts.TransactionContext, IMPORT_reboot_aio_contexts.WorkflowContext, IMPORT_reboot_aio_external.ExternalContext])
        super().__init__(
            context=context,
            state_ref=state_ref,
            bearer_token=bearer_token,
        )

    # Queue specific methods:



    async def Empty(
        self,
        request: Queue.EmptyRequest,
        *,
        metadata: IMPORT_typing.Optional[IMPORT_reboot_aio_types.GrpcMetadata] = None,
        bearer_token: IMPORT_typing.Optional[str] = None,
        idempotency: IMPORT_typing.Optional[IMPORT_reboot_aio_idempotency.Idempotency] = None,
    ) -> rbt.std.collections.queue.v1.queue_pb2.EmptyResponse:
        state_type_name = IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue')
        service_name = IMPORT_reboot_aio_types.ServiceName('rbt.std.collections.queue.v1.QueueMethods')
        method = 'Empty'

        proto_request = QueueEmptyRequestToProto(
            request,
        )

        async def call():
            async with self._call(
                state_type_name,
                service_name,
                method,
                self._rbt_std_collections_queue_v1_queuemethods_stub.Empty,
                proto_request,
                unary=True,
                reader=True,
                response_type=rbt.std.collections.queue.v1.queue_pb2.EmptyResponse,
                aborted_type=Queue.EmptyAborted,
                metadata=metadata,
                bearer_token=bearer_token,
            ) as call:
                assert isinstance(call, IMPORT_typing.Awaitable)
                return await call

        if isinstance(self._context, IMPORT_reboot_aio_contexts.WorkflowContext):
            # Use the idempotency manager to make sure that this
            # reader is being called following the rules.
            with self._context.idempotently(
                state_type_name=state_type_name,
                state_ref=self._headers.state_ref,
                service_name=service_name,
                method=method,
                mutation=False,
                request=proto_request,
                metadata=metadata,
                idempotency=idempotency,
                # Only need to pass `aborted_type` for mutations.
                aborted_type=None,
            ) as idempotency_key:
                assert idempotency is not None
                # Check if this reader is from an `.always()` and if
                # so, don't memoize!
                if idempotency.always:
                    return await call()

                assert idempotency_key is not None
                return await IMPORT_reboot_aio_workflows.at_least_once(
                    (
                        # TODO: for easier debugging include the
                        # original alias (or generated alias in the
                        # case of `.per_iteration()` w/o an alias)
                        # instead of just `idempotency_key`.
                        f'{ service_name }.{ method } ({str(idempotency_key)})',
                        # NOTE: we want this to be `PER_WORKFLOW`
                        # because any per iteration concerns should
                        # have already been taken care of by caller
                        # using `.per_iteration()`.
                        IMPORT_reboot_aio_workflows.PER_WORKFLOW
                    ),
                    self._context,
                    call,
                    type=rbt.std.collections.queue.v1.queue_pb2.EmptyResponse,
                )
        return await call()



class QueueWriterStub(_QueueStub):

    def __init__(
        self,
        context: IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
        *,
        state_ref: IMPORT_reboot_aio_types.StateRef,
        bearer_token: IMPORT_typing.Optional[str] = None,
    ):
        IMPORT_reboot_aio_types.assert_type(context, [IMPORT_reboot_aio_contexts.TransactionContext, IMPORT_reboot_aio_contexts.WorkflowContext, IMPORT_reboot_aio_external.ExternalContext])
        super().__init__(
            context=context,
            state_ref=state_ref,
            bearer_token=bearer_token,
        )

    # Queue specific methods:



    async def Empty(
        self,
        request: Queue.EmptyRequest,
        *,
        metadata: IMPORT_typing.Optional[IMPORT_reboot_aio_types.GrpcMetadata] = None,
        bearer_token: IMPORT_typing.Optional[str] = None,
    ) -> rbt.std.collections.queue.v1.queue_pb2.EmptyResponse:
        async with self._call(
            IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue'),
            IMPORT_reboot_aio_types.ServiceName('rbt.std.collections.queue.v1.QueueMethods'),
            'Empty',
            self._rbt_std_collections_queue_v1_queuemethods_stub.Empty,
            QueueEmptyRequestToProto(
                request,
            ),
            unary=True,
            reader=True,
            response_type=rbt.std.collections.queue.v1.queue_pb2.EmptyResponse,
            aborted_type=Queue.EmptyAborted,
            metadata=metadata,
            bearer_token=bearer_token,
        ) as call:
            assert isinstance(call, IMPORT_typing.Awaitable), type(call)
            return await call


class QueueWorkflowStub(_QueueStub):

    def __init__(
        self,
        *,
        context: IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
        state_ref: IMPORT_reboot_aio_types.StateRef,
        bearer_token: IMPORT_typing.Optional[str] = None,
    ):
        IMPORT_reboot_aio_types.assert_type(context, [IMPORT_reboot_aio_contexts.TransactionContext, IMPORT_reboot_aio_contexts.WorkflowContext, IMPORT_reboot_aio_external.ExternalContext])
        super().__init__(
            context=context,
            state_ref=state_ref,
            bearer_token=bearer_token,
        )

    # Queue specific methods:
    async def Enqueue(
        self,
        request: Queue.EnqueueRequest,
        idempotency: IMPORT_typing.Optional[IMPORT_reboot_aio_idempotency.Idempotency] = None,
        *,
        metadata: IMPORT_typing.Optional[IMPORT_reboot_aio_types.GrpcMetadata] = None,
        bearer_token: IMPORT_typing.Optional[str] = None,
    ) -> rbt.std.collections.queue.v1.queue_pb2.EnqueueResponse:
        idempotency_key: IMPORT_typing.Optional[IMPORT_uuid.UUID]
        proto_request = QueueEnqueueRequestToProto(
            request,
        )

        with self._idempotency_manager.idempotently(
            state_type_name=IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue'),
            state_ref=self._headers.state_ref,
            service_name=IMPORT_reboot_aio_types.ServiceName('rbt.std.collections.queue.v1.QueueMethods'),
            method='Enqueue',
            mutation=True,
            request=proto_request,
            metadata=metadata,
            idempotency=idempotency,
            aborted_type=Queue.EnqueueAborted,
        ) as idempotency_key:
            async with self._call(
                IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue'),
                IMPORT_reboot_aio_types.ServiceName('rbt.std.collections.queue.v1.QueueMethods'),
                'Enqueue',
                self._rbt_std_collections_queue_v1_queuemethods_stub.Enqueue,
                proto_request,
                unary=True,
                reader=False,
                response_type=rbt.std.collections.queue.v1.queue_pb2.EnqueueResponse,
                aborted_type=Queue.EnqueueAborted,
                metadata=metadata,
                idempotency_key=idempotency_key,
                bearer_token=bearer_token,
            ) as call:
                assert isinstance(call, IMPORT_typing.Awaitable), type(call)
                return await call


    async def TryDequeue(
        self,
        request: Queue.TryDequeueRequest,
        idempotency: IMPORT_typing.Optional[IMPORT_reboot_aio_idempotency.Idempotency] = None,
        *,
        metadata: IMPORT_typing.Optional[IMPORT_reboot_aio_types.GrpcMetadata] = None,
        bearer_token: IMPORT_typing.Optional[str] = None,
    ) -> rbt.std.collections.queue.v1.queue_pb2.DequeueResponse:
        idempotency_key: IMPORT_typing.Optional[IMPORT_uuid.UUID]
        proto_request = QueueTryDequeueRequestToProto(
            request,
        )

        with self._idempotency_manager.idempotently(
            state_type_name=IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue'),
            state_ref=self._headers.state_ref,
            service_name=IMPORT_reboot_aio_types.ServiceName('rbt.std.collections.queue.v1.QueueMethods'),
            method='TryDequeue',
            mutation=True,
            request=proto_request,
            metadata=metadata,
            idempotency=idempotency,
            aborted_type=Queue.TryDequeueAborted,
        ) as idempotency_key:
            async with self._call(
                IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue'),
                IMPORT_reboot_aio_types.ServiceName('rbt.std.collections.queue.v1.QueueMethods'),
                'TryDequeue',
                self._rbt_std_collections_queue_v1_queuemethods_stub.TryDequeue,
                proto_request,
                unary=True,
                reader=False,
                response_type=rbt.std.collections.queue.v1.queue_pb2.DequeueResponse,
                aborted_type=Queue.TryDequeueAborted,
                metadata=metadata,
                idempotency_key=idempotency_key,
                bearer_token=bearer_token,
            ) as call:
                assert isinstance(call, IMPORT_typing.Awaitable), type(call)
                return await call

    async def Empty(
        self,
        request: Queue.EmptyRequest,
        *,
        metadata: IMPORT_typing.Optional[IMPORT_reboot_aio_types.GrpcMetadata] = None,
        bearer_token: IMPORT_typing.Optional[str] = None,
    ) -> rbt.std.collections.queue.v1.queue_pb2.EmptyResponse:
        async with self._call(
            IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue'),
            IMPORT_reboot_aio_types.ServiceName('rbt.std.collections.queue.v1.QueueMethods'),
            'Empty',
            self._rbt_std_collections_queue_v1_queuemethods_stub.Empty,
            QueueEmptyRequestToProto(
                request,
            ),
            unary=True,
            reader=True,
            response_type=rbt.std.collections.queue.v1.queue_pb2.EmptyResponse,
            aborted_type=Queue.EmptyAborted,
            metadata=metadata,
            bearer_token=bearer_token,
        ) as call:
            assert isinstance(call, IMPORT_typing.Awaitable), type(call)
            return await call



class QueueTasksStub(_QueueStub):

    def __init__(
        self,
        context: IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
        *,
        state_ref: IMPORT_reboot_aio_types.StateRef,
        bearer_token: IMPORT_typing.Optional[str] = None,
    ):
        IMPORT_reboot_aio_types.assert_type(context, [IMPORT_reboot_aio_contexts.TransactionContext, IMPORT_reboot_aio_contexts.WorkflowContext, IMPORT_reboot_aio_external.ExternalContext])
        super().__init__(
            context=context,
            state_ref=state_ref,
            bearer_token=bearer_token,
        )

    # Queue specific methods:
    async def Enqueue(
        self,
        request: Queue.EnqueueRequest,
        idempotency: IMPORT_typing.Optional[IMPORT_reboot_aio_idempotency.Idempotency] = None,
        *,
        metadata: IMPORT_typing.Optional[IMPORT_reboot_aio_types.GrpcMetadata] = None,
        bearer_token: IMPORT_typing.Optional[str] = None,
    ) -> IMPORT_rbt_v1alpha1.tasks_pb2.TaskId:
        idempotency_key: IMPORT_typing.Optional[IMPORT_uuid.UUID]
        proto_request = QueueEnqueueRequestToProto(
            request,
        )

        with self._idempotency_manager.idempotently(
            state_type_name=IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue'),
            state_ref=self._headers.state_ref,
            service_name=IMPORT_reboot_aio_types.ServiceName('rbt.std.collections.queue.v1.QueueMethods'),
            method='Enqueue',
            mutation=True,
            request=proto_request,
            metadata=metadata,
            idempotency=idempotency,
            aborted_type=Queue.EnqueueAborted,
        ) as idempotency_key:
            async with self._call(
                IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue'),
                IMPORT_reboot_aio_types.ServiceName('rbt.std.collections.queue.v1.QueueMethods'),
                'Enqueue',
                self._rbt_std_collections_queue_v1_queuemethods_stub.Enqueue,
                proto_request,
                unary=True,
                reader=False,
                response_type=rbt.std.collections.queue.v1.queue_pb2.EnqueueResponse,
                aborted_type=Queue.EnqueueAborted,
                metadata=metadata,
                idempotency_key=idempotency_key,
                bearer_token=bearer_token,
            ) as call:
                assert isinstance(call, IMPORT_typing.Awaitable), type(call)
                await call
                for (key, value) in await call.trailing_metadata():  # type: ignore[misc, attr-defined]
                    if key == IMPORT_reboot_aio_headers.TASK_ID_UUID:
                        return IMPORT_rbt_v1alpha1.tasks_pb2.TaskId(
                            state_type=IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue'),
                            state_ref=self._headers.state_ref.to_str(),
                            task_uuid=IMPORT_uuid.UUID(value).bytes,
                        )
                raise IMPORT_rebootdev.aio.aborted.SystemAborted(
                    IMPORT_rbt_v1alpha1.errors_pb2.Internal(),
                    message='Trailing metadata missing for task schedule',
                )
    async def Dequeue(
        self,
        request: Queue.DequeueRequest,
        idempotency: IMPORT_typing.Optional[IMPORT_reboot_aio_idempotency.Idempotency] = None,
        *,
        metadata: IMPORT_typing.Optional[IMPORT_reboot_aio_types.GrpcMetadata] = None,
        bearer_token: IMPORT_typing.Optional[str] = None,
    ) -> IMPORT_rbt_v1alpha1.tasks_pb2.TaskId:
        idempotency_key: IMPORT_typing.Optional[IMPORT_uuid.UUID]
        proto_request = QueueDequeueRequestToProto(
            request,
        )

        with self._idempotency_manager.idempotently(
            state_type_name=IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue'),
            state_ref=self._headers.state_ref,
            service_name=IMPORT_reboot_aio_types.ServiceName('rbt.std.collections.queue.v1.QueueMethods'),
            method='Dequeue',
            mutation=True,
            request=proto_request,
            metadata=metadata,
            idempotency=idempotency,
            aborted_type=Queue.DequeueAborted,
        ) as idempotency_key:
            async with self._call(
                IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue'),
                IMPORT_reboot_aio_types.ServiceName('rbt.std.collections.queue.v1.QueueMethods'),
                'Dequeue',
                self._rbt_std_collections_queue_v1_queuemethods_stub.Dequeue,
                proto_request,
                unary=True,
                reader=False,
                response_type=rbt.std.collections.queue.v1.queue_pb2.DequeueResponse,
                aborted_type=Queue.DequeueAborted,
                metadata=metadata,
                idempotency_key=idempotency_key,
                bearer_token=bearer_token,
            ) as call:
                assert isinstance(call, IMPORT_typing.Awaitable), type(call)
                await call
                for (key, value) in await call.trailing_metadata():  # type: ignore[misc, attr-defined]
                    if key == IMPORT_reboot_aio_headers.TASK_ID_UUID:
                        return IMPORT_rbt_v1alpha1.tasks_pb2.TaskId(
                            state_type=IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue'),
                            state_ref=self._headers.state_ref.to_str(),
                            task_uuid=IMPORT_uuid.UUID(value).bytes,
                        )
                raise IMPORT_rebootdev.aio.aborted.SystemAborted(
                    IMPORT_rbt_v1alpha1.errors_pb2.Internal(),
                    message='Trailing metadata missing for task schedule',
                )
    async def TryDequeue(
        self,
        request: Queue.TryDequeueRequest,
        idempotency: IMPORT_typing.Optional[IMPORT_reboot_aio_idempotency.Idempotency] = None,
        *,
        metadata: IMPORT_typing.Optional[IMPORT_reboot_aio_types.GrpcMetadata] = None,
        bearer_token: IMPORT_typing.Optional[str] = None,
    ) -> IMPORT_rbt_v1alpha1.tasks_pb2.TaskId:
        idempotency_key: IMPORT_typing.Optional[IMPORT_uuid.UUID]
        proto_request = QueueTryDequeueRequestToProto(
            request,
        )

        with self._idempotency_manager.idempotently(
            state_type_name=IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue'),
            state_ref=self._headers.state_ref,
            service_name=IMPORT_reboot_aio_types.ServiceName('rbt.std.collections.queue.v1.QueueMethods'),
            method='TryDequeue',
            mutation=True,
            request=proto_request,
            metadata=metadata,
            idempotency=idempotency,
            aborted_type=Queue.TryDequeueAborted,
        ) as idempotency_key:
            async with self._call(
                IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue'),
                IMPORT_reboot_aio_types.ServiceName('rbt.std.collections.queue.v1.QueueMethods'),
                'TryDequeue',
                self._rbt_std_collections_queue_v1_queuemethods_stub.TryDequeue,
                proto_request,
                unary=True,
                reader=False,
                response_type=rbt.std.collections.queue.v1.queue_pb2.DequeueResponse,
                aborted_type=Queue.TryDequeueAborted,
                metadata=metadata,
                idempotency_key=idempotency_key,
                bearer_token=bearer_token,
            ) as call:
                assert isinstance(call, IMPORT_typing.Awaitable), type(call)
                await call
                for (key, value) in await call.trailing_metadata():  # type: ignore[misc, attr-defined]
                    if key == IMPORT_reboot_aio_headers.TASK_ID_UUID:
                        return IMPORT_rbt_v1alpha1.tasks_pb2.TaskId(
                            state_type=IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue'),
                            state_ref=self._headers.state_ref.to_str(),
                            task_uuid=IMPORT_uuid.UUID(value).bytes,
                        )
                raise IMPORT_rebootdev.aio.aborted.SystemAborted(
                    IMPORT_rbt_v1alpha1.errors_pb2.Internal(),
                    message='Trailing metadata missing for task schedule',
                )
    async def Empty(
        self,
        request: Queue.EmptyRequest,
        idempotency: IMPORT_typing.Optional[IMPORT_reboot_aio_idempotency.Idempotency] = None,
        *,
        metadata: IMPORT_typing.Optional[IMPORT_reboot_aio_types.GrpcMetadata] = None,
        bearer_token: IMPORT_typing.Optional[str] = None,
    ) -> IMPORT_rbt_v1alpha1.tasks_pb2.TaskId:
        idempotency_key: IMPORT_typing.Optional[IMPORT_uuid.UUID]
        proto_request = QueueEmptyRequestToProto(
            request,
        )

        with self._idempotency_manager.idempotently(
            state_type_name=IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue'),
            state_ref=self._headers.state_ref,
            service_name=IMPORT_reboot_aio_types.ServiceName('rbt.std.collections.queue.v1.QueueMethods'),
            method='Empty',
            mutation=True,
            request=proto_request,
            metadata=metadata,
            idempotency=idempotency,
            aborted_type=Queue.EmptyAborted,
        ) as idempotency_key:
            async with self._call(
                IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue'),
                IMPORT_reboot_aio_types.ServiceName('rbt.std.collections.queue.v1.QueueMethods'),
                'Empty',
                self._rbt_std_collections_queue_v1_queuemethods_stub.Empty,
                proto_request,
                unary=True,
                reader=False,
                response_type=rbt.std.collections.queue.v1.queue_pb2.EmptyResponse,
                aborted_type=Queue.EmptyAborted,
                metadata=metadata,
                idempotency_key=idempotency_key,
                bearer_token=bearer_token,
            ) as call:
                assert isinstance(call, IMPORT_typing.Awaitable), type(call)
                await call
                for (key, value) in await call.trailing_metadata():  # type: ignore[misc, attr-defined]
                    if key == IMPORT_reboot_aio_headers.TASK_ID_UUID:
                        return IMPORT_rbt_v1alpha1.tasks_pb2.TaskId(
                            state_type=IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue'),
                            state_ref=self._headers.state_ref.to_str(),
                            task_uuid=IMPORT_uuid.UUID(value).bytes,
                        )
                raise IMPORT_rebootdev.aio.aborted.SystemAborted(
                    IMPORT_rbt_v1alpha1.errors_pb2.Internal(),
                    message='Trailing metadata missing for task schedule',
                )


class QueueServicerTasks:

    _context: IMPORT_reboot_aio_contexts.WriterContext

    def __init__(
        self,
        context: IMPORT_reboot_aio_contexts.WriterContext,
        *,
        state_ref: IMPORT_reboot_aio_types.StateRef,
        bearer_token: IMPORT_typing.Optional[str] = None,
    ):
        IMPORT_reboot_aio_types.assert_type(context, [IMPORT_reboot_aio_contexts.WriterContext])
        self._context = context
        self._state_ref = state_ref

    # Queue specific methods:
    async def Enqueue(
        self,
        request: Queue.EnqueueRequest,
        *,
        schedule: IMPORT_typing.Optional[IMPORT_datetime_datetime | IMPORT_datetime_timedelta] = None,
    ) -> IMPORT_reboot_aio_tasks.TaskEffect:
        schedule = ensure_has_timezone(when=schedule)
        task = IMPORT_reboot_aio_tasks.TaskEffect(
            state_type=IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue'),
            state_ref=self._state_ref,
            method_name='Enqueue',
            request=QueueEnqueueRequestToProto(
                request,
            ),
            schedule=(IMPORT_reboot_time_DateTimeWithTimeZone.now() + schedule) if isinstance(
                schedule, IMPORT_datetime_timedelta
            ) else schedule,
        )

        self._context._tasks.append(task)

        return task

    async def Dequeue(
        self,
        request: Queue.DequeueRequest,
        *,
        schedule: IMPORT_typing.Optional[IMPORT_datetime_datetime | IMPORT_datetime_timedelta] = None,
    ) -> IMPORT_reboot_aio_tasks.TaskEffect:
        schedule = ensure_has_timezone(when=schedule)
        task = IMPORT_reboot_aio_tasks.TaskEffect(
            state_type=IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue'),
            state_ref=self._state_ref,
            method_name='Dequeue',
            request=QueueDequeueRequestToProto(
                request,
            ),
            schedule=(IMPORT_reboot_time_DateTimeWithTimeZone.now() + schedule) if isinstance(
                schedule, IMPORT_datetime_timedelta
            ) else schedule,
        )

        self._context._tasks.append(task)

        return task

    async def TryDequeue(
        self,
        request: Queue.TryDequeueRequest,
        *,
        schedule: IMPORT_typing.Optional[IMPORT_datetime_datetime | IMPORT_datetime_timedelta] = None,
    ) -> IMPORT_reboot_aio_tasks.TaskEffect:
        schedule = ensure_has_timezone(when=schedule)
        task = IMPORT_reboot_aio_tasks.TaskEffect(
            state_type=IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue'),
            state_ref=self._state_ref,
            method_name='TryDequeue',
            request=QueueTryDequeueRequestToProto(
                request,
            ),
            schedule=(IMPORT_reboot_time_DateTimeWithTimeZone.now() + schedule) if isinstance(
                schedule, IMPORT_datetime_timedelta
            ) else schedule,
        )

        self._context._tasks.append(task)

        return task

    async def Empty(
        self,
        request: Queue.EmptyRequest,
        *,
        schedule: IMPORT_typing.Optional[IMPORT_datetime_datetime | IMPORT_datetime_timedelta] = None,
    ) -> IMPORT_reboot_aio_tasks.TaskEffect:
        schedule = ensure_has_timezone(when=schedule)
        task = IMPORT_reboot_aio_tasks.TaskEffect(
            state_type=IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue'),
            state_ref=self._state_ref,
            method_name='Empty',
            request=QueueEmptyRequestToProto(
                request,
            ),
            schedule=(IMPORT_reboot_time_DateTimeWithTimeZone.now() + schedule) if isinstance(
                schedule, IMPORT_datetime_timedelta
            ) else schedule,
        )

        self._context._tasks.append(task)

        return task



############################ Authorizers ############################
# Relevant to servicers; irrelevant to clients.

QueueStateType: IMPORT_typing.TypeAlias = rbt.std.collections.queue.v1.queue_pb2.Queue
QueueRequestTypes: IMPORT_typing.TypeAlias = \
        rbt.std.collections.queue.v1.queue_pb2.EnqueueRequest \
        | rbt.std.collections.queue.v1.queue_pb2.DequeueRequest \
        | rbt.std.collections.queue.v1.queue_pb2.EmptyRequest

class QueueAuthorizer(
    IMPORT_rebootdev.aio.auth.authorizers.Authorizer[QueueStateType, QueueRequestTypes],
):
    StateType: IMPORT_typing.TypeAlias = QueueStateType
    RequestTypes: IMPORT_typing.TypeAlias = QueueRequestTypes
    Decision: IMPORT_typing.TypeAlias = IMPORT_rebootdev.aio.auth.authorizers.Authorizer.Decision

    def __init__(
        self,
        *,
        Enqueue: IMPORT_typing.Optional[
            IMPORT_rebootdev.aio.auth.authorizers.AuthorizerRule[
              Queue.State,
              Queue.EnqueueRequest,
            ]
        ] = None,
        enqueue: IMPORT_typing.Optional[
            IMPORT_rebootdev.aio.auth.authorizers.AuthorizerRule[
              Queue.State,
              Queue.EnqueueRequest,
            ]
        ] = None,
        Dequeue: IMPORT_typing.Optional[
            IMPORT_rebootdev.aio.auth.authorizers.AuthorizerRule[
              Queue.State,
              Queue.DequeueRequest,
            ]
        ] = None,
        dequeue: IMPORT_typing.Optional[
            IMPORT_rebootdev.aio.auth.authorizers.AuthorizerRule[
              Queue.State,
              Queue.DequeueRequest,
            ]
        ] = None,
        TryDequeue: IMPORT_typing.Optional[
            IMPORT_rebootdev.aio.auth.authorizers.AuthorizerRule[
              Queue.State,
              Queue.TryDequeueRequest,
            ]
        ] = None,
        try_dequeue: IMPORT_typing.Optional[
            IMPORT_rebootdev.aio.auth.authorizers.AuthorizerRule[
              Queue.State,
              Queue.TryDequeueRequest,
            ]
        ] = None,
        Empty: IMPORT_typing.Optional[
            IMPORT_rebootdev.aio.auth.authorizers.AuthorizerRule[
              Queue.State,
              Queue.EmptyRequest,
            ]
        ] = None,
        empty: IMPORT_typing.Optional[
            IMPORT_rebootdev.aio.auth.authorizers.AuthorizerRule[
              Queue.State,
              Queue.EmptyRequest,
            ]
        ] = None,
        # NOTE: using `_` prefix for `_default` so as not to collide
        # with any method names since a prefixed `_` is forbidden by
        # our protoc plugins.
        _default: IMPORT_rebootdev.aio.auth.authorizers.AuthorizerRule[
            rbt.std.collections.queue.v1.queue_pb2.Queue,
            IMPORT_google_protobuf_message.Message,
        ] = IMPORT_rebootdev.aio.auth.authorizers.allow_if(
            all=[IMPORT_rebootdev.aio.auth.authorizers.is_app_internal],
        ),
    ):
        if enqueue is not None and Enqueue is not None:
            raise ValueError(
                f"Cannot specify both 'Enqueue' and 'enqueue' authorizer rules"
            )
        self._enqueue = enqueue or Enqueue
        if dequeue is not None and Dequeue is not None:
            raise ValueError(
                f"Cannot specify both 'Dequeue' and 'dequeue' authorizer rules"
            )
        self._dequeue = dequeue or Dequeue
        if try_dequeue is not None and TryDequeue is not None:
            raise ValueError(
                f"Cannot specify both 'TryDequeue' and 'try_dequeue' authorizer rules"
            )
        self._try_dequeue = try_dequeue or TryDequeue
        if empty is not None and Empty is not None:
            raise ValueError(
                f"Cannot specify both 'Empty' and 'empty' authorizer rules"
            )
        self._empty = empty or Empty
        self.__default = _default

    async def authorize(
        self,
        *,
        method_name: str,
        context: IMPORT_reboot_aio_contexts.ReaderContext,
        state: IMPORT_typing.Optional[QueueStateType],
        request: IMPORT_typing.Optional[QueueRequestTypes],
        **kwargs,
    ) -> IMPORT_rebootdev.aio.auth.authorizers.Authorizer.Decision:
        if method_name == 'rbt.std.collections.queue.v1.QueueMethods.Enqueue':
            return await self.Enqueue(
                context=context,
                state=IMPORT_typing.cast(rbt.std.collections.queue.v1.queue_pb2.Queue, state),
                request=IMPORT_typing.cast(rbt.std.collections.queue.v1.queue_pb2.EnqueueRequest, request),
            )
        elif method_name == 'rbt.std.collections.queue.v1.QueueMethods.Dequeue':
            return await self.Dequeue(
                context=context,
                state=IMPORT_typing.cast(rbt.std.collections.queue.v1.queue_pb2.Queue, state),
                request=IMPORT_typing.cast(rbt.std.collections.queue.v1.queue_pb2.DequeueRequest, request),
            )
        elif method_name == 'rbt.std.collections.queue.v1.QueueMethods.TryDequeue':
            return await self.TryDequeue(
                context=context,
                state=IMPORT_typing.cast(rbt.std.collections.queue.v1.queue_pb2.Queue, state),
                request=IMPORT_typing.cast(rbt.std.collections.queue.v1.queue_pb2.DequeueRequest, request),
            )
        elif method_name == 'rbt.std.collections.queue.v1.QueueMethods.Empty':
            return await self.Empty(
                context=context,
                state=IMPORT_typing.cast(rbt.std.collections.queue.v1.queue_pb2.Queue, state),
                request=IMPORT_typing.cast(rbt.std.collections.queue.v1.queue_pb2.EmptyRequest, request),
            )
        else:
            return IMPORT_rbt_v1alpha1.errors_pb2.PermissionDenied()

    # For 'rbt.std.collections.queue.v1.QueueMethods.Enqueue'.
    async def Enqueue(
        self,
        *,
        context: IMPORT_reboot_aio_contexts.ReaderContext,
        state: Queue.State,
        request: Queue.EnqueueRequest,
    ) -> IMPORT_rebootdev.aio.auth.authorizers.Authorizer.Decision:
        return await (self._enqueue or self.__default).execute(
            context=context,
            state=state,
            request=request,
        )

    # For 'rbt.std.collections.queue.v1.QueueMethods.Dequeue'.
    async def Dequeue(
        self,
        *,
        context: IMPORT_reboot_aio_contexts.ReaderContext,
        state: Queue.State,
        request: Queue.DequeueRequest,
    ) -> IMPORT_rebootdev.aio.auth.authorizers.Authorizer.Decision:
        return await (self._dequeue or self.__default).execute(
            context=context,
            state=state,
            request=request,
        )

    # For 'rbt.std.collections.queue.v1.QueueMethods.TryDequeue'.
    async def TryDequeue(
        self,
        *,
        context: IMPORT_reboot_aio_contexts.ReaderContext,
        state: Queue.State,
        request: Queue.TryDequeueRequest,
    ) -> IMPORT_rebootdev.aio.auth.authorizers.Authorizer.Decision:
        return await (self._try_dequeue or self.__default).execute(
            context=context,
            state=state,
            request=request,
        )

    # For 'rbt.std.collections.queue.v1.QueueMethods.Empty'.
    async def Empty(
        self,
        *,
        context: IMPORT_reboot_aio_contexts.ReaderContext,
        state: Queue.State,
        request: Queue.EmptyRequest,
    ) -> IMPORT_rebootdev.aio.auth.authorizers.Authorizer.Decision:
        return await (self._empty or self.__default).execute(
            context=context,
            state=state,
            request=request,
        )



############################ Reboot Servicers ############################
# Base classes for server-side implementations of Reboot servicers.
# Irrelevant to clients.

class QueueBaseServicer(IMPORT_reboot_aio_servicers.Servicer):
    Authorizer: IMPORT_typing.TypeAlias = QueueAuthorizer

    __servicer__: IMPORT_contextvars.ContextVar[IMPORT_typing.Optional[QueueBaseServicer]] = IMPORT_contextvars.ContextVar(
        'Provides access to a servicer in the current asyncio context. '
        'We need that to be able to do inline writes and reads inside '
        'a workflow',
        default=None,
    )

    __service_names__ = [
        IMPORT_reboot_aio_types.ServiceName('rbt.std.collections.queue.v1.QueueMethods'),
    ]
    __state_type_name__ = IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue')
    __state_type__ = rbt.std.collections.queue.v1.queue_pb2.Queue
    __file_descriptor__ = rbt.std.collections.queue.v1.queue_pb2.DESCRIPTOR

    def __init__(self):
        super().__init__()
        # NOTE: need to hold on to the middleware so we can do inline
        # writes (see 'self.write(...)').
        #
        # Because '_middleware' is not really private this does mean
        # users may do possibly dangerous things, but this is no more
        # likely given they could have already overridden
        # 'create_middleware()'.
        self._middleware: IMPORT_typing.Optional[QueueServicerMiddleware] = None

    def create_middleware(
        self,
        *,
        application_id: IMPORT_reboot_aio_types.ApplicationId,
        server_id: IMPORT_reboot_aio_types.ServerId,
        state_manager: IMPORT_reboot_aio_state_managers.StateManager,
        placement_client: IMPORT_reboot_aio_placement.PlacementClient,
        channel_manager: IMPORT_reboot_aio_internals_channel_manager._ChannelManager,
        tasks_cache: IMPORT_reboot_aio_internals_tasks_cache.TasksCache,
        token_verifier: IMPORT_typing.Optional[IMPORT_rebootdev.aio.auth.token_verifiers.TokenVerifier],
        effect_validation: IMPORT_reboot_aio_contexts.EffectValidation,
        ready: IMPORT_asyncio.Event,
    ) -> QueueServicerMiddleware:
        self._middleware = QueueServicerMiddleware(
            servicer=self,
            application_id=application_id,
            server_id=server_id,
            state_manager=state_manager,
            placement_client=placement_client,
            channel_manager=channel_manager,
            tasks_cache=tasks_cache,
            token_verifier=token_verifier,
            effect_validation=effect_validation,
            ready=ready,
        )
        return self._middleware

    def authorizer(self) -> IMPORT_typing.Optional[IMPORT_rebootdev.aio.auth.authorizers.Authorizer | IMPORT_rebootdev.aio.auth.authorizers.AuthorizerRule]:
        return None

    def token_verifier(self) -> IMPORT_typing.Optional[IMPORT_rebootdev.aio.auth.token_verifiers.TokenVerifier]:
        return None

    def ref(
        self,
        *,
        bearer_token: IMPORT_typing.Optional[str] = None,
    ) -> Queue.WeakReference[Queue.WeakReference._WriterSchedule]:
        context = IMPORT_reboot_aio_contexts.Context.get()

        if context is None:
            raise RuntimeError(
                'Missing asyncio context variable `context`; '
                'are you using this class without Reboot?'
            )

        return Queue.WeakReference(
            # TODO(https://github.com/reboot-dev/mono/issues/3226): add support for calling other applications.
            # For now this always stays within the application that creates the context.
            application_id=None,
            state_id=context._state_ref.id,
            schedule_type=Queue.WeakReference._WriterSchedule,
            # If the user didn't specify a bearer token we may still end up using the app-internal bearer token,
            # but that's decided at the time of the call.
            bearer_token=bearer_token,
            servicer=self,
        )

    class Effects(IMPORT_reboot_aio_state_managers.Effects):
        def __init__(
            self,
            *,
            state: rbt.std.collections.queue.v1.queue_pb2.Queue,
            response: IMPORT_typing.Optional[IMPORT_google_protobuf_message.Message] = None,
            tasks: IMPORT_typing.Optional[list[IMPORT_reboot_aio_tasks.TaskEffect]] = None,
            _colocated_upserts: IMPORT_typing.Optional[list[tuple[str, IMPORT_typing.Optional[bytes]]]] = None,
        ):
            IMPORT_reboot_aio_types.assert_type(state, [rbt.std.collections.queue.v1.queue_pb2.Queue])

            super().__init__(state=state, response=response, tasks=tasks, _colocated_upserts=_colocated_upserts)






    InlineWriterCallableResult = IMPORT_typing.TypeVar('InlineWriterCallableResult', covariant=True)

    class InlineWriterCallable(IMPORT_typing.Protocol[InlineWriterCallableResult]):
        async def __call__(
            self,
            state: rbt.std.collections.queue.v1.queue_pb2.Queue
        ) -> QueueBaseServicer.InlineWriterCallableResult:
            ...

    class WorkflowState:

        def __init__(
            self,
            servicer,
        ):
            self._servicer = servicer

        async def read(
            self, context: IMPORT_reboot_aio_contexts.WorkflowContext
        ) -> Queue.State:
            """Read the current state within a workflow."""
            return await (
                self.always() if context.within_until()
                else (
                    self.per_iteration() if context.within_loop()
                    else self.per_workflow()
                )
            ).read(context)

        @IMPORT_typing.overload
        async def write(
            self,
            idempotency_alias: str,
            context: IMPORT_reboot_aio_contexts.WorkflowContext,
            writer: QueueBaseServicer.InlineWriterCallable[None],
            __options__: IMPORT_reboot_aio_call.Options = IMPORT_reboot_aio_call.Options(),
            *,
            type: type = type(None),
        ) -> None:
            ...

        @IMPORT_typing.overload
        async def write(
            self,
            idempotency_alias: str,
            context: IMPORT_reboot_aio_contexts.WorkflowContext,
            writer: QueueBaseServicer.InlineWriterCallable[QueueBaseServicer.InlineWriterCallableResult],
            __options__: IMPORT_reboot_aio_call.Options = IMPORT_reboot_aio_call.Options(),
            *,
            type: type[QueueBaseServicer.InlineWriterCallableResult],
        ) -> QueueBaseServicer.InlineWriterCallableResult:
            ...

        async def write(
            self,
            idempotency_alias: str,
            context: IMPORT_reboot_aio_contexts.WorkflowContext,
            writer: QueueBaseServicer.InlineWriterCallable[QueueBaseServicer.InlineWriterCallableResult],
            __options__: IMPORT_reboot_aio_call.Options = IMPORT_reboot_aio_call.Options(),
            *,
            type: type = type(None),
        ) -> QueueBaseServicer.InlineWriterCallableResult:
            """Perform an "inline write" within a workflow."""
            return await (
                self.per_iteration(idempotency_alias) if context.within_loop()
                else self.per_workflow(idempotency_alias)
            ).write(
                context, writer, __options__, type=type
            )

        class _Idempotently:

            def __init__(
                self,
                *,
                servicer: QueueBaseServicer,
                alias: IMPORT_typing.Optional[str],
                how: IMPORT_reboot_aio_workflows.How,
            ):
                self._servicer = servicer
                self._alias = alias
                self._how = how

            async def read(
                self, context: IMPORT_reboot_aio_contexts.WorkflowContext
            ) -> Queue.State:
                """Read the current state within a workflow."""
                return await self._read(
                    self._servicer,
                    context.idempotency(
                        key=IMPORT_uuid.uuid4(),
                        generated=True,
                    ) if self._how == IMPORT_reboot_aio_workflows.ALWAYS else context.idempotency(
                        alias=self._alias,
                        each_iteration=self._how == IMPORT_reboot_aio_workflows.PER_ITERATION
                    ),
                    context,
                )

            @staticmethod
            async def _read(
                servicer: QueueBaseServicer,
                idempotency: IMPORT_reboot_aio_idempotency.Idempotency,
                context: IMPORT_reboot_aio_contexts.WorkflowContext,
            ) -> Queue.State:
                """Read the current state within a workflow."""
                IMPORT_reboot_aio_types.assert_type(context, [IMPORT_reboot_aio_contexts.WorkflowContext])

                if servicer._middleware is None:
                    raise RuntimeError(
                        'Reboot middleware was not created; '
                        'are you using this class without Reboot?'
                    )

                async def read():
                    assert servicer._middleware is not None
                    return await servicer._middleware._state_manager.read(
                        context, servicer.__state_type__
                    )

                if idempotency.always:
                    return await read()

                state_type_name = IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue')

                # Use the idempotency manager to make sure that this
                # reader is being called following the rules.
                with context.idempotently(
                    state_type_name=state_type_name,
                    state_ref=context._state_ref,
                    # Not calling a method so `service_name`,
                    # `method`, `request`, etc are irrelevant.
                    service_name=None,
                    method=None,
                    mutation=False,
                    request=None,
                    metadata=None,
                    idempotency=idempotency,
                    # Only need to pass `aborted_type` for mutations.
                    aborted_type=None,
                ) as idempotency_key:
                    assert idempotency_key is not None
                    protobuf_state = await IMPORT_reboot_aio_workflows.at_least_once(
                        (
                            # TODO: for easier debugging include the
                            # original alias (or generated alias in
                            # the case of `.per_iteration()` w/o an
                            # alias) instead of just
                            # `idempotency_key`.
                            f"inline reader of '{ state_type_name }' ({str(idempotency_key)})",
                            # NOTE: we want this to be `PER_WORKFLOW`
                            # because any per iteration concerns
                            # should have already been taken care of
                            # by caller using `.per_iteration()`.
                            IMPORT_reboot_aio_workflows.PER_WORKFLOW
                        ),
                        context,
                        read,
                        type=rbt.std.collections.queue.v1.queue_pb2.Queue,
                    )

                    return QueueFromProto(protobuf_state)

            @IMPORT_typing.overload
            async def write(
                self,
                context: IMPORT_reboot_aio_contexts.WorkflowContext,
                writer: QueueBaseServicer.InlineWriterCallable[None],
                __options__: IMPORT_reboot_aio_call.Options = IMPORT_reboot_aio_call.Options(),
                *,
                type: type = type(None),
                check_type: bool = True,
            ) -> None:
                ...

            @IMPORT_typing.overload
            async def write(
                self,
                context: IMPORT_reboot_aio_contexts.WorkflowContext,
                writer: QueueBaseServicer.InlineWriterCallable[QueueBaseServicer.InlineWriterCallableResult],
                __options__: IMPORT_reboot_aio_call.Options = IMPORT_reboot_aio_call.Options(),
                *,
                type: type[QueueBaseServicer.InlineWriterCallableResult],
                check_type: bool = True,
            ) -> QueueBaseServicer.InlineWriterCallableResult:
                ...

            async def write(
                self,
                context: IMPORT_reboot_aio_contexts.WorkflowContext,
                writer: QueueBaseServicer.InlineWriterCallable[QueueBaseServicer.InlineWriterCallableResult],
                __options__: IMPORT_reboot_aio_call.Options = IMPORT_reboot_aio_call.Options(),
                *,
                type: type = type(None),
                check_type: bool = True,
            ) -> QueueBaseServicer.InlineWriterCallableResult:
                return await self._write(
                    context,
                    writer,
                    __options__,
                    type_result=type,
                    check_type=check_type,
                )

            async def _write(
                self,
                context: IMPORT_reboot_aio_contexts.WorkflowContext,
                writer: QueueBaseServicer.InlineWriterCallable[QueueBaseServicer.InlineWriterCallableResult],
                __options__: IMPORT_reboot_aio_call.Options = IMPORT_reboot_aio_call.Options(),
                *,
                type_result: type,
                check_type: bool,
            ) -> QueueBaseServicer.InlineWriterCallableResult:
                unidempotently = self._how == IMPORT_reboot_aio_workflows.ALWAYS
                idempotency = (
                    context.idempotency(
                        key=IMPORT_uuid.uuid4(),
                        generated=True,
                    ) if unidempotently else context.idempotency(
                        alias=self._alias,
                        each_iteration=self._how == IMPORT_reboot_aio_workflows.PER_ITERATION
                    )
                )

                return await self._write_validating_effects(
                    self._servicer,
                    idempotency,
                    context,
                    writer,
                    __options__,
                    type_result=type_result,
                    check_type=check_type,
                    unidempotently=unidempotently,
                    checkpoint=context.checkpoint(),
                )

            @staticmethod
            @IMPORT_reboot_aio_internals_middleware.maybe_run_function_twice_to_validate_effects
            async def _write_validating_effects(
                validating_effects: bool,
                servicer: QueueBaseServicer,
                idempotency: IMPORT_reboot_aio_idempotency.Idempotency,
                context: IMPORT_reboot_aio_contexts.WorkflowContext,
                writer: QueueBaseServicer.InlineWriterCallable[QueueBaseServicer.InlineWriterCallableResult],
                __options__: IMPORT_reboot_aio_call.Options = IMPORT_reboot_aio_call.Options(),
                *,
                type_result: type,
                check_type: bool,
                unidempotently: bool,
                checkpoint: IMPORT_reboot_aio_idempotency.Checkpoint,
            ) -> QueueBaseServicer.InlineWriterCallableResult:
                IMPORT_reboot_aio_types.assert_type(__options__, [IMPORT_reboot_aio_call.Options])
                if __options__.idempotency is not None:
                    raise RuntimeError(
                        'Found redundant idempotency in `Options`'
                    )

                IMPORT_reboot_aio_types.assert_type(context, [IMPORT_reboot_aio_contexts.WorkflowContext])

                if servicer._middleware is None:
                    raise RuntimeError(
                        'Reboot middleware was not created; '
                        'are you using this class without Reboot?'
                    )

                metadata: IMPORT_typing.Optional[IMPORT_reboot_aio_types.GrpcMetadata] = None

                if __options__ is not None:
                    if __options__.metadata is not None:
                        metadata = __options__.metadata

                if metadata is None:
                    metadata = ()

                headers = IMPORT_reboot_aio_headers.Headers(
                    application_id=context.application_id,
                    state_ref=context._state_ref,
                    caller_id=IMPORT_reboot_aio_caller_id.CallerID(
                        application_id=context.application_id,
                    ),
                )

                metadata += headers.to_grpc_metadata()

                idempotency_key: IMPORT_typing.Optional[IMPORT_uuid.UUID]
                with context.idempotently(
                    state_type_name=IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue'),
                    state_ref=context._state_ref,
                    service_name=None,  # Indicates an inline writer.
                    method=None,  # Indicates an inline writer.
                    mutation=True,
                    request=None,  # Indicates an inline writer.
                    metadata=metadata,
                    idempotency=idempotency,
                    aborted_type=None,  # Indicates an inline writer.
                ) as idempotency_key:

                    if any(t[0] == IMPORT_reboot_aio_headers.IDEMPOTENCY_KEY_HEADER for t in metadata):
                        raise ValueError(
                            f"Do not set '{IMPORT_reboot_aio_headers.IDEMPOTENCY_KEY_HEADER}' metadata yourself"
                        )

                    if idempotency_key is not None:
                        metadata += (
                            (IMPORT_reboot_aio_headers.IDEMPOTENCY_KEY_HEADER, str(idempotency_key)),
                        )

                    with servicer._middleware.use_context(
                        headers=IMPORT_reboot_aio_headers.Headers.from_grpc_metadata(metadata),
                        state_type_name = IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue'),
                        method='inline writer',
                        context_type=IMPORT_reboot_aio_contexts.WriterContext,
                    ) as writer_context:
                        # Check if we already have performed this mutation!
                        #
                        # We do this _before_ calling 'transactionally()' because
                        # if this call is for a transaction method _and_ we've
                        # already performed the transaction then we don't want to
                        # become a transaction participant (again) we just want to
                        # return the transaction's response.
                        idempotent_mutation = (
                            await servicer._middleware._state_manager.check_for_idempotent_mutation(
                                writer_context
                            )
                        )

                        if idempotent_mutation is not None:
                            assert len(idempotent_mutation.response) != 0
                            response = IMPORT_google_protobuf_wrappers_pb2.BytesValue()
                            response.ParseFromString(idempotent_mutation.response)
                            result: QueueBaseServicer.InlineWriterCallableResult = IMPORT_pickle.loads(response.value)

                            if check_type and type(result) is not type_result:
                                raise TypeError(
                                    f"Stored result of type '{type(result).__name__}' from 'writer' "
                                    f"is not of expected type '{type_result.__name__}'; have you changed "
                                    "the 'type' that you expect after having stored a result?"
                                )

                            return result

                        async with servicer._middleware._state_manager.transactionally(
                            writer_context,
                            servicer._middleware.tasks_dispatcher,
                            aborted_type=None,
                        ) as transaction:
                            async with servicer._middleware._state_manager.writer(
                                writer_context,
                                servicer.__state_type__,
                                servicer._middleware.tasks_dispatcher,
                                # TODO: Decide if we want to do any kind of authorization for inline
                                # writers otherwise passing `None` here is fine.
                                authorize=None,
                                transaction=transaction,
                            ) as (protobuf_state, state_manager_writer):
                                # Serialize the state so we can see if it changed.
                                serialized_state = protobuf_state.SerializeToString(
                                    deterministic=True,
                                )

                                typed_state = QueueFromProto(protobuf_state)

                                result = await writer(state=typed_state)

                                QueueToProto(typed_state, protobuf_state)

                                if check_type and type(result) is not type_result:
                                    raise TypeError(
                                        f"Result of type '{type(result).__name__}' from 'writer' is "
                                        f"not of expected type '{type_result.__name__}'; "
                                        "did you specify an incorrect 'type'?"
                                    )

                                task: IMPORT_typing.Optional[IMPORT_reboot_aio_tasks.TaskEffect] = context.task

                                assert task is not None, (
                                    "Should always have a task when running a `workflow`"
                                )

                                method_name = f"Queue.{task.method_name} inline writer"

                                if idempotency.alias is not None:
                                    method_name += " with idempotency alias '" + idempotency.alias + "'"
                                elif idempotency.key is not None:
                                    method_name += " with idempotency key=" + str(idempotency.key)

                                servicer._middleware.maybe_raise_effect_validation_retry(
                                    logger=logger,
                                    idempotency_manager=context,
                                    method_name=method_name,
                                    validating_effects=validating_effects,
                                    context=context,
                                    checkpoint=checkpoint,
                                )

                                # We don't pass the context to the
                                # writer, so we don't expect there to
                                # be any scheduled tasks!
                                assert len(context._tasks) == 0

                                effects = IMPORT_reboot_aio_state_managers.Effects(
                                    state=(
                                        # Pass `None` if the state hasn't changed!
                                        protobuf_state if serialized_state != protobuf_state.SerializeToString(
                                            deterministic=True,
                                        )
                                        else None
                                    ),
                                    response=IMPORT_google_protobuf_wrappers_pb2.BytesValue(
                                        value=IMPORT_pickle.dumps(result)
                                    ),
                                )

                                await state_manager_writer.complete(effects)

                                return result

        def per_workflow(self, alias: IMPORT_typing.Optional[str] = None):
            return QueueBaseServicer.WorkflowState._Idempotently(
                servicer=self._servicer,
                alias=alias,
                how=IMPORT_reboot_aio_workflows.PER_WORKFLOW,
            )

        def per_iteration(self, alias: IMPORT_typing.Optional[str] = None):
            return QueueBaseServicer.WorkflowState._Idempotently(
                servicer=self._servicer,
                alias=alias,
                how=IMPORT_reboot_aio_workflows.PER_ITERATION,
            )

        class _Always:
            """Helper class for providing better types for `write` that don't
            require passing `type` or `check_type`."""

            def __init__(
                self,
                *,
                servicer: QueueBaseServicer,
            ):
                self._servicer = servicer

            async def read(
                self, context: IMPORT_reboot_aio_contexts.WorkflowContext
            ) -> Queue.State:
                return await QueueBaseServicer.WorkflowState._Idempotently(
                    servicer=self._servicer,
                    alias=None,
                    how=IMPORT_reboot_aio_workflows.ALWAYS,
                ).read(context)

            async def write(
                self,
                context: IMPORT_reboot_aio_contexts.WorkflowContext,
                writer: QueueBaseServicer.InlineWriterCallable[QueueBaseServicer.InlineWriterCallableResult],
                __options__: IMPORT_reboot_aio_call.Options = IMPORT_reboot_aio_call.Options(),
            ) -> QueueBaseServicer.InlineWriterCallableResult:
                return await QueueBaseServicer.WorkflowState._Idempotently(
                    servicer=self._servicer,
                    alias=None,
                    how=IMPORT_reboot_aio_workflows.ALWAYS,
                )._write(
                    context,
                    writer,
                    __options__,
                    type_result=type(None),
                    check_type=False,
                )

        def always(self):
            return QueueBaseServicer.WorkflowState._Always(
                servicer=self._servicer,
            )

    # For 'rbt.std.collections.queue.v1.QueueMethods.Enqueue'.
    @IMPORT_abc_abstractmethod
    async def _Enqueue(
        self,
        context: IMPORT_reboot_aio_contexts.TransactionContext,
        state: Queue.State,
        request: rbt.std.collections.queue.v1.queue_pb2.EnqueueRequest,
    ) -> rbt.std.collections.queue.v1.queue_pb2.EnqueueResponse:
        raise NotImplementedError

    # For 'rbt.std.collections.queue.v1.QueueMethods.Dequeue'.
    @IMPORT_abc_abstractmethod
    async def _Dequeue(
        self,
        context: IMPORT_reboot_aio_contexts.WorkflowContext,
        request: rbt.std.collections.queue.v1.queue_pb2.DequeueRequest,
    ) -> rbt.std.collections.queue.v1.queue_pb2.DequeueResponse:
        raise NotImplementedError

    # For 'rbt.std.collections.queue.v1.QueueMethods.TryDequeue'.
    @IMPORT_abc_abstractmethod
    async def _TryDequeue(
        self,
        context: IMPORT_reboot_aio_contexts.TransactionContext,
        state: Queue.State,
        request: rbt.std.collections.queue.v1.queue_pb2.DequeueRequest,
    ) -> rbt.std.collections.queue.v1.queue_pb2.DequeueResponse:
        raise NotImplementedError

    # For 'rbt.std.collections.queue.v1.QueueMethods.Empty'.
    @IMPORT_abc_abstractmethod
    async def _Empty(
        self,
        context: IMPORT_reboot_aio_contexts.ReaderContext,
        state: Queue.State,
        request: rbt.std.collections.queue.v1.queue_pb2.EmptyRequest,
    ) -> rbt.std.collections.queue.v1.queue_pb2.EmptyResponse:
        raise NotImplementedError



class QueueSingletonServicer(QueueBaseServicer):

    @property
    def state(self):
        return QueueBaseServicer.WorkflowState(
            servicer=self
        )

    # For 'rbt.std.collections.queue.v1.QueueMethods.Enqueue'.
    # To be backwards compatible during the renaming don't make this
    # method to be 'abstractmethod', so that new code that
    # doesn't implement it continues to work.
    # TODO: make it abstractmethod when renaming is done.
    async def Enqueue(
        self,
        context: IMPORT_reboot_aio_contexts.TransactionContext,
        state: Queue.State,
        request: Queue.EnqueueRequest,
    ) -> Queue.EnqueueResponse:
        # During the migration from 'PascalCase' to 'snake_case' method
        # naming in Python servicers, we call the 'snake_case' version
        # by default, so new names will do the correct thing making the
        # code to be backwards compatible for some time and if a servicer
        # overrides the 'PascalCase' version - it will override that
        # method and will just work.
        return await self.enqueue(
            context,
            state,
            request,
        )

    # To be backwards compatible during the renaming don't make this
    # method to be 'abstractmethod', so that existing code that
    # doesn't implement it continues to work.
    async def enqueue(
        self,
        context: IMPORT_reboot_aio_contexts.TransactionContext,
        state: Queue.State,
        request: Queue.EnqueueRequest,
    ) -> Queue.EnqueueResponse:
        raise NotImplementedError

    # For 'rbt.std.collections.queue.v1.QueueMethods.Dequeue'.
    # To be backwards compatible during the renaming don't make this
    # method to be 'abstractmethod', so that new code that
    # doesn't implement it continues to work.
    # TODO: make it abstractmethod when renaming is done.
    @classmethod
    async def Dequeue(
        cls,
        context: IMPORT_reboot_aio_contexts.WorkflowContext,
        request: Queue.DequeueRequest,
    ) -> Queue.DequeueResponse:
        # During the migration from 'PascalCase' to 'snake_case' method
        # naming in Python servicers, we call the 'snake_case' version
        # by default, so new names will do the correct thing making the
        # code to be backwards compatible for some time and if a servicer
        # overrides the 'PascalCase' version - it will override that
        # method and will just work.
        return await cls.dequeue(
            context,
            request,
        )

    # To be backwards compatible during the renaming don't make this
    # method to be 'abstractmethod', so that existing code that
    # doesn't implement it continues to work.
    @classmethod
    async def dequeue(
        cls,
        context: IMPORT_reboot_aio_contexts.WorkflowContext,
        request: Queue.DequeueRequest,
    ) -> Queue.DequeueResponse:
        raise NotImplementedError

    # For 'rbt.std.collections.queue.v1.QueueMethods.TryDequeue'.
    # To be backwards compatible during the renaming don't make this
    # method to be 'abstractmethod', so that new code that
    # doesn't implement it continues to work.
    # TODO: make it abstractmethod when renaming is done.
    async def TryDequeue(
        self,
        context: IMPORT_reboot_aio_contexts.TransactionContext,
        state: Queue.State,
        request: Queue.TryDequeueRequest,
    ) -> Queue.TryDequeueResponse:
        # During the migration from 'PascalCase' to 'snake_case' method
        # naming in Python servicers, we call the 'snake_case' version
        # by default, so new names will do the correct thing making the
        # code to be backwards compatible for some time and if a servicer
        # overrides the 'PascalCase' version - it will override that
        # method and will just work.
        return await self.try_dequeue(
            context,
            state,
            request,
        )

    # To be backwards compatible during the renaming don't make this
    # method to be 'abstractmethod', so that existing code that
    # doesn't implement it continues to work.
    async def try_dequeue(
        self,
        context: IMPORT_reboot_aio_contexts.TransactionContext,
        state: Queue.State,
        request: Queue.TryDequeueRequest,
    ) -> Queue.TryDequeueResponse:
        raise NotImplementedError

    # For 'rbt.std.collections.queue.v1.QueueMethods.Empty'.
    # To be backwards compatible during the renaming don't make this
    # method to be 'abstractmethod', so that new code that
    # doesn't implement it continues to work.
    # TODO: make it abstractmethod when renaming is done.
    async def Empty(
        self,
        context: IMPORT_reboot_aio_contexts.ReaderContext,
        state: Queue.State,
        request: Queue.EmptyRequest,
    ) -> Queue.EmptyResponse:
        # During the migration from 'PascalCase' to 'snake_case' method
        # naming in Python servicers, we call the 'snake_case' version
        # by default, so new names will do the correct thing making the
        # code to be backwards compatible for some time and if a servicer
        # overrides the 'PascalCase' version - it will override that
        # method and will just work.
        return await self.empty(
            context,
            state,
            request,
        )

    # To be backwards compatible during the renaming don't make this
    # method to be 'abstractmethod', so that existing code that
    # doesn't implement it continues to work.
    # TODO: make it abstractmethod when renaming is done.
    async def empty(
        self,
        context: IMPORT_reboot_aio_contexts.ReaderContext,
        state: Queue.State,
        request: Queue.EmptyRequest,
    ) -> Queue.EmptyResponse:
        raise NotImplementedError


    # For 'rbt.std.collections.queue.v1.QueueMethods.Enqueue'.
    async def _Enqueue(
        self,
        context: IMPORT_reboot_aio_contexts.TransactionContext,
        state: Queue.State,
        request: rbt.std.collections.queue.v1.queue_pb2.EnqueueRequest,
    ) -> rbt.std.collections.queue.v1.queue_pb2.EnqueueResponse:
        # Wrap the call to the developer's method in a `span` so that it
        # is traced using its fully-qualified Python name.
        with IMPORT_reboot_aio_tracing.span(
                state_name=f"rbt.std.collections.queue.v1.Queue('{context.state_id}')",
                span_name=f"{IMPORT_reboot_aio_tracing.qualified_type_name(self)}.Enqueue()",
                level=IMPORT_reboot_aio_tracing.TraceLevel.CUSTOMER,
                python_specific=True,
        ):
            typed_request = QueueEnqueueRequestFromProto(request)
            return QueueEnqueueResponseToProto(
                await self.Enqueue(
                    context,
                    state,
                    typed_request
                )
            )


    # For 'rbt.std.collections.queue.v1.QueueMethods.Dequeue'.
    async def _Dequeue(
        self,
        context: IMPORT_reboot_aio_contexts.WorkflowContext,
        request: rbt.std.collections.queue.v1.queue_pb2.DequeueRequest,
    ) -> rbt.std.collections.queue.v1.queue_pb2.DequeueResponse:
        # Wrap the call to the developer's method in a `span` so that it
        # is traced using its fully-qualified Python name.
        with IMPORT_reboot_aio_tracing.span(
                state_name=f"rbt.std.collections.queue.v1.Queue('{context.state_id}')",
                span_name=f"{IMPORT_reboot_aio_tracing.qualified_type_name(self)}.Dequeue()",
                level=IMPORT_reboot_aio_tracing.TraceLevel.CUSTOMER,
                python_specific=True,
        ):
            typed_request = QueueDequeueRequestFromProto(request)
            return QueueDequeueResponseToProto(
                await self.Dequeue(
                    context,
                    typed_request,
                )
            )


    # For 'rbt.std.collections.queue.v1.QueueMethods.TryDequeue'.
    async def _TryDequeue(
        self,
        context: IMPORT_reboot_aio_contexts.TransactionContext,
        state: Queue.State,
        request: rbt.std.collections.queue.v1.queue_pb2.DequeueRequest,
    ) -> rbt.std.collections.queue.v1.queue_pb2.DequeueResponse:
        # Wrap the call to the developer's method in a `span` so that it
        # is traced using its fully-qualified Python name.
        with IMPORT_reboot_aio_tracing.span(
                state_name=f"rbt.std.collections.queue.v1.Queue('{context.state_id}')",
                span_name=f"{IMPORT_reboot_aio_tracing.qualified_type_name(self)}.TryDequeue()",
                level=IMPORT_reboot_aio_tracing.TraceLevel.CUSTOMER,
                python_specific=True,
        ):
            typed_request = QueueTryDequeueRequestFromProto(request)
            return QueueTryDequeueResponseToProto(
                await self.TryDequeue(
                    context,
                    state,
                    typed_request
                )
            )


    # For 'rbt.std.collections.queue.v1.QueueMethods.Empty'.
    async def _Empty(
        self,
        context: IMPORT_reboot_aio_contexts.ReaderContext,
        state: Queue.State,
        request: rbt.std.collections.queue.v1.queue_pb2.EmptyRequest,
    ) -> rbt.std.collections.queue.v1.queue_pb2.EmptyResponse:
        # Wrap the call to the developer's method in a `span` so that it
        # is traced using its fully-qualified Python name.
        with IMPORT_reboot_aio_tracing.span(
                state_name=f"rbt.std.collections.queue.v1.Queue('{context.state_id}')",
                span_name=f"{IMPORT_reboot_aio_tracing.qualified_type_name(self)}.Empty()",
                level=IMPORT_reboot_aio_tracing.TraceLevel.CUSTOMER,
                python_specific=True,
        ):
            typed_request = QueueEmptyRequestFromProto(request)
            response = (
                self.Empty(
                    context,
                    state,
                    typed_request,
                )
            )
            return QueueEmptyResponseToProto(await response)



class QueueServicer(QueueBaseServicer):

    _state: IMPORT_contextvars.ContextVar[
        IMPORT_typing.Optional[Queue.State]
    ] = IMPORT_contextvars.ContextVar(
        'Provides access to state for each call, i.e., there may be '
        'multiple readers executing concurrently but each might have '
        'a different `state`',
        default=None,
    )

    # An instance of the derived class for each state.
    _instances: dict[str, QueueServicer] = {}

    def _instance(self, state_id: str):
        instances = QueueServicer._instances
        instance = instances.get(state_id)
        if instance is None:
            instance = self.__class__()
            instance._middleware = self._middleware
        instances[state_id] = instance
        return instance

    @property
    def state(self) -> Queue.State:
        state = QueueServicer._state.get()
        if state is None:
            raise RuntimeError(
                "`state` property is only relevant within a `Servicer` method"
            )
        return state

    @state.setter
    def state(self, new_state: Queue.State):
        state = QueueServicer._state.get()
        if state is None:
            raise RuntimeError(
                "`state` property is only relevant within a `Servicer` method"
            )
        state.CopyFrom(new_state)

    # For 'rbt.std.collections.queue.v1.QueueMethods.Enqueue'.
    # To be backwards compatible during the renaming don't make this
    # method to be 'abstractmethod', so that new code that
    # doesn't implement it continues to work.
    # TODO: make it abstractmethod when renaming is done.
    async def Enqueue(
        self,
        context: IMPORT_reboot_aio_contexts.TransactionContext,
        request: Queue.EnqueueRequest,
    ) -> Queue.EnqueueResponse:
        # During the migration from 'PascalCase' to 'snake_case' method
        # naming in Python servicers, we call the 'snake_case' version
        # by default, so new names will do the correct thing making the
        # code to be backwards compatible for some time and if a servicer
        # overrides the 'PascalCase' version - it will override that
        # method and will just work.
        return await self.enqueue(
            context,
            request,
        )

    # To be backwards compatible during the renaming don't make this
    # method to be 'abstractmethod', so that existing code that
    # doesn't implement it continues to work.
    async def enqueue(
        self,
        context: IMPORT_reboot_aio_contexts.TransactionContext,
        request: Queue.EnqueueRequest,
    ) -> Queue.EnqueueResponse:
        raise NotImplementedError

    # For 'rbt.std.collections.queue.v1.QueueMethods.Dequeue'.
    # To be backwards compatible during the renaming don't make this
    # method to be 'abstractmethod', so that new code that
    # doesn't implement it continues to work.
    # TODO: make it abstractmethod when renaming is done.
    @classmethod
    async def Dequeue(
        cls,
        context: IMPORT_reboot_aio_contexts.WorkflowContext,
        request: Queue.DequeueRequest,
    ) -> Queue.DequeueResponse:
        # During the migration from 'PascalCase' to 'snake_case' method
        # naming in Python servicers, we call the 'snake_case' version
        # by default, so new names will do the correct thing making the
        # code to be backwards compatible for some time and if a servicer
        # overrides the 'PascalCase' version - it will override that
        # method and will just work.
        return await cls.dequeue(
            context,
            request,
        )

    # To be backwards compatible during the renaming don't make this
    # method to be 'abstractmethod', so that existing code that
    # doesn't implement it continues to work.
    @classmethod
    async def dequeue(
        cls,
        context: IMPORT_reboot_aio_contexts.WorkflowContext,
        request: Queue.DequeueRequest,
    ) -> Queue.DequeueResponse:
        raise NotImplementedError

    # For 'rbt.std.collections.queue.v1.QueueMethods.TryDequeue'.
    # To be backwards compatible during the renaming don't make this
    # method to be 'abstractmethod', so that new code that
    # doesn't implement it continues to work.
    # TODO: make it abstractmethod when renaming is done.
    async def TryDequeue(
        self,
        context: IMPORT_reboot_aio_contexts.TransactionContext,
        request: Queue.TryDequeueRequest,
    ) -> Queue.TryDequeueResponse:
        # During the migration from 'PascalCase' to 'snake_case' method
        # naming in Python servicers, we call the 'snake_case' version
        # by default, so new names will do the correct thing making the
        # code to be backwards compatible for some time and if a servicer
        # overrides the 'PascalCase' version - it will override that
        # method and will just work.
        return await self.try_dequeue(
            context,
            request,
        )

    # To be backwards compatible during the renaming don't make this
    # method to be 'abstractmethod', so that existing code that
    # doesn't implement it continues to work.
    async def try_dequeue(
        self,
        context: IMPORT_reboot_aio_contexts.TransactionContext,
        request: Queue.TryDequeueRequest,
    ) -> Queue.TryDequeueResponse:
        raise NotImplementedError

    # For 'rbt.std.collections.queue.v1.QueueMethods.Empty'.
    # To be backwards compatible during the renaming don't make this
    # method to be 'abstractmethod', so that new code that
    # doesn't implement it continues to work.
    # TODO: make it abstractmethod when renaming is done.
    async def Empty(
        self,
        context: IMPORT_reboot_aio_contexts.ReaderContext,
        request: Queue.EmptyRequest,
    ) -> Queue.EmptyResponse:
        # During the migration from 'PascalCase' to 'snake_case' method
        # naming in Python servicers, we call the 'snake_case' version
        # by default, so new names will do the correct thing making the
        # code to be backwards compatible for some time and if a servicer
        # overrides the 'PascalCase' version - it will override that
        # method and will just work.
        return await self.empty(
            context,
            request,
        )

    # To be backwards compatible during the renaming don't make this
    # method to be 'abstractmethod', so that existing code that
    # doesn't implement it continues to work.
    async def empty(
        self,
        context: IMPORT_reboot_aio_contexts.ReaderContext,
        request: Queue.EmptyRequest,
    ) -> Queue.EmptyResponse:
        raise NotImplementedError


    # For 'rbt.std.collections.queue.v1.QueueMethods.Enqueue'.
    async def _Enqueue(
        self,
        context: IMPORT_reboot_aio_contexts.TransactionContext,
        state: Queue.State,
        request: rbt.std.collections.queue.v1.queue_pb2.EnqueueRequest,
    ) -> rbt.std.collections.queue.v1.queue_pb2.EnqueueResponse:
        # We should have an asyncio task and thus context per request,
        # let's confirm this assumption by making sure that
        # `_state is None`.
        assert QueueServicer._state.get() is None
        QueueServicer._state.set(state)
        try:
            # Wrap the call to the developer's method in a `span` so that it
            # is traced using its fully-qualified Python name.
            instance = self._instance(context.state_id)
            with IMPORT_reboot_aio_tracing.span(
                    state_name=f"rbt.std.collections.queue.v1.Queue('{context.state_id}')",
                    span_name=f"{IMPORT_reboot_aio_tracing.qualified_type_name(instance)}.Enqueue()",
                    level=IMPORT_reboot_aio_tracing.TraceLevel.CUSTOMER,
                    python_specific=True,
            ):
                typed_request = QueueEnqueueRequestFromProto(request)

                return QueueEnqueueResponseToProto(
                    await instance.Enqueue(
                        context,
                        typed_request,
                    )
                )
        finally:
            QueueServicer._state.set(None)

    # For 'rbt.std.collections.queue.v1.QueueMethods.Dequeue'.
    async def _Dequeue(
        self,
        context: IMPORT_reboot_aio_contexts.WorkflowContext,
        request: rbt.std.collections.queue.v1.queue_pb2.DequeueRequest,
    ) -> rbt.std.collections.queue.v1.queue_pb2.DequeueResponse:
        # Wrap the call to the developer's method in a `span` so that it
        # is traced using its fully-qualified Python name.
        instance = self._instance(context.state_id)
        with IMPORT_reboot_aio_tracing.span(
                state_name=f"rbt.std.collections.queue.v1.Queue('{context.state_id}')",
                span_name=f"{IMPORT_reboot_aio_tracing.qualified_type_name(instance)}.Dequeue()",
                level=IMPORT_reboot_aio_tracing.TraceLevel.CUSTOMER,
                python_specific=True,
        ):
            typed_request = QueueDequeueRequestFromProto(request)

            return QueueDequeueResponseToProto(
                await instance.Dequeue(
                    context,
                    typed_request,
                )
            )

    # For 'rbt.std.collections.queue.v1.QueueMethods.TryDequeue'.
    async def _TryDequeue(
        self,
        context: IMPORT_reboot_aio_contexts.TransactionContext,
        state: Queue.State,
        request: rbt.std.collections.queue.v1.queue_pb2.DequeueRequest,
    ) -> rbt.std.collections.queue.v1.queue_pb2.DequeueResponse:
        # We should have an asyncio task and thus context per request,
        # let's confirm this assumption by making sure that
        # `_state is None`.
        assert QueueServicer._state.get() is None
        QueueServicer._state.set(state)
        try:
            # Wrap the call to the developer's method in a `span` so that it
            # is traced using its fully-qualified Python name.
            instance = self._instance(context.state_id)
            with IMPORT_reboot_aio_tracing.span(
                    state_name=f"rbt.std.collections.queue.v1.Queue('{context.state_id}')",
                    span_name=f"{IMPORT_reboot_aio_tracing.qualified_type_name(instance)}.TryDequeue()",
                    level=IMPORT_reboot_aio_tracing.TraceLevel.CUSTOMER,
                    python_specific=True,
            ):
                typed_request = QueueTryDequeueRequestFromProto(request)

                return QueueTryDequeueResponseToProto(
                    await instance.TryDequeue(
                        context,
                        typed_request,
                    )
                )
        finally:
            QueueServicer._state.set(None)

    # For 'rbt.std.collections.queue.v1.QueueMethods.Empty'.
    async def _Empty(
        self,
        context: IMPORT_reboot_aio_contexts.ReaderContext,
        state: Queue.State,
        request: rbt.std.collections.queue.v1.queue_pb2.EmptyRequest,
    ) -> rbt.std.collections.queue.v1.queue_pb2.EmptyResponse:
        # We should have an asyncio task and thus context per request,
        # let's confirm this assumption by making sure that
        # `_state is None`.
        assert QueueServicer._state.get() is None
        QueueServicer._state.set(state)
        try:
            # Wrap the call to the developer's method in a `span` so that it
            # is traced using its fully-qualified Python name.
            instance = self._instance(context.state_id)
            with IMPORT_reboot_aio_tracing.span(
                    state_name=f"rbt.std.collections.queue.v1.Queue('{context.state_id}')",
                    span_name=f"{IMPORT_reboot_aio_tracing.qualified_type_name(instance)}.Empty()",
                    level=IMPORT_reboot_aio_tracing.TraceLevel.CUSTOMER,
                    python_specific=True,
            ):
                typed_request = QueueEmptyRequestFromProto(request)

                return QueueEmptyResponseToProto(
                    await instance.Empty(
                        context,
                        typed_request,
                    )
                )
        finally:
            QueueServicer._state.set(None)



############################ Clients ############################
# The main developer-facing entrypoints for any Reboot type. Relevant to both
# clients and servicers (who use it to find the right servicer base types, as well
# as often being clients themselves).

# Attach an explicit time time zone to "naive" `datetime` objects. A "naive" `datetime` doesn't have a
# time zone. Such objects are typically interpreted as representing local time, but could be confused
# for objects representing UTC. This helper function disambiguates by explicitly attaching the local
# time zone to `datetime` objects that don't already have an explicit time zone. If the `datetime` object
# is already timezone-aware, we still convert it to our custom `DateTimeWithTimeZone` type.
def ensure_has_timezone(
    *,
    when: IMPORT_typing.Optional[IMPORT_datetime_datetime | IMPORT_datetime_timedelta] = None,
) -> IMPORT_typing.Optional[IMPORT_reboot_time_DateTimeWithTimeZone | IMPORT_datetime_timedelta]:
    if isinstance(when, IMPORT_datetime_datetime):
        return IMPORT_reboot_time_DateTimeWithTimeZone.from_datetime(when)
    return when

Queue_ScheduleTypeVar = IMPORT_typing.TypeVar('Queue_ScheduleTypeVar', 'Queue.WeakReference._Schedule', 'Queue.WeakReference._WriterSchedule')
Queue_IdempotentlyScheduleTypeVar = IMPORT_typing.TypeVar('Queue_IdempotentlyScheduleTypeVar', 'Queue.WeakReference._Schedule', 'Queue.WeakReference._WriterSchedule')

Queue_UntilCallableType = IMPORT_typing.TypeVar('Queue_UntilCallableType')

class QueueSingleton:
    Servicer: IMPORT_typing.TypeAlias = QueueSingletonServicer


class Queue:


    Servicer: IMPORT_typing.TypeAlias = QueueServicer

    singleton: IMPORT_typing.TypeAlias = QueueSingleton

    Effects: IMPORT_typing.TypeAlias = QueueBaseServicer.Effects

    Authorizer: IMPORT_typing.TypeAlias = QueueAuthorizer

    State: IMPORT_typing.TypeAlias = rbt.std.collections.queue.v1.queue_pb2.Queue

    EnqueueRequest: IMPORT_typing.TypeAlias = rbt.std.collections.queue.v1.queue_pb2.EnqueueRequest
    EnqueueResponse: IMPORT_typing.TypeAlias = rbt.std.collections.queue.v1.queue_pb2.EnqueueResponse

    DequeueRequest: IMPORT_typing.TypeAlias = rbt.std.collections.queue.v1.queue_pb2.DequeueRequest
    DequeueResponse: IMPORT_typing.TypeAlias = rbt.std.collections.queue.v1.queue_pb2.DequeueResponse

    TryDequeueRequest: IMPORT_typing.TypeAlias = rbt.std.collections.queue.v1.queue_pb2.DequeueRequest
    TryDequeueResponse: IMPORT_typing.TypeAlias = rbt.std.collections.queue.v1.queue_pb2.DequeueResponse

    EmptyRequest: IMPORT_typing.TypeAlias = rbt.std.collections.queue.v1.queue_pb2.EmptyRequest
    EmptyResponse: IMPORT_typing.TypeAlias = rbt.std.collections.queue.v1.queue_pb2.EmptyResponse

    __state_type_name__ = IMPORT_reboot_aio_types.StateTypeName("rbt.std.collections.queue.v1.Queue")

    class EnqueueTask:
        """Represents a scheduled task running for the
        state. Note that this is not a coroutine because we are trying
        to convey the semantics that the task is already running (or
        will soon be).
        """

        @classmethod
        def retrieve(
            cls,
            context: IMPORT_reboot_aio_contexts.Context | IMPORT_reboot_aio_external.ExternalContext,
            *,
            task_id: IMPORT_rbt_v1alpha1.tasks_pb2.TaskId,
        ):
            return cls(context, task_id=task_id)

        def __init__(
            self,
            context: IMPORT_reboot_aio_contexts.Context | IMPORT_reboot_aio_external.ExternalContext,
            *,
            task_id: IMPORT_rbt_v1alpha1.tasks_pb2.TaskId,
        ) -> None:
            # Depending on the context type (inside or outside a Reboot application)
            # we may or may not know the application ID. If we don't know it, then
            # the `ExternalContext.gateway` will determine it.
            #
            # TODO: in the future we expect to support cross-application calls, in
            #       which case the developer may explicitly pass in an application ID
            #       here.
            self._application_id: IMPORT_typing.Optional[IMPORT_reboot_aio_types.ApplicationId] = None
            if isinstance(context, IMPORT_reboot_aio_contexts.Context):
                self._application_id = context.application_id
            self._channel_manager = context.channel_manager
            self._task_id = task_id

        @property
        def task_id(self) -> IMPORT_rbt_v1alpha1.tasks_pb2.TaskId:
            return self._task_id

        def __await__(self) -> IMPORT_typing.Generator[None, None, Queue.EnqueueResponse]:
            """Awaits for task to finish and returns its response."""
            async def wait_for_task() -> rbt.std.collections.queue.v1.queue_pb2.EnqueueResponse:
                channel = self._channel_manager.get_channel_to_state(
                    IMPORT_reboot_aio_types.StateTypeName(self._task_id.state_type),
                    IMPORT_reboot_aio_types.StateRef(self._task_id.state_ref),
                )

                stub = IMPORT_rbt_v1alpha1.tasks_pb2_grpc.TasksStub(channel)

                try:
                    call = IMPORT_reboot_aio_stubs.UnaryRetriedCall(
                        call=None,  # `RetriedCall` can create the call itself.
                        stub_method=stub.Wait,
                        method_name="Wait",
                        request=IMPORT_rbt_v1alpha1.tasks_pb2.WaitRequest(task_id=self._task_id),
                        metadata=IMPORT_reboot_aio_headers.Headers(
                            state_ref=IMPORT_reboot_aio_types.StateRef(self._task_id.state_ref),
                            application_id=self._application_id,
                        ).to_grpc_metadata(),
                        aborted_type=IMPORT_rebootdev.aio.aborted.SystemAborted,
                    )

                    wait_for_task_response = await call
                except IMPORT_rebootdev.aio.aborted.SystemAborted as error:
                    if error.code == IMPORT_grpc.StatusCode.NOT_FOUND:
                        raise IMPORT_rebootdev.aio.aborted.SystemAborted(
                            IMPORT_rbt_v1alpha1.errors_pb2.UnknownTask()
                        ) from None

                    raise
                else:
                    response_or_error: IMPORT_typing.Optional[IMPORT_google_protobuf_any_pb2.Any] = None
                    is_error = False

                    if wait_for_task_response.response_or_error.WhichOneof("response_or_error") == "response":
                        response_or_error = wait_for_task_response.response_or_error.response
                    else:
                        is_error = True
                        response_or_error = wait_for_task_response.response_or_error.error

                    assert response_or_error is not None
                    assert response_or_error.TypeName() != ""

                    response = rbt.std.collections.queue.v1.queue_pb2.EnqueueResponse()

                    if (
                        not is_error and response_or_error.TypeName() != response.DESCRIPTOR.full_name
                    ):
                        raise IMPORT_rebootdev.aio.aborted.SystemAborted(
                            IMPORT_rbt_v1alpha1.errors_pb2.InvalidArgument(),
                            message=
                            f"task with UUID {IMPORT_uuid.UUID(bytes=self._task_id.task_uuid)} "
                            f"has a response of type '{response_or_error.TypeName()}' "
                            "but expecting type 'rbt.std.collections.queue.v1.queue_pb2.EnqueueResponse'; "
                            "are you waiting on a task of the correct method?",
                        ) from None

                    if is_error:
                        aborted_type = Queue.EnqueueAborted

                        # In Reboot >= 0.40.2 we expect the error to be a `google.rpc.Status`.
                        if response_or_error.Is(IMPORT_google_rpc_status_pb2.Status.DESCRIPTOR):
                            status = IMPORT_google_rpc_status_pb2.Status()
                            response_or_error.Unpack(status)
                            raise aborted_type.from_status(status)

                        # In Reboot < 0.40.2 workflows throwing declared errors behaved poorly;
                        # we don't aim to emulate its behavior. Indicate that we don't know the
                        # reason for the abort.
                        raise IMPORT_rebootdev.aio.aborted.SystemAborted(
                            IMPORT_rbt_v1alpha1.errors_pb2.Unknown(),
                        )

                    else:
                        response_or_error.Unpack(response)
                        return QueueEnqueueResponseFromProto(response)

            return wait_for_task().__await__()


    class EnqueueAborted(IMPORT_rebootdev.aio.aborted.Aborted):


        Error = IMPORT_typing.Union[
            IMPORT_rebootdev.aio.aborted.GrpcError,
            IMPORT_rebootdev.aio.aborted.RebootError,
        ]

        METHOD_ERROR_TYPES: list[type[IMPORT_google_protobuf_message.Message]] = [
        ]

        ERROR_TYPES: list[type[IMPORT_google_protobuf_message.Message]] = (
            METHOD_ERROR_TYPES +
            IMPORT_rebootdev.aio.aborted.GRPC_ERROR_TYPES +
            IMPORT_rebootdev.aio.aborted.REBOOT_ERROR_TYPES
        )

        _error: Error
        _code: IMPORT_grpc.StatusCode
        _message: IMPORT_typing.Optional[str]

        def __init__(
            self,
            error:  IMPORT_rebootdev.aio.aborted.GrpcError,
            *,
            message: IMPORT_typing.Optional[str] = None,
            # Do not set this value when constructing in order to
            # raise. This is only used internally when constructing
            # from aborted calls.
            error_types: IMPORT_typing.Sequence[type[Error]] = (
                METHOD_ERROR_TYPES + IMPORT_rebootdev.aio.aborted.GRPC_ERROR_TYPES
            ),
        ):
            super().__init__()

            IMPORT_reboot_aio_types.assert_type(error, error_types)

            self._error = error

            code = self.grpc_status_code_from_error(self._error)

            if code is None:
                # Must be a Reboot specific or declared method error.
                code = IMPORT_grpc.StatusCode.ABORTED

            self._code = code

            self._message = message

        @property
        def error(self) -> Error:
            return self._error

        @property
        def code(self) -> IMPORT_grpc.StatusCode:
            return self._code

        @property
        def message(self) -> IMPORT_typing.Optional[str]:
            return self._message

        @classmethod
        def from_status(cls, status: IMPORT_google_rpc_status_pb2.Status):
            error = cls.error_from_google_rpc_status_details(
                status,
                cls.ERROR_TYPES,
            )

            message = status.message if len(status.message) > 0 else None

            if error is not None:
                return cls(error, message=message, error_types=cls.ERROR_TYPES)

            error = cls.error_from_google_rpc_status_code(status)

            assert error is not None

            # TODO(benh): also consider getting the type names from
            # `status.details` and including that in `message` to make
            # debugging easier.

            return cls(error, message=message)

        @classmethod
        def from_grpc_aio_rpc_error(cls, aio_rpc_error: IMPORT_grpc.aio.AioRpcError):
            return cls(
                cls.error_from_grpc_aio_rpc_error(aio_rpc_error),
                message=aio_rpc_error.details(),
            )

        @classmethod
        def is_declared_error(cls, message: IMPORT_google_protobuf_message.Message) -> bool:
            return False

    class DequeueTask:
        """Represents a scheduled task running for the
        state. Note that this is not a coroutine because we are trying
        to convey the semantics that the task is already running (or
        will soon be).
        """

        @classmethod
        def retrieve(
            cls,
            context: IMPORT_reboot_aio_contexts.Context | IMPORT_reboot_aio_external.ExternalContext,
            *,
            task_id: IMPORT_rbt_v1alpha1.tasks_pb2.TaskId,
        ):
            return cls(context, task_id=task_id)

        def __init__(
            self,
            context: IMPORT_reboot_aio_contexts.Context | IMPORT_reboot_aio_external.ExternalContext,
            *,
            task_id: IMPORT_rbt_v1alpha1.tasks_pb2.TaskId,
        ) -> None:
            # Depending on the context type (inside or outside a Reboot application)
            # we may or may not know the application ID. If we don't know it, then
            # the `ExternalContext.gateway` will determine it.
            #
            # TODO: in the future we expect to support cross-application calls, in
            #       which case the developer may explicitly pass in an application ID
            #       here.
            self._application_id: IMPORT_typing.Optional[IMPORT_reboot_aio_types.ApplicationId] = None
            if isinstance(context, IMPORT_reboot_aio_contexts.Context):
                self._application_id = context.application_id
            self._channel_manager = context.channel_manager
            self._task_id = task_id

        @property
        def task_id(self) -> IMPORT_rbt_v1alpha1.tasks_pb2.TaskId:
            return self._task_id

        def __await__(self) -> IMPORT_typing.Generator[None, None, Queue.DequeueResponse]:
            """Awaits for task to finish and returns its response."""
            async def wait_for_task() -> rbt.std.collections.queue.v1.queue_pb2.DequeueResponse:
                channel = self._channel_manager.get_channel_to_state(
                    IMPORT_reboot_aio_types.StateTypeName(self._task_id.state_type),
                    IMPORT_reboot_aio_types.StateRef(self._task_id.state_ref),
                )

                stub = IMPORT_rbt_v1alpha1.tasks_pb2_grpc.TasksStub(channel)

                try:
                    call = IMPORT_reboot_aio_stubs.UnaryRetriedCall(
                        call=None,  # `RetriedCall` can create the call itself.
                        stub_method=stub.Wait,
                        method_name="Wait",
                        request=IMPORT_rbt_v1alpha1.tasks_pb2.WaitRequest(task_id=self._task_id),
                        metadata=IMPORT_reboot_aio_headers.Headers(
                            state_ref=IMPORT_reboot_aio_types.StateRef(self._task_id.state_ref),
                            application_id=self._application_id,
                        ).to_grpc_metadata(),
                        aborted_type=IMPORT_rebootdev.aio.aborted.SystemAborted,
                    )

                    wait_for_task_response = await call
                except IMPORT_rebootdev.aio.aborted.SystemAborted as error:
                    if error.code == IMPORT_grpc.StatusCode.NOT_FOUND:
                        raise IMPORT_rebootdev.aio.aborted.SystemAborted(
                            IMPORT_rbt_v1alpha1.errors_pb2.UnknownTask()
                        ) from None

                    raise
                else:
                    response_or_error: IMPORT_typing.Optional[IMPORT_google_protobuf_any_pb2.Any] = None
                    is_error = False

                    if wait_for_task_response.response_or_error.WhichOneof("response_or_error") == "response":
                        response_or_error = wait_for_task_response.response_or_error.response
                    else:
                        is_error = True
                        response_or_error = wait_for_task_response.response_or_error.error

                    assert response_or_error is not None
                    assert response_or_error.TypeName() != ""

                    response = rbt.std.collections.queue.v1.queue_pb2.DequeueResponse()

                    if (
                        not is_error and response_or_error.TypeName() != response.DESCRIPTOR.full_name
                    ):
                        raise IMPORT_rebootdev.aio.aborted.SystemAborted(
                            IMPORT_rbt_v1alpha1.errors_pb2.InvalidArgument(),
                            message=
                            f"task with UUID {IMPORT_uuid.UUID(bytes=self._task_id.task_uuid)} "
                            f"has a response of type '{response_or_error.TypeName()}' "
                            "but expecting type 'rbt.std.collections.queue.v1.queue_pb2.DequeueResponse'; "
                            "are you waiting on a task of the correct method?",
                        ) from None

                    if is_error:
                        aborted_type = Queue.DequeueAborted

                        # In Reboot >= 0.40.2 we expect the error to be a `google.rpc.Status`.
                        if response_or_error.Is(IMPORT_google_rpc_status_pb2.Status.DESCRIPTOR):
                            status = IMPORT_google_rpc_status_pb2.Status()
                            response_or_error.Unpack(status)
                            raise aborted_type.from_status(status)

                        # In Reboot < 0.40.2 workflows throwing declared errors behaved poorly;
                        # we don't aim to emulate its behavior. Indicate that we don't know the
                        # reason for the abort.
                        raise IMPORT_rebootdev.aio.aborted.SystemAborted(
                            IMPORT_rbt_v1alpha1.errors_pb2.Unknown(),
                        )

                    else:
                        response_or_error.Unpack(response)
                        return QueueDequeueResponseFromProto(response)

            return wait_for_task().__await__()


    class DequeueAborted(IMPORT_rebootdev.aio.aborted.Aborted):


        Error = IMPORT_typing.Union[
            IMPORT_rebootdev.aio.aborted.GrpcError,
            IMPORT_rebootdev.aio.aborted.RebootError,
        ]

        METHOD_ERROR_TYPES: list[type[IMPORT_google_protobuf_message.Message]] = [
        ]

        ERROR_TYPES: list[type[IMPORT_google_protobuf_message.Message]] = (
            METHOD_ERROR_TYPES +
            IMPORT_rebootdev.aio.aborted.GRPC_ERROR_TYPES +
            IMPORT_rebootdev.aio.aborted.REBOOT_ERROR_TYPES
        )

        _error: Error
        _code: IMPORT_grpc.StatusCode
        _message: IMPORT_typing.Optional[str]

        def __init__(
            self,
            error:  IMPORT_rebootdev.aio.aborted.GrpcError,
            *,
            message: IMPORT_typing.Optional[str] = None,
            # Do not set this value when constructing in order to
            # raise. This is only used internally when constructing
            # from aborted calls.
            error_types: IMPORT_typing.Sequence[type[Error]] = (
                METHOD_ERROR_TYPES + IMPORT_rebootdev.aio.aborted.GRPC_ERROR_TYPES
            ),
        ):
            super().__init__()

            IMPORT_reboot_aio_types.assert_type(error, error_types)

            self._error = error

            code = self.grpc_status_code_from_error(self._error)

            if code is None:
                # Must be a Reboot specific or declared method error.
                code = IMPORT_grpc.StatusCode.ABORTED

            self._code = code

            self._message = message

        @property
        def error(self) -> Error:
            return self._error

        @property
        def code(self) -> IMPORT_grpc.StatusCode:
            return self._code

        @property
        def message(self) -> IMPORT_typing.Optional[str]:
            return self._message

        @classmethod
        def from_status(cls, status: IMPORT_google_rpc_status_pb2.Status):
            error = cls.error_from_google_rpc_status_details(
                status,
                cls.ERROR_TYPES,
            )

            message = status.message if len(status.message) > 0 else None

            if error is not None:
                return cls(error, message=message, error_types=cls.ERROR_TYPES)

            error = cls.error_from_google_rpc_status_code(status)

            assert error is not None

            # TODO(benh): also consider getting the type names from
            # `status.details` and including that in `message` to make
            # debugging easier.

            return cls(error, message=message)

        @classmethod
        def from_grpc_aio_rpc_error(cls, aio_rpc_error: IMPORT_grpc.aio.AioRpcError):
            return cls(
                cls.error_from_grpc_aio_rpc_error(aio_rpc_error),
                message=aio_rpc_error.details(),
            )

        @classmethod
        def is_declared_error(cls, message: IMPORT_google_protobuf_message.Message) -> bool:
            return False

    class TryDequeueTask:
        """Represents a scheduled task running for the
        state. Note that this is not a coroutine because we are trying
        to convey the semantics that the task is already running (or
        will soon be).
        """

        @classmethod
        def retrieve(
            cls,
            context: IMPORT_reboot_aio_contexts.Context | IMPORT_reboot_aio_external.ExternalContext,
            *,
            task_id: IMPORT_rbt_v1alpha1.tasks_pb2.TaskId,
        ):
            return cls(context, task_id=task_id)

        def __init__(
            self,
            context: IMPORT_reboot_aio_contexts.Context | IMPORT_reboot_aio_external.ExternalContext,
            *,
            task_id: IMPORT_rbt_v1alpha1.tasks_pb2.TaskId,
        ) -> None:
            # Depending on the context type (inside or outside a Reboot application)
            # we may or may not know the application ID. If we don't know it, then
            # the `ExternalContext.gateway` will determine it.
            #
            # TODO: in the future we expect to support cross-application calls, in
            #       which case the developer may explicitly pass in an application ID
            #       here.
            self._application_id: IMPORT_typing.Optional[IMPORT_reboot_aio_types.ApplicationId] = None
            if isinstance(context, IMPORT_reboot_aio_contexts.Context):
                self._application_id = context.application_id
            self._channel_manager = context.channel_manager
            self._task_id = task_id

        @property
        def task_id(self) -> IMPORT_rbt_v1alpha1.tasks_pb2.TaskId:
            return self._task_id

        def __await__(self) -> IMPORT_typing.Generator[None, None, Queue.TryDequeueResponse]:
            """Awaits for task to finish and returns its response."""
            async def wait_for_task() -> rbt.std.collections.queue.v1.queue_pb2.DequeueResponse:
                channel = self._channel_manager.get_channel_to_state(
                    IMPORT_reboot_aio_types.StateTypeName(self._task_id.state_type),
                    IMPORT_reboot_aio_types.StateRef(self._task_id.state_ref),
                )

                stub = IMPORT_rbt_v1alpha1.tasks_pb2_grpc.TasksStub(channel)

                try:
                    call = IMPORT_reboot_aio_stubs.UnaryRetriedCall(
                        call=None,  # `RetriedCall` can create the call itself.
                        stub_method=stub.Wait,
                        method_name="Wait",
                        request=IMPORT_rbt_v1alpha1.tasks_pb2.WaitRequest(task_id=self._task_id),
                        metadata=IMPORT_reboot_aio_headers.Headers(
                            state_ref=IMPORT_reboot_aio_types.StateRef(self._task_id.state_ref),
                            application_id=self._application_id,
                        ).to_grpc_metadata(),
                        aborted_type=IMPORT_rebootdev.aio.aborted.SystemAborted,
                    )

                    wait_for_task_response = await call
                except IMPORT_rebootdev.aio.aborted.SystemAborted as error:
                    if error.code == IMPORT_grpc.StatusCode.NOT_FOUND:
                        raise IMPORT_rebootdev.aio.aborted.SystemAborted(
                            IMPORT_rbt_v1alpha1.errors_pb2.UnknownTask()
                        ) from None

                    raise
                else:
                    response_or_error: IMPORT_typing.Optional[IMPORT_google_protobuf_any_pb2.Any] = None
                    is_error = False

                    if wait_for_task_response.response_or_error.WhichOneof("response_or_error") == "response":
                        response_or_error = wait_for_task_response.response_or_error.response
                    else:
                        is_error = True
                        response_or_error = wait_for_task_response.response_or_error.error

                    assert response_or_error is not None
                    assert response_or_error.TypeName() != ""

                    response = rbt.std.collections.queue.v1.queue_pb2.DequeueResponse()

                    if (
                        not is_error and response_or_error.TypeName() != response.DESCRIPTOR.full_name
                    ):
                        raise IMPORT_rebootdev.aio.aborted.SystemAborted(
                            IMPORT_rbt_v1alpha1.errors_pb2.InvalidArgument(),
                            message=
                            f"task with UUID {IMPORT_uuid.UUID(bytes=self._task_id.task_uuid)} "
                            f"has a response of type '{response_or_error.TypeName()}' "
                            "but expecting type 'rbt.std.collections.queue.v1.queue_pb2.DequeueResponse'; "
                            "are you waiting on a task of the correct method?",
                        ) from None

                    if is_error:
                        aborted_type = Queue.TryDequeueAborted

                        # In Reboot >= 0.40.2 we expect the error to be a `google.rpc.Status`.
                        if response_or_error.Is(IMPORT_google_rpc_status_pb2.Status.DESCRIPTOR):
                            status = IMPORT_google_rpc_status_pb2.Status()
                            response_or_error.Unpack(status)
                            raise aborted_type.from_status(status)

                        # In Reboot < 0.40.2 workflows throwing declared errors behaved poorly;
                        # we don't aim to emulate its behavior. Indicate that we don't know the
                        # reason for the abort.
                        raise IMPORT_rebootdev.aio.aborted.SystemAborted(
                            IMPORT_rbt_v1alpha1.errors_pb2.Unknown(),
                        )

                    else:
                        response_or_error.Unpack(response)
                        return QueueTryDequeueResponseFromProto(response)

            return wait_for_task().__await__()


    class TryDequeueAborted(IMPORT_rebootdev.aio.aborted.Aborted):


        Error = IMPORT_typing.Union[
            IMPORT_rebootdev.aio.aborted.GrpcError,
            IMPORT_rebootdev.aio.aborted.RebootError,
        ]

        METHOD_ERROR_TYPES: list[type[IMPORT_google_protobuf_message.Message]] = [
        ]

        ERROR_TYPES: list[type[IMPORT_google_protobuf_message.Message]] = (
            METHOD_ERROR_TYPES +
            IMPORT_rebootdev.aio.aborted.GRPC_ERROR_TYPES +
            IMPORT_rebootdev.aio.aborted.REBOOT_ERROR_TYPES
        )

        _error: Error
        _code: IMPORT_grpc.StatusCode
        _message: IMPORT_typing.Optional[str]

        def __init__(
            self,
            error:  IMPORT_rebootdev.aio.aborted.GrpcError,
            *,
            message: IMPORT_typing.Optional[str] = None,
            # Do not set this value when constructing in order to
            # raise. This is only used internally when constructing
            # from aborted calls.
            error_types: IMPORT_typing.Sequence[type[Error]] = (
                METHOD_ERROR_TYPES + IMPORT_rebootdev.aio.aborted.GRPC_ERROR_TYPES
            ),
        ):
            super().__init__()

            IMPORT_reboot_aio_types.assert_type(error, error_types)

            self._error = error

            code = self.grpc_status_code_from_error(self._error)

            if code is None:
                # Must be a Reboot specific or declared method error.
                code = IMPORT_grpc.StatusCode.ABORTED

            self._code = code

            self._message = message

        @property
        def error(self) -> Error:
            return self._error

        @property
        def code(self) -> IMPORT_grpc.StatusCode:
            return self._code

        @property
        def message(self) -> IMPORT_typing.Optional[str]:
            return self._message

        @classmethod
        def from_status(cls, status: IMPORT_google_rpc_status_pb2.Status):
            error = cls.error_from_google_rpc_status_details(
                status,
                cls.ERROR_TYPES,
            )

            message = status.message if len(status.message) > 0 else None

            if error is not None:
                return cls(error, message=message, error_types=cls.ERROR_TYPES)

            error = cls.error_from_google_rpc_status_code(status)

            assert error is not None

            # TODO(benh): also consider getting the type names from
            # `status.details` and including that in `message` to make
            # debugging easier.

            return cls(error, message=message)

        @classmethod
        def from_grpc_aio_rpc_error(cls, aio_rpc_error: IMPORT_grpc.aio.AioRpcError):
            return cls(
                cls.error_from_grpc_aio_rpc_error(aio_rpc_error),
                message=aio_rpc_error.details(),
            )

        @classmethod
        def is_declared_error(cls, message: IMPORT_google_protobuf_message.Message) -> bool:
            return False

    class EmptyTask:
        """Represents a scheduled task running for the
        state. Note that this is not a coroutine because we are trying
        to convey the semantics that the task is already running (or
        will soon be).
        """

        @classmethod
        def retrieve(
            cls,
            context: IMPORT_reboot_aio_contexts.Context | IMPORT_reboot_aio_external.ExternalContext,
            *,
            task_id: IMPORT_rbt_v1alpha1.tasks_pb2.TaskId,
        ):
            return cls(context, task_id=task_id)

        def __init__(
            self,
            context: IMPORT_reboot_aio_contexts.Context | IMPORT_reboot_aio_external.ExternalContext,
            *,
            task_id: IMPORT_rbt_v1alpha1.tasks_pb2.TaskId,
        ) -> None:
            # Depending on the context type (inside or outside a Reboot application)
            # we may or may not know the application ID. If we don't know it, then
            # the `ExternalContext.gateway` will determine it.
            #
            # TODO: in the future we expect to support cross-application calls, in
            #       which case the developer may explicitly pass in an application ID
            #       here.
            self._application_id: IMPORT_typing.Optional[IMPORT_reboot_aio_types.ApplicationId] = None
            if isinstance(context, IMPORT_reboot_aio_contexts.Context):
                self._application_id = context.application_id
            self._channel_manager = context.channel_manager
            self._task_id = task_id

        @property
        def task_id(self) -> IMPORT_rbt_v1alpha1.tasks_pb2.TaskId:
            return self._task_id

        def __await__(self) -> IMPORT_typing.Generator[None, None, Queue.EmptyResponse]:
            """Awaits for task to finish and returns its response."""
            async def wait_for_task() -> rbt.std.collections.queue.v1.queue_pb2.EmptyResponse:
                channel = self._channel_manager.get_channel_to_state(
                    IMPORT_reboot_aio_types.StateTypeName(self._task_id.state_type),
                    IMPORT_reboot_aio_types.StateRef(self._task_id.state_ref),
                )

                stub = IMPORT_rbt_v1alpha1.tasks_pb2_grpc.TasksStub(channel)

                try:
                    call = IMPORT_reboot_aio_stubs.UnaryRetriedCall(
                        call=None,  # `RetriedCall` can create the call itself.
                        stub_method=stub.Wait,
                        method_name="Wait",
                        request=IMPORT_rbt_v1alpha1.tasks_pb2.WaitRequest(task_id=self._task_id),
                        metadata=IMPORT_reboot_aio_headers.Headers(
                            state_ref=IMPORT_reboot_aio_types.StateRef(self._task_id.state_ref),
                            application_id=self._application_id,
                        ).to_grpc_metadata(),
                        aborted_type=IMPORT_rebootdev.aio.aborted.SystemAborted,
                    )

                    wait_for_task_response = await call
                except IMPORT_rebootdev.aio.aborted.SystemAborted as error:
                    if error.code == IMPORT_grpc.StatusCode.NOT_FOUND:
                        raise IMPORT_rebootdev.aio.aborted.SystemAborted(
                            IMPORT_rbt_v1alpha1.errors_pb2.UnknownTask()
                        ) from None

                    raise
                else:
                    response_or_error: IMPORT_typing.Optional[IMPORT_google_protobuf_any_pb2.Any] = None
                    is_error = False

                    if wait_for_task_response.response_or_error.WhichOneof("response_or_error") == "response":
                        response_or_error = wait_for_task_response.response_or_error.response
                    else:
                        is_error = True
                        response_or_error = wait_for_task_response.response_or_error.error

                    assert response_or_error is not None
                    assert response_or_error.TypeName() != ""

                    response = rbt.std.collections.queue.v1.queue_pb2.EmptyResponse()

                    if (
                        not is_error and response_or_error.TypeName() != response.DESCRIPTOR.full_name
                    ):
                        raise IMPORT_rebootdev.aio.aborted.SystemAborted(
                            IMPORT_rbt_v1alpha1.errors_pb2.InvalidArgument(),
                            message=
                            f"task with UUID {IMPORT_uuid.UUID(bytes=self._task_id.task_uuid)} "
                            f"has a response of type '{response_or_error.TypeName()}' "
                            "but expecting type 'rbt.std.collections.queue.v1.queue_pb2.EmptyResponse'; "
                            "are you waiting on a task of the correct method?",
                        ) from None

                    if is_error:
                        aborted_type = Queue.EmptyAborted

                        # In Reboot >= 0.40.2 we expect the error to be a `google.rpc.Status`.
                        if response_or_error.Is(IMPORT_google_rpc_status_pb2.Status.DESCRIPTOR):
                            status = IMPORT_google_rpc_status_pb2.Status()
                            response_or_error.Unpack(status)
                            raise aborted_type.from_status(status)

                        # In Reboot < 0.40.2 workflows throwing declared errors behaved poorly;
                        # we don't aim to emulate its behavior. Indicate that we don't know the
                        # reason for the abort.
                        raise IMPORT_rebootdev.aio.aborted.SystemAborted(
                            IMPORT_rbt_v1alpha1.errors_pb2.Unknown(),
                        )

                    else:
                        response_or_error.Unpack(response)
                        return QueueEmptyResponseFromProto(response)

            return wait_for_task().__await__()


    class EmptyAborted(IMPORT_rebootdev.aio.aborted.Aborted):


        Error = IMPORT_typing.Union[
            IMPORT_rebootdev.aio.aborted.GrpcError,
            IMPORT_rebootdev.aio.aborted.RebootError,
        ]

        METHOD_ERROR_TYPES: list[type[IMPORT_google_protobuf_message.Message]] = [
        ]

        ERROR_TYPES: list[type[IMPORT_google_protobuf_message.Message]] = (
            METHOD_ERROR_TYPES +
            IMPORT_rebootdev.aio.aborted.GRPC_ERROR_TYPES +
            IMPORT_rebootdev.aio.aborted.REBOOT_ERROR_TYPES
        )

        _error: Error
        _code: IMPORT_grpc.StatusCode
        _message: IMPORT_typing.Optional[str]

        def __init__(
            self,
            error:  IMPORT_rebootdev.aio.aborted.GrpcError,
            *,
            message: IMPORT_typing.Optional[str] = None,
            # Do not set this value when constructing in order to
            # raise. This is only used internally when constructing
            # from aborted calls.
            error_types: IMPORT_typing.Sequence[type[Error]] = (
                METHOD_ERROR_TYPES + IMPORT_rebootdev.aio.aborted.GRPC_ERROR_TYPES
            ),
        ):
            super().__init__()

            IMPORT_reboot_aio_types.assert_type(error, error_types)

            self._error = error

            code = self.grpc_status_code_from_error(self._error)

            if code is None:
                # Must be a Reboot specific or declared method error.
                code = IMPORT_grpc.StatusCode.ABORTED

            self._code = code

            self._message = message

        @property
        def error(self) -> Error:
            return self._error

        @property
        def code(self) -> IMPORT_grpc.StatusCode:
            return self._code

        @property
        def message(self) -> IMPORT_typing.Optional[str]:
            return self._message

        @classmethod
        def from_status(cls, status: IMPORT_google_rpc_status_pb2.Status):
            error = cls.error_from_google_rpc_status_details(
                status,
                cls.ERROR_TYPES,
            )

            message = status.message if len(status.message) > 0 else None

            if error is not None:
                return cls(error, message=message, error_types=cls.ERROR_TYPES)

            error = cls.error_from_google_rpc_status_code(status)

            assert error is not None

            # TODO(benh): also consider getting the type names from
            # `status.details` and including that in `message` to make
            # debugging easier.

            return cls(error, message=message)

        @classmethod
        def from_grpc_aio_rpc_error(cls, aio_rpc_error: IMPORT_grpc.aio.AioRpcError):
            return cls(
                cls.error_from_grpc_aio_rpc_error(aio_rpc_error),
                message=aio_rpc_error.details(),
            )

        @classmethod
        def is_declared_error(cls, message: IMPORT_google_protobuf_message.Message) -> bool:
            return False


    class WeakReference(IMPORT_typing.Generic[Queue_ScheduleTypeVar]):

        _schedule_type: type[Queue_ScheduleTypeVar]

        def __init__(
            self,
            # When application ID is None, refers to a state within the application given by the context.
            application_id: IMPORT_typing.Optional[IMPORT_reboot_aio_types.ApplicationId],
            state_id: IMPORT_reboot_aio_types.StateId,
            *,
            schedule_type: type[Queue_ScheduleTypeVar],
            bearer_token: IMPORT_typing.Optional[str] = None,
            servicer: IMPORT_typing.Optional[QueueBaseServicer] = None,
        ):
            self._application_id = application_id
            self._state_ref = IMPORT_reboot_aio_types.StateRef.from_id(
              Queue.__state_type_name__,
              state_id,
            )
            self._schedule_type = schedule_type
            self._idempotency_manager: IMPORT_typing.Optional[IMPORT_reboot_aio_idempotency.IdempotencyManager] = None
            self._reader_stub: IMPORT_typing.Optional[QueueReaderStub] = None
            self._writer_stub: IMPORT_typing.Optional[QueueWriterStub] = None
            self._workflow_stub: IMPORT_typing.Optional[QueueWorkflowStub] = None
            self._tasks_stub: IMPORT_typing.Optional[QueueTasksStub] = None
            self._bearer_token = bearer_token
            self._servicer = servicer

        @property
        def state_id(self) -> IMPORT_reboot_aio_types.StateId:
            return self._state_ref.id

        def _reader(
            self,
            context: IMPORT_reboot_aio_contexts.ReaderContext | IMPORT_reboot_aio_contexts.WriterContext | IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
        ) -> QueueReaderStub:
            if self._reader_stub is None:
                self._reader_stub = QueueReaderStub(
                    context=context,
                    state_ref=self._state_ref,
                    bearer_token=self._bearer_token,
                )
            assert self._reader_stub is not None
            if self._idempotency_manager is None:
                self._idempotency_manager = context
            elif self._idempotency_manager != context:
                raise IMPORT_reboot_aio_call.MixedContextsError(
                    "This `WeakReference` for `Queue` with ID "
                    f"'{self.state_id}' has previously been used by a "
                    "different `Context`. That is not allowed. "
                    "Instead create a new `WeakReference` for every `Context` by calling "
                    f"`Queue.ref('{self.state_id}')`."
                )
            return self._reader_stub

        def _writer(
            self,
            context: IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
        ) -> QueueWriterStub:
            if self._writer_stub is None:
                self._writer_stub = QueueWriterStub(
                    context=context,
                    state_ref=self._state_ref,
                    bearer_token=self._bearer_token,
                )
            assert self._writer_stub is not None
            if self._idempotency_manager is None:
                self._idempotency_manager = context
            elif self._idempotency_manager != context:
                raise IMPORT_reboot_aio_call.MixedContextsError(
                    "This `WeakReference` for `Queue` with ID "
                    f"'{self.state_id}' has previously been used by a "
                    "different `Context`. That is not allowed. "
                    "Instead create a new `WeakReference` for every `Context` by calling "
                    f"`Queue.ref('{self.state_id}')`."
                )
            return self._writer_stub

        def _workflow(
            self,
            context: IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
        ) -> QueueWorkflowStub:
            if self._workflow_stub is None:
                self._workflow_stub = QueueWorkflowStub(
                    context=context,
                    state_ref=self._state_ref,
                    bearer_token=self._bearer_token,
                )
            assert self._workflow_stub is not None
            if self._idempotency_manager is None:
                self._idempotency_manager = context
            elif self._idempotency_manager != context:
                raise IMPORT_reboot_aio_call.MixedContextsError(
                    "This `WeakReference` for `Queue` with ID "
                    f"'{self.state_id}' has previously been used by a "
                    "different `Context`. That is not allowed. "
                    "Instead create a new `WeakReference` for every `Context` by calling "
                    f"`Queue.ref('{self.state_id}')`."
                )
            return self._workflow_stub

        def _tasks(
            self,
            context: IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
        ) -> QueueTasksStub:
            if self._tasks_stub is None:
                self._tasks_stub = QueueTasksStub(
                    context=context,
                    state_ref=self._state_ref,
                    bearer_token=self._bearer_token,
                )
            assert self._tasks_stub is not None
            if self._idempotency_manager is None:
                self._idempotency_manager = context
            elif self._idempotency_manager != context:
                raise IMPORT_reboot_aio_call.MixedContextsError(
                    "This `WeakReference` for `Queue` with ID "
                    f"'{self.state_id}' has previously been used by a "
                    "different `Context`. That is not allowed. "
                    "Instead create a new `WeakReference` for every `Context` by calling "
                    f"`Queue.ref('{self.state_id}')`."
                )
            return self._tasks_stub

        class _Reactively:

            def __init__(
                self,
                *,
                application_id: IMPORT_typing.Optional[IMPORT_reboot_aio_types.ApplicationId],
                state_ref: IMPORT_reboot_aio_types.StateRef,
                bearer_token: IMPORT_typing.Optional[str] = None,
            ):
                self._application_id = application_id
                self._state_ref = state_ref
                self._bearer_token = bearer_token

            @IMPORT_typing.overload
            async def Empty(
                __this__,
                __context__: IMPORT_reboot_aio_external.ExternalContext | IMPORT_reboot_aio_contexts.ReaderContext | IMPORT_reboot_aio_contexts.WorkflowContext,
                __request_or_options__: Queue.EmptyRequest,
                __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
            ) -> IMPORT_typing.AsyncIterator[Queue.EmptyResponse]:
                ...

            @IMPORT_typing.overload
            async def Empty(
                __this__,
                __context__: IMPORT_reboot_aio_external.ExternalContext | IMPORT_reboot_aio_contexts.ReaderContext | IMPORT_reboot_aio_contexts.WorkflowContext,
                __request_or_options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
            ) -> IMPORT_typing.AsyncIterator[Queue.EmptyResponse]:
                ...

            async def Empty( # type: ignore[misc]
                # In methods which are dealing with user input, (i.e.,
                # proto message field names), we should use '__double_underscored__'
                # variables to avoid any potential name conflicts with the method's
                # parameters.
                # The '__self__' parameter is a convention in Python to
                # indicate that this method is a bound method, so we use
                # '__this__' instead.
                __this__,
                # Explicitly-reactive calls only make sense in the context of either...
                # (A) an external client, or...
                # (B) methods that may reasonably run for a long time, which in Reboot means: readers or workflows.
                __context__: IMPORT_reboot_aio_external.ExternalContext | IMPORT_reboot_aio_contexts.ReaderContext | IMPORT_reboot_aio_contexts.WorkflowContext,
                __request_or_options__: IMPORT_typing.Optional[Queue.EmptyRequest | IMPORT_reboot_aio_call.Options] = None,
                __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
            ) -> IMPORT_typing.AsyncIterator[Queue.EmptyResponse]:
                IMPORT_reboot_aio_types.assert_type(__context__, [IMPORT_reboot_aio_external.ExternalContext, IMPORT_reboot_aio_contexts.ReaderContext, IMPORT_reboot_aio_contexts.WorkflowContext])
                # UX improvement: check that neither positional argument was accidentally
                # given a gRPC request type.
                IMPORT_reboot_aio_types.assert_not_request_type(__context__, request_type=Queue.EmptyRequest)
                IMPORT_reboot_aio_types.assert_not_request_type(__options__, request_type=Queue.EmptyRequest)

                __request__: IMPORT_typing.Optional[Queue.EmptyRequest] = None

                if isinstance(__request_or_options__, Queue.EmptyRequest):
                    assert __request_or_options__ is not None
                    assert __options__ is None or isinstance(__options__, IMPORT_reboot_aio_call.Options)
                    __request__ = __request_or_options__

                else:
                    assert __options__ is None
                    assert __request_or_options__ is None or isinstance(__request_or_options__, IMPORT_reboot_aio_call.Options)
                    __options__ = __request_or_options__

                    __request__ = QueueEmptyRequestFromInputFields(
                    )

                __metadata__: IMPORT_typing.Optional[IMPORT_reboot_aio_types.GrpcMetadata] = None
                __bearer_token__: IMPORT_typing.Optional[str] = None
                __caller_id__: IMPORT_typing.Optional[IMPORT_reboot_aio_caller_id.CallerID] = None

                if __options__ is not None:
                    IMPORT_reboot_aio_types.assert_type(__options__, [IMPORT_reboot_aio_call.Options])
                    if __options__.metadata is not None:
                        __metadata__ = __options__.metadata
                    if __options__.bearer_token is not None:
                        __bearer_token__ = __options__.bearer_token

                if __bearer_token__ is None:
                    __bearer_token__ = __this__._bearer_token
                if __bearer_token__ is None and isinstance(__context__, IMPORT_reboot_aio_external.ExternalContext):
                    # Within a Reboot context we do not pass on the caller's bearer token, as that might
                    # have security implications - we cannot simply trust any service we are calling with
                    # the user's credentials. Instead, the developer can rely on the default app-internal
                    # auth, or override that and set an explicit bearer token.
                    #
                    # In the case of `ExternalContext`, however, its `bearer_token` was set specifically
                    # by the developer for the purpose of making these calls. Note that only
                    # `ExternalContext` even has a `bearer_token` field.
                    __bearer_token__ = __context__.bearer_token

                if __metadata__ is None:
                    __metadata__ = ()

                if isinstance(__context__, IMPORT_reboot_aio_contexts.Context):
                    __caller_id__ = IMPORT_reboot_aio_caller_id.CallerID(
                        application_id=__context__.application_id,
                    )
                    if __this__._application_id is None:
                        # Given our context type (inside a Reboot application) we can default to
                        # making the application send traffic to itself.
                        __this__._application_id = __context__.application_id
                elif isinstance(__context__, IMPORT_reboot_aio_external.ExternalContext):
                    __caller_id__ = __context__.caller_id

                __headers__ = IMPORT_reboot_aio_headers.Headers(
                    bearer_token=__bearer_token__,
                    state_ref=__this__._state_ref,
                    application_id=__this__._application_id,
                    caller_id=__caller_id__,
                )

                __metadata__ += __headers__.to_grpc_metadata()

                __query_backoff__ = IMPORT_reboot_aio_backoff.Backoff()
                while True:
                    __call__ = None
                    try:
                        async with __context__.channel_manager.get_channel_to_state(
                            IMPORT_reboot_aio_types.StateTypeName('rbt.std.collections.queue.v1.Queue'),
                            __this__._state_ref,
                        ) as __channel__:

                            __call__ = IMPORT_rbt_v1alpha1.react_pb2_grpc.ReactStub(
                                __channel__
                            ).Query(
                                IMPORT_rbt_v1alpha1.react_pb2.QueryRequest(
                                    method='Empty',
                                    request=QueueEmptyRequestToProto(
                                        __request__
                                    ).SerializeToString(),
                                ),
                                metadata=__metadata__,
                            )

                            async for __query_response__ in __call__:
                                # Clear the backoff so we don't wait
                                # as long the next time we get
                                # disconnected.
                                __query_backoff__.clear()

                                # The backend may have sent us this query
                                # response only to let us know that a new
                                # idempotency key has been recorded; there may
                                # not be a new response. Python callers don't
                                # (currently) care about such an event, so we
                                # simply ignore it.
                                if not __query_response__.HasField("response"):
                                    continue

                                __response__ = rbt.std.collections.queue.v1.queue_pb2.EmptyResponse()
                                __response__.ParseFromString(__query_response__.response)
                                yield QueueEmptyResponseFromProto(__response__)

                    except IMPORT_grpc.aio.AioRpcError as error:
                        # We expect to get disconnected from the server
                        # from time to time, e.g., when it is being
                        # updated, but we don't want that error to
                        # propagate, we just want to retry.
                        if IMPORT_rebootdev.aio.aborted.is_grpc_retryable_exception(error):
                            logger.debug(
                                "Reactive read to 'rbt.std.collections.queue.v1.QueueMethods.Empty' "
                                f"failed with a retryable error: '{error}'; "
                                "will retry..."
                            )
                            await __query_backoff__()
                            continue
                        if error.code() == IMPORT_grpc.StatusCode.ABORTED:
                            # Reconstitute the error that the server threw, if it was a declared error.
                            status = await IMPORT_rpc_status_async.from_call(__call__)
                            if status is not None:
                                raise Queue.EmptyAborted.from_status(
                                    status
                                ) from None
                            raise Queue.EmptyAborted.from_grpc_aio_rpc_error(
                                error
                            ) from None

                        raise

            # Keep the original functions on the client, so old code will
            # continue to work, but use the new 'snake_case' method in
            # the new code.
            empty = Empty

        def reactively(self):
            return Queue.WeakReference._Reactively(
                application_id=self._application_id,
                state_ref=self._state_ref,
                bearer_token=self._bearer_token,
            )

        class _Idempotently(IMPORT_typing.Generic[Queue_IdempotentlyScheduleTypeVar]):

            _weak_reference: Queue.WeakReference[Queue_IdempotentlyScheduleTypeVar]

            def __init__(
                self,
                *,
                weak_reference: Queue.WeakReference[Queue_IdempotentlyScheduleTypeVar],
                idempotency: IMPORT_reboot_aio_idempotency.Idempotency,
            ):
                self._weak_reference = weak_reference
                self._idempotency = idempotency

            def schedule(
                self,
                *,
                when: IMPORT_typing.Optional[IMPORT_datetime_datetime | IMPORT_datetime_timedelta] = None,
            ) -> Queue_IdempotentlyScheduleTypeVar:
                return self._weak_reference._schedule_type(
                    self._weak_reference._application_id,
                    self._weak_reference._tasks,
                    when=when,
                    idempotency=self._idempotency,
                )

            def spawn(
                self,
                *,
                when: IMPORT_typing.Optional[IMPORT_datetime_datetime | IMPORT_datetime_timedelta] = None,
            ) -> Queue.WeakReference._Spawn:
                return Queue.WeakReference._Spawn(
                    self._weak_reference._application_id,
                    self._weak_reference._tasks,
                    when=when,
                    idempotency=self._idempotency,
                )

            async def read(
                self,
                context: IMPORT_reboot_aio_contexts.WorkflowContext,
            ) -> Queue.State:
                if self._weak_reference._servicer is None:
                    raise RuntimeError(
                        "`read()` is currently only supported within workflows; "
                        "Please reach out and let us know your use case if this "
                        "is important for you!"
                    )

                return await QueueBaseServicer.WorkflowState._Idempotently._read(
                    self._weak_reference._servicer,
                    self._idempotency,
                    context,
                )

            @IMPORT_typing.overload
            async def write(
                self,
                context: IMPORT_reboot_aio_contexts.WorkflowContext,
                writer: QueueBaseServicer.InlineWriterCallable[None],
                *,
                type: type = type(None),
            ) -> None:
                ...

            @IMPORT_typing.overload
            async def write(
                self,
                context: IMPORT_reboot_aio_contexts.WorkflowContext,
                writer: QueueBaseServicer.InlineWriterCallable[QueueBaseServicer.InlineWriterCallableResult],
                *,
                type: type[QueueBaseServicer.InlineWriterCallableResult],
            ) -> QueueBaseServicer.InlineWriterCallableResult:
                ...

            async def write(
                self,
                context: IMPORT_reboot_aio_contexts.WorkflowContext,
                writer: QueueBaseServicer.InlineWriterCallable[QueueBaseServicer.InlineWriterCallableResult],
                *,
                type: type = type(None),
            ) -> QueueBaseServicer.InlineWriterCallableResult:
                if self._weak_reference._servicer is None:
                    raise RuntimeError(
                        "`write()` is currently only supported within workflows; "
                        "Please reach out and let us know your use case if this "
                        "is important for you!"
                    )

                return await QueueBaseServicer.WorkflowState._Idempotently._write_validating_effects(
                    self._weak_reference._servicer,
                    self._idempotency,
                    context,
                    writer,
                    type_result=type,
                    check_type=not self._idempotency.always,
                    unidempotently=self._idempotency.always,
                    checkpoint=context.checkpoint(),
                )

            @IMPORT_typing.overload
            async def Enqueue(
                __this__,
                __context__: IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
                __request_or_options__: Queue.EnqueueRequest,
                __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
            ) -> Queue.EnqueueResponse:
                ...

            @IMPORT_typing.overload
            async def Enqueue(
                __this__,
                __context__: IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
                __request_or_options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
                *,
                value: IMPORT_typing.Optional[google.protobuf.struct_pb2.Value] | Unset = UNSET,
                bytes: IMPORT_typing.Optional[bytes] | Unset = UNSET,
                any: IMPORT_typing.Optional[google.protobuf.any_pb2.Any] | Unset = UNSET,
                items: IMPORT_typing.Optional[IMPORT_typing.Iterable[rbt.std.item.v1.item_pb2.Item]] | Unset = UNSET,
            ) -> Queue.EnqueueResponse:
                ...

            async def Enqueue( # type: ignore[misc]
                # In methods which are dealing with user input, (i.e.,
                # proto message field names), we should use '__double_underscored__'
                # variables to avoid any potential name conflicts with the method's
                # parameters.
                # The '__self__' parameter is a convention in Python to
                # indicate that this method is a bound method, so we use
                # '__this__' instead.
                __this__,
                __context__: IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
                __request_or_options__: IMPORT_typing.Optional[Queue.EnqueueRequest | IMPORT_reboot_aio_call.Options] = None,
                __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
                *,
                value: IMPORT_typing.Optional[google.protobuf.struct_pb2.Value] | Unset = UNSET,
                bytes: IMPORT_typing.Optional[bytes] | Unset = UNSET,
                any: IMPORT_typing.Optional[google.protobuf.any_pb2.Any] | Unset = UNSET,
                items: IMPORT_typing.Optional[IMPORT_typing.Iterable[rbt.std.item.v1.item_pb2.Item]] | Unset = UNSET,
            ) -> Queue.EnqueueResponse:
                # UX improvement: check that neither positional argument was accidentally
                # given a gRPC request type.
                IMPORT_reboot_aio_types.assert_not_request_type(__context__, request_type=Queue.EnqueueRequest)
                IMPORT_reboot_aio_types.assert_not_request_type(__options__, request_type=Queue.EnqueueRequest)

                __request__: IMPORT_typing.Optional[Queue.EnqueueRequest] = None
                if isinstance(__request_or_options__, Queue.EnqueueRequest):
                    assert __request_or_options__ is not None
                    assert __options__ is None or isinstance(__options__, IMPORT_reboot_aio_call.Options)
                    __options__ = __options__ or IMPORT_reboot_aio_call.Options()

                    assert value is UNSET
                    assert bytes is UNSET
                    assert any is UNSET
                    assert items is UNSET

                    __request__ = __request_or_options__
                else:
                    assert __options__ is None
                    assert __request_or_options__ is None or isinstance(__request_or_options__, IMPORT_reboot_aio_call.Options)
                    __options__ = __request_or_options__ or IMPORT_reboot_aio_call.Options()

                    __request__ = QueueEnqueueRequestFromInputFields(
                        value=value,
                        bytes=bytes,
                        any=any,
                        items=items,
                    )
                IMPORT_reboot_aio_types.assert_type(__options__, [IMPORT_reboot_aio_call.Options])
                if __options__.idempotency is not None:
                    raise RuntimeError(
                        'Found redundant idempotency in `Options`'
                    )

                __options__ = IMPORT_dataclasses.replace(
                    __options__,
                    idempotency_key=__this__._idempotency.key,
                    idempotency_alias=__this__._idempotency.alias,
                    generate_idempotency=__this__._idempotency.generate,
                    generated_idempotency=__this__._idempotency.generated,
                )

                return await __this__._weak_reference.Enqueue(
                    __context__,
                    __request__,
                    __options__,
                )

            # Keep the original functions on the client, so old code will
            # continue to work, but use the new 'snake_case' method in
            # the new code.
            enqueue = Enqueue
            @IMPORT_typing.overload
            async def Dequeue(
                __this__,
                __context__: IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
                __request_or_options__: Queue.DequeueRequest,
                __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
            ) -> Queue.DequeueResponse:
                ...

            @IMPORT_typing.overload
            async def Dequeue(
                __this__,
                __context__: IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
                __request_or_options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
                *,
                bulk: IMPORT_typing.Optional[bool] | Unset = UNSET,
                at_most: IMPORT_typing.Optional[int] | Unset = UNSET,
            ) -> Queue.DequeueResponse:
                ...

            async def Dequeue( # type: ignore[misc]
                # In methods which are dealing with user input, (i.e.,
                # proto message field names), we should use '__double_underscored__'
                # variables to avoid any potential name conflicts with the method's
                # parameters.
                # The '__self__' parameter is a convention in Python to
                # indicate that this method is a bound method, so we use
                # '__this__' instead.
                __this__,
                __context__: IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
                __request_or_options__: IMPORT_typing.Optional[Queue.DequeueRequest | IMPORT_reboot_aio_call.Options] = None,
                __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
                *,
                bulk: IMPORT_typing.Optional[bool] | Unset = UNSET,
                at_most: IMPORT_typing.Optional[int] | Unset = UNSET,
            ) -> Queue.DequeueResponse:
                def error_message_supplement():
                    if any([isinstance(__context__, t) for t in [IMPORT_reboot_aio_contexts.WriterContext, IMPORT_reboot_aio_contexts.TransactionContext]]):
                        return f"'Dequeue' is a workflow and must be scheduled from a '{type(__context__).__name__}' via `await [...].schedule([...]).Dequeue(context, [...])`"
                    else:
                        return f"'Dequeue' is a workflow and can not be called from '{type(__context__).__name__}'"

                IMPORT_reboot_aio_types.assert_type(
                    __context__,
                    [
                        IMPORT_reboot_aio_contexts.WorkflowContext,
                        IMPORT_reboot_aio_external.ExternalContext,
                    ],
                    error_message_supplement=error_message_supplement(),
                )
                # UX improvement: check that neither positional argument was accidentally
                # given a gRPC request type.
                IMPORT_reboot_aio_types.assert_not_request_type(__context__, request_type=Queue.DequeueRequest)
                IMPORT_reboot_aio_types.assert_not_request_type(__options__, request_type=Queue.DequeueRequest)

                if isinstance(__request_or_options__, Queue.DequeueRequest):
                    assert __request_or_options__ is not None
                    assert __options__ is None or isinstance(__options__, IMPORT_reboot_aio_call.Options)
                    __options__ = __options__ or IMPORT_reboot_aio_call.Options()

                    assert bulk is UNSET
                    assert at_most is UNSET

                    return await (
                        await __this__.spawn().Dequeue(
                            __context__,
                            __request_or_options__,
                            __options__,
                        )
                    )
                else:
                    assert __options__ is None
                    assert __request_or_options__ is None or isinstance(__request_or_options__, IMPORT_reboot_aio_call.Options)
                    __options__ = __request_or_options__ or IMPORT_reboot_aio_call.Options()

                    return await (
                        await __this__.spawn().Dequeue(
                            __context__,
                            QueueDequeueRequestFromInputFields(
                                bulk=bulk,
                                at_most=at_most,
                            ),
                            __options__,
                        )
                    )

            # Keep the original functions on the client, so old code will
            # continue to work, but use the new 'snake_case' method in
            # the new code.
            dequeue = Dequeue
            @IMPORT_typing.overload
            async def TryDequeue(
                __this__,
                __context__: IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
                __request_or_options__: Queue.TryDequeueRequest,
                __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
            ) -> Queue.TryDequeueResponse:
                ...

            @IMPORT_typing.overload
            async def TryDequeue(
                __this__,
                __context__: IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
                __request_or_options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
                *,
                bulk: IMPORT_typing.Optional[bool] | Unset = UNSET,
                at_most: IMPORT_typing.Optional[int] | Unset = UNSET,
            ) -> Queue.TryDequeueResponse:
                ...

            async def TryDequeue( # type: ignore[misc]
                # In methods which are dealing with user input, (i.e.,
                # proto message field names), we should use '__double_underscored__'
                # variables to avoid any potential name conflicts with the method's
                # parameters.
                # The '__self__' parameter is a convention in Python to
                # indicate that this method is a bound method, so we use
                # '__this__' instead.
                __this__,
                __context__: IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
                __request_or_options__: IMPORT_typing.Optional[Queue.TryDequeueRequest | IMPORT_reboot_aio_call.Options] = None,
                __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
                *,
                bulk: IMPORT_typing.Optional[bool] | Unset = UNSET,
                at_most: IMPORT_typing.Optional[int] | Unset = UNSET,
            ) -> Queue.TryDequeueResponse:
                # UX improvement: check that neither positional argument was accidentally
                # given a gRPC request type.
                IMPORT_reboot_aio_types.assert_not_request_type(__context__, request_type=Queue.TryDequeueRequest)
                IMPORT_reboot_aio_types.assert_not_request_type(__options__, request_type=Queue.TryDequeueRequest)

                __request__: IMPORT_typing.Optional[Queue.TryDequeueRequest] = None
                if isinstance(__request_or_options__, Queue.TryDequeueRequest):
                    assert __request_or_options__ is not None
                    assert __options__ is None or isinstance(__options__, IMPORT_reboot_aio_call.Options)
                    __options__ = __options__ or IMPORT_reboot_aio_call.Options()

                    assert bulk is UNSET
                    assert at_most is UNSET

                    __request__ = __request_or_options__
                else:
                    assert __options__ is None
                    assert __request_or_options__ is None or isinstance(__request_or_options__, IMPORT_reboot_aio_call.Options)
                    __options__ = __request_or_options__ or IMPORT_reboot_aio_call.Options()

                    __request__ = QueueTryDequeueRequestFromInputFields(
                        bulk=bulk,
                        at_most=at_most,
                    )
                IMPORT_reboot_aio_types.assert_type(__options__, [IMPORT_reboot_aio_call.Options])
                if __options__.idempotency is not None:
                    raise RuntimeError(
                        'Found redundant idempotency in `Options`'
                    )

                __options__ = IMPORT_dataclasses.replace(
                    __options__,
                    idempotency_key=__this__._idempotency.key,
                    idempotency_alias=__this__._idempotency.alias,
                    generate_idempotency=__this__._idempotency.generate,
                    generated_idempotency=__this__._idempotency.generated,
                )

                return await __this__._weak_reference.TryDequeue(
                    __context__,
                    __request__,
                    __options__,
                )

            # Keep the original functions on the client, so old code will
            # continue to work, but use the new 'snake_case' method in
            # the new code.
            try_dequeue = TryDequeue
            @IMPORT_typing.overload
            async def Empty(
                __this__,
                __context__: IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
                __request_or_options__: Queue.EmptyRequest,
                __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
            ) -> Queue.EmptyResponse:
                ...

            @IMPORT_typing.overload
            async def Empty(
                __this__,
                __context__: IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
                __request_or_options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
            ) -> Queue.EmptyResponse:
                ...

            async def Empty( # type: ignore[misc]
                # In methods which are dealing with user input, (i.e.,
                # proto message field names), we should use '__double_underscored__'
                # variables to avoid any potential name conflicts with the method's
                # parameters.
                # The '__self__' parameter is a convention in Python to
                # indicate that this method is a bound method, so we use
                # '__this__' instead.
                __this__,
                __context__: IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
                __request_or_options__: IMPORT_typing.Optional[Queue.EmptyRequest | IMPORT_reboot_aio_call.Options] = None,
                __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
            ) -> Queue.EmptyResponse:
                # UX improvement: check that neither positional argument was accidentally
                # given a gRPC request type.
                IMPORT_reboot_aio_types.assert_not_request_type(__context__, request_type=Queue.EmptyRequest)
                IMPORT_reboot_aio_types.assert_not_request_type(__options__, request_type=Queue.EmptyRequest)

                __request__: IMPORT_typing.Optional[Queue.EmptyRequest] = None
                if isinstance(__request_or_options__, Queue.EmptyRequest):
                    assert __request_or_options__ is not None
                    assert __options__ is None or isinstance(__options__, IMPORT_reboot_aio_call.Options)
                    __options__ = __options__ or IMPORT_reboot_aio_call.Options()


                    __request__ = __request_or_options__
                else:
                    assert __options__ is None
                    assert __request_or_options__ is None or isinstance(__request_or_options__, IMPORT_reboot_aio_call.Options)
                    __options__ = __request_or_options__ or IMPORT_reboot_aio_call.Options()

                    __request__ = QueueEmptyRequestFromInputFields(
                    )
                IMPORT_reboot_aio_types.assert_type(__options__, [IMPORT_reboot_aio_call.Options])
                if __options__.idempotency is not None:
                    raise RuntimeError(
                        'Found redundant idempotency in `Options`'
                    )

                __options__ = IMPORT_dataclasses.replace(
                    __options__,
                    idempotency_key=__this__._idempotency.key,
                    idempotency_alias=__this__._idempotency.alias,
                    generate_idempotency=__this__._idempotency.generate,
                    generated_idempotency=__this__._idempotency.generated,
                )

                return await __this__._weak_reference.Empty(
                    __context__,
                    __request__,
                    __options__,
                )

            # Keep the original functions on the client, so old code will
            # continue to work, but use the new 'snake_case' method in
            # the new code.
            empty = Empty

        @IMPORT_typing.overload
        def idempotently(self, alias: IMPORT_typing.Optional[str] = None, *, each_iteration: bool = False) -> Queue.WeakReference._Idempotently[Queue_ScheduleTypeVar]:
            ...

        @IMPORT_typing.overload
        def idempotently(self, *, key: IMPORT_uuid.UUID, generated: bool = False) -> Queue.WeakReference._Idempotently[Queue_ScheduleTypeVar]:
            ...

        def idempotently(
            self,
            alias: IMPORT_typing.Optional[str] = None,
            *,
            key: IMPORT_typing.Optional[IMPORT_uuid.UUID] = None,
            each_iteration: IMPORT_typing.Optional[bool] = None,
            generated: bool = False,
        ) -> Queue.WeakReference._Idempotently[Queue_ScheduleTypeVar]:
            return Queue.WeakReference._Idempotently(
                weak_reference=self,
                idempotency=IMPORT_reboot_aio_contexts.Context.idempotency(
                    alias=alias,
                    key=key,
                    each_iteration=each_iteration,
                    generated=generated,
                )
            )

        def per_workflow(self, alias: IMPORT_typing.Optional[str] = None):
            return self.idempotently(alias)

        def per_iteration(self, alias: IMPORT_typing.Optional[str] = None):
            return self.idempotently(alias, each_iteration=True)

        def always(self):
            return self.idempotently(key=IMPORT_uuid.uuid4(), generated=True)

        class _UntilChangesSatisfies(IMPORT_typing.Generic[Queue_UntilCallableType]):

            _idempotency_alias: str
            _context: IMPORT_reboot_aio_contexts.WorkflowContext
            _callable: IMPORT_typing.Callable[[], IMPORT_typing.Awaitable[Queue_UntilCallableType]]
            _type: type[Queue_UntilCallableType]

            def __init__(
                self,
                *,
                idempotency_alias: str,
                context: IMPORT_reboot_aio_contexts.WorkflowContext,
                callable: IMPORT_typing.Callable[[], IMPORT_typing.Awaitable[Queue_UntilCallableType]],
                type: type[Queue_UntilCallableType],
            ):
                self._idempotency_alias = idempotency_alias
                self._context = context
                self._callable = callable
                self._type = type

            async def changes(self):
                return await IMPORT_reboot_aio_workflows.until_changes(
                    self._idempotency_alias,
                    self._context,
                    self._callable,
                    type=self._type,
                )

            async def satisfies(
                self,
                condition: IMPORT_typing.Callable[[Queue_UntilCallableType], bool],
            ):

                async def converge():
                    response = await self._callable()
                    if condition(response):
                        return response
                    return False

                return await IMPORT_reboot_aio_workflows.until(
                    self._idempotency_alias,
                    self._context,
                    converge,
                    type=self._type,
                )

        class _Until:

            _weak_reference: Queue.WeakReference
            _idempotency_alias: str

            def __init__(
                self,
                *,
                weak_reference: Queue.WeakReference,
                idempotency_alias: str,
            ):
                self._weak_reference = weak_reference
                self._idempotency_alias = idempotency_alias

            def read(
                self,
                context: IMPORT_reboot_aio_contexts.WorkflowContext,
            ) -> Queue.WeakReference._UntilChangesSatisfies[Queue.State]:
                IMPORT_reboot_aio_types.assert_type(
                    context,
                    [IMPORT_reboot_aio_contexts.WorkflowContext],
                )

                async def callable():
                    return await self._weak_reference.read(context)

                return Queue.WeakReference._UntilChangesSatisfies(
                    idempotency_alias=self._idempotency_alias,
                    context=context,
                    callable=callable,
                    type=Queue.State,
                )

            @IMPORT_typing.overload
            async def Empty(
                __this__,
                __context__: IMPORT_reboot_aio_contexts.WorkflowContext,
                __request_or_options__: Queue.EmptyRequest,
                __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
            ) -> Queue.WeakReference._UntilChangesSatisfies[Queue.EmptyResponse]:
                ...

            @IMPORT_typing.overload
            async def Empty(
                __this__,
                __context__: IMPORT_reboot_aio_contexts.WorkflowContext,
                __request_or_options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
            ) -> Queue.WeakReference._UntilChangesSatisfies[Queue.EmptyResponse]:
                ...

            def Empty( # type: ignore[misc]
                # In methods which are dealing with user input, (i.e.,
                # proto message field names), we should use '__double_underscored__'
                # variables to avoid any potential name conflicts with the method's
                # parameters.
                # The '__self__' parameter is a convention in Python to
                # indicate that this method is a bound method, so we use
                # '__this__' instead.
                __this__,
                __context__: IMPORT_reboot_aio_contexts.WorkflowContext,
                __request_or_options__: IMPORT_typing.Optional[Queue.EmptyRequest | IMPORT_reboot_aio_call.Options] = None,
                __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
            ) -> Queue.WeakReference._UntilChangesSatisfies[Queue.EmptyResponse]:
                IMPORT_reboot_aio_types.assert_type(
                    __context__,
                    [IMPORT_reboot_aio_contexts.WorkflowContext],
                )

                __request__: IMPORT_typing.Optional[Queue.EmptyRequest] = None
                if isinstance(__request_or_options__, Queue.EmptyRequest):
                    assert __request_or_options__ is not None
                    assert __options__ is None or isinstance(__options__, IMPORT_reboot_aio_call.Options)
                    __options__ = __options__ or IMPORT_reboot_aio_call.Options()


                    __request__ = __request_or_options__
                else:
                    assert __options__ is None
                    assert __request_or_options__ is None or isinstance(__request_or_options__, IMPORT_reboot_aio_call.Options)
                    __options__ = __request_or_options__ or IMPORT_reboot_aio_call.Options()

                    __request__ = QueueEmptyRequestFromInputFields(
                    )

                async def callable():
                    return await __this__._weak_reference.Empty(
                        __context__,
                        __request__,
                        __options__,
                    )

                return Queue.WeakReference._UntilChangesSatisfies(
                    idempotency_alias=__this__._idempotency_alias,
                    context=__context__,
                    callable=callable,
                    type=Queue.EmptyResponse,
                )

            # Keep the original functions on the client, so old code will
            # continue to work, but use the new 'snake_case' method in
            # the new code.
            empty = Empty

        def until(self, alias: str):
            return Queue.WeakReference._Until(
                weak_reference=self,
                idempotency_alias=alias,
            )

        def schedule(
            self,
            *,
            when: IMPORT_typing.Optional[IMPORT_datetime_datetime | IMPORT_datetime_timedelta] = None,
        ) -> Queue_ScheduleTypeVar:
            return self._schedule_type(self._application_id, self._tasks, when=when)

        class _Schedule:

            def __init__(
                self,
                application_id: IMPORT_typing.Optional[IMPORT_reboot_aio_types.ApplicationId],
                tasks: IMPORT_typing.Callable[[IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext], QueueTasksStub],
                *,
                when: IMPORT_typing.Optional[IMPORT_datetime_datetime | IMPORT_datetime_timedelta] = None,
                idempotency: IMPORT_typing.Optional[IMPORT_reboot_aio_idempotency.Idempotency] = None,
            ) -> None:
                self._application_id = application_id
                self._tasks = tasks
                self._when = ensure_has_timezone(when=when)
                self._idempotency = idempotency

            # Queue callable tasks:
            @IMPORT_typing.overload
            async def Enqueue(
                __this__,
                __context__: IMPORT_reboot_aio_contexts.TransactionContext,
                __request_or_options__: Queue.EnqueueRequest,
                __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
            ) -> IMPORT_rbt_v1alpha1.tasks_pb2.TaskId:
                ...

            @IMPORT_typing.overload
            async def Enqueue(
                __this__,
                __context__: IMPORT_reboot_aio_contexts.TransactionContext,
                __request_or_options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
                *,
                value: IMPORT_typing.Optional[google.protobuf.struct_pb2.Value] | Unset = UNSET,
                bytes: IMPORT_typing.Optional[bytes] | Unset = UNSET,
                any: IMPORT_typing.Optional[google.protobuf.any_pb2.Any] | Unset = UNSET,
                items: IMPORT_typing.Optional[IMPORT_typing.Iterable[rbt.std.item.v1.item_pb2.Item]] | Unset = UNSET,
            ) -> IMPORT_rbt_v1alpha1.tasks_pb2.TaskId:
                ...

            async def Enqueue( # type: ignore[misc]
                __this__,
                __context__: IMPORT_reboot_aio_contexts.TransactionContext,
                __request_or_options__: IMPORT_typing.Optional[Queue.EnqueueRequest | IMPORT_reboot_aio_call.Options] = None,
                __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
                *,
                value: IMPORT_typing.Optional[google.protobuf.struct_pb2.Value] | Unset = UNSET,
                bytes: IMPORT_typing.Optional[bytes] | Unset = UNSET,
                any: IMPORT_typing.Optional[google.protobuf.any_pb2.Any] | Unset = UNSET,
                items: IMPORT_typing.Optional[IMPORT_typing.Iterable[rbt.std.item.v1.item_pb2.Item]] | Unset = UNSET,
            ) -> IMPORT_rbt_v1alpha1.tasks_pb2.TaskId:
                IMPORT_reboot_aio_types.assert_type(__context__, [IMPORT_reboot_aio_contexts.TransactionContext])
                # UX improvement: check that neither positional argument was accidentally
                # given a gRPC request type.
                IMPORT_reboot_aio_types.assert_not_request_type(__context__, request_type=Queue.EnqueueRequest)
                IMPORT_reboot_aio_types.assert_not_request_type(__options__, request_type=Queue.EnqueueRequest)

                __request__: IMPORT_typing.Optional[Queue.EnqueueRequest] = None
                if isinstance(__request_or_options__, Queue.EnqueueRequest):
                    assert __request_or_options__ is not None
                    assert __options__ is None or isinstance(__options__, IMPORT_reboot_aio_call.Options)

                    assert value is UNSET
                    assert bytes is UNSET
                    assert any is UNSET
                    assert items is UNSET

                    __request__ = __request_or_options__
                else:
                    assert __options__ is None
                    assert __request_or_options__ is None or isinstance(__request_or_options__, IMPORT_reboot_aio_call.Options)
                    __options__ = __request_or_options__

                    __request__ = QueueEnqueueRequestFromInputFields(
                        value=value,
                        bytes=bytes,
                        any=any,
                        items=items,
                    )

                __schedule__: IMPORT_typing.Optional[IMPORT_reboot_time_DateTimeWithTimeZone] = (IMPORT_reboot_time_DateTimeWithTimeZone.now() + __this__._when) if isinstance(
                    __this__._when, IMPORT_datetime_timedelta
                ) else __this__._when

                __metadata__: IMPORT_typing.Optional[IMPORT_reboot_aio_types.GrpcMetadata] = None
                __idempotency__: IMPORT_typing.Optional[IMPORT_reboot_aio_idempotency.Idempotency] = __this__._idempotency
                __bearer_token__: IMPORT_typing.Optional[str] = None

                if __options__ is not None:
                    IMPORT_reboot_aio_types.assert_type(__options__, [IMPORT_reboot_aio_call.Options])
                    if __options__.idempotency:
                        if __idempotency__ is not None:
                            raise RuntimeError(
                                'Found redundant idempotency in `Options`'
                            )
                        __idempotency__ = __options__.idempotency
                    if __options__.metadata is not None:
                        __metadata__ = __options__.metadata
                    if __options__.bearer_token is not None:
                        __bearer_token__ = __options__.bearer_token

                # Add scheduling information to the metadata.
                __metadata__ = (
                    (IMPORT_reboot_aio_headers.TASK_SCHEDULE,
                    __schedule__.isoformat() if __schedule__ else ''),
                ) + (__metadata__ or tuple())

                __task_id__ = await __this__._tasks(
                    __context__
                ).Enqueue(
                    __request__,
                    idempotency=__idempotency__,
                    metadata=__metadata__,
                    bearer_token=__bearer_token__,
                )

                return __task_id__

            # Keep the original functions on the client, so old code will
            # continue to work, but use the new 'snake_case' method in
            # the new code.
            enqueue = Enqueue
            @IMPORT_typing.overload
            async def Dequeue(
                __this__,
                __context__: IMPORT_reboot_aio_contexts.TransactionContext,
                __request_or_options__: Queue.DequeueRequest,
                __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
            ) -> IMPORT_rbt_v1alpha1.tasks_pb2.TaskId:
                ...

            @IMPORT_typing.overload
            async def Dequeue(
                __this__,
                __context__: IMPORT_reboot_aio_contexts.TransactionContext,
                __request_or_options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
                *,
                bulk: IMPORT_typing.Optional[bool] | Unset = UNSET,
                at_most: IMPORT_typing.Optional[int] | Unset = UNSET,
            ) -> IMPORT_rbt_v1alpha1.tasks_pb2.TaskId:
                ...

            async def Dequeue( # type: ignore[misc]
                __this__,
                __context__: IMPORT_reboot_aio_contexts.TransactionContext,
                __request_or_options__: IMPORT_typing.Optional[Queue.DequeueRequest | IMPORT_reboot_aio_call.Options] = None,
                __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
                *,
                bulk: IMPORT_typing.Optional[bool] | Unset = UNSET,
                at_most: IMPORT_typing.Optional[int] | Unset = UNSET,
            ) -> IMPORT_rbt_v1alpha1.tasks_pb2.TaskId:
                IMPORT_reboot_aio_types.assert_type(__context__, [IMPORT_reboot_aio_contexts.TransactionContext])
                # UX improvement: check that neither positional argument was accidentally
                # given a gRPC request type.
                IMPORT_reboot_aio_types.assert_not_request_type(__context__, request_type=Queue.DequeueRequest)
                IMPORT_reboot_aio_types.assert_not_request_type(__options__, request_type=Queue.DequeueRequest)

                __request__: IMPORT_typing.Optional[Queue.DequeueRequest] = None
                if isinstance(__request_or_options__, Queue.DequeueRequest):
                    assert __request_or_options__ is not None
                    assert __options__ is None or isinstance(__options__, IMPORT_reboot_aio_call.Options)

                    assert bulk is UNSET
                    assert at_most is UNSET

                    __request__ = __request_or_options__
                else:
                    assert __options__ is None
                    assert __request_or_options__ is None or isinstance(__request_or_options__, IMPORT_reboot_aio_call.Options)
                    __options__ = __request_or_options__

                    __request__ = QueueDequeueRequestFromInputFields(
                        bulk=bulk,
                        at_most=at_most,
                    )

                __schedule__: IMPORT_typing.Optional[IMPORT_reboot_time_DateTimeWithTimeZone] = (IMPORT_reboot_time_DateTimeWithTimeZone.now() + __this__._when) if isinstance(
                    __this__._when, IMPORT_datetime_timedelta
                ) else __this__._when

                __metadata__: IMPORT_typing.Optional[IMPORT_reboot_aio_types.GrpcMetadata] = None
                __idempotency__: IMPORT_typing.Optional[IMPORT_reboot_aio_idempotency.Idempotency] = __this__._idempotency
                __bearer_token__: IMPORT_typing.Optional[str] = None

                if __options__ is not None:
                    IMPORT_reboot_aio_types.assert_type(__options__, [IMPORT_reboot_aio_call.Options])
                    if __options__.idempotency:
                        if __idempotency__ is not None:
                            raise RuntimeError(
                                'Found redundant idempotency in `Options`'
                            )
                        __idempotency__ = __options__.idempotency
                    if __options__.metadata is not None:
                        __metadata__ = __options__.metadata
                    if __options__.bearer_token is not None:
                        __bearer_token__ = __options__.bearer_token

                # Add scheduling information to the metadata.
                __metadata__ = (
                    (IMPORT_reboot_aio_headers.TASK_SCHEDULE,
                    __schedule__.isoformat() if __schedule__ else ''),
                ) + (__metadata__ or tuple())

                __task_id__ = await __this__._tasks(
                    __context__
                ).Dequeue(
                    __request__,
                    idempotency=__idempotency__,
                    metadata=__metadata__,
                    bearer_token=__bearer_token__,
                )

                return __task_id__

            # Keep the original functions on the client, so old code will
            # continue to work, but use the new 'snake_case' method in
            # the new code.
            dequeue = Dequeue
            @IMPORT_typing.overload
            async def TryDequeue(
                __this__,
                __context__: IMPORT_reboot_aio_contexts.TransactionContext,
                __request_or_options__: Queue.TryDequeueRequest,
                __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
            ) -> IMPORT_rbt_v1alpha1.tasks_pb2.TaskId:
                ...

            @IMPORT_typing.overload
            async def TryDequeue(
                __this__,
                __context__: IMPORT_reboot_aio_contexts.TransactionContext,
                __request_or_options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
                *,
                bulk: IMPORT_typing.Optional[bool] | Unset = UNSET,
                at_most: IMPORT_typing.Optional[int] | Unset = UNSET,
            ) -> IMPORT_rbt_v1alpha1.tasks_pb2.TaskId:
                ...

            async def TryDequeue( # type: ignore[misc]
                __this__,
                __context__: IMPORT_reboot_aio_contexts.TransactionContext,
                __request_or_options__: IMPORT_typing.Optional[Queue.TryDequeueRequest | IMPORT_reboot_aio_call.Options] = None,
                __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
                *,
                bulk: IMPORT_typing.Optional[bool] | Unset = UNSET,
                at_most: IMPORT_typing.Optional[int] | Unset = UNSET,
            ) -> IMPORT_rbt_v1alpha1.tasks_pb2.TaskId:
                IMPORT_reboot_aio_types.assert_type(__context__, [IMPORT_reboot_aio_contexts.TransactionContext])
                # UX improvement: check that neither positional argument was accidentally
                # given a gRPC request type.
                IMPORT_reboot_aio_types.assert_not_request_type(__context__, request_type=Queue.TryDequeueRequest)
                IMPORT_reboot_aio_types.assert_not_request_type(__options__, request_type=Queue.TryDequeueRequest)

                __request__: IMPORT_typing.Optional[Queue.TryDequeueRequest] = None
                if isinstance(__request_or_options__, Queue.TryDequeueRequest):
                    assert __request_or_options__ is not None
                    assert __options__ is None or isinstance(__options__, IMPORT_reboot_aio_call.Options)

                    assert bulk is UNSET
                    assert at_most is UNSET

                    __request__ = __request_or_options__
                else:
                    assert __options__ is None
                    assert __request_or_options__ is None or isinstance(__request_or_options__, IMPORT_reboot_aio_call.Options)
                    __options__ = __request_or_options__

                    __request__ = QueueTryDequeueRequestFromInputFields(
                        bulk=bulk,
                        at_most=at_most,
                    )

                __schedule__: IMPORT_typing.Optional[IMPORT_reboot_time_DateTimeWithTimeZone] = (IMPORT_reboot_time_DateTimeWithTimeZone.now() + __this__._when) if isinstance(
                    __this__._when, IMPORT_datetime_timedelta
                ) else __this__._when

                __metadata__: IMPORT_typing.Optional[IMPORT_reboot_aio_types.GrpcMetadata] = None
                __idempotency__: IMPORT_typing.Optional[IMPORT_reboot_aio_idempotency.Idempotency] = __this__._idempotency
                __bearer_token__: IMPORT_typing.Optional[str] = None

                if __options__ is not None:
                    IMPORT_reboot_aio_types.assert_type(__options__, [IMPORT_reboot_aio_call.Options])
                    if __options__.idempotency:
                        if __idempotency__ is not None:
                            raise RuntimeError(
                                'Found redundant idempotency in `Options`'
                            )
                        __idempotency__ = __options__.idempotency
                    if __options__.metadata is not None:
                        __metadata__ = __options__.metadata
                    if __options__.bearer_token is not None:
                        __bearer_token__ = __options__.bearer_token

                # Add scheduling information to the metadata.
                __metadata__ = (
                    (IMPORT_reboot_aio_headers.TASK_SCHEDULE,
                    __schedule__.isoformat() if __schedule__ else ''),
                ) + (__metadata__ or tuple())

                __task_id__ = await __this__._tasks(
                    __context__
                ).TryDequeue(
                    __request__,
                    idempotency=__idempotency__,
                    metadata=__metadata__,
                    bearer_token=__bearer_token__,
                )

                return __task_id__

            # Keep the original functions on the client, so old code will
            # continue to work, but use the new 'snake_case' method in
            # the new code.
            try_dequeue = TryDequeue
            @IMPORT_typing.overload
            async def Empty(
                __this__,
                __context__: IMPORT_reboot_aio_contexts.TransactionContext,
                __request_or_options__: Queue.EmptyRequest,
                __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
            ) -> IMPORT_rbt_v1alpha1.tasks_pb2.TaskId:
                ...

            @IMPORT_typing.overload
            async def Empty(
                __this__,
                __context__: IMPORT_reboot_aio_contexts.TransactionContext,
                __request_or_options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
            ) -> IMPORT_rbt_v1alpha1.tasks_pb2.TaskId:
                ...

            async def Empty( # type: ignore[misc]
                __this__,
                __context__: IMPORT_reboot_aio_contexts.TransactionContext,
                __request_or_options__: IMPORT_typing.Optional[Queue.EmptyRequest | IMPORT_reboot_aio_call.Options] = None,
                __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
            ) -> IMPORT_rbt_v1alpha1.tasks_pb2.TaskId:
                IMPORT_reboot_aio_types.assert_type(__context__, [IMPORT_reboot_aio_contexts.TransactionContext])
                # UX improvement: check that neither positional argument was accidentally
                # given a gRPC request type.
                IMPORT_reboot_aio_types.assert_not_request_type(__context__, request_type=Queue.EmptyRequest)
                IMPORT_reboot_aio_types.assert_not_request_type(__options__, request_type=Queue.EmptyRequest)

                __request__: IMPORT_typing.Optional[Queue.EmptyRequest] = None
                if isinstance(__request_or_options__, Queue.EmptyRequest):
                    assert __request_or_options__ is not None
                    assert __options__ is None or isinstance(__options__, IMPORT_reboot_aio_call.Options)


                    __request__ = __request_or_options__
                else:
                    assert __options__ is None
                    assert __request_or_options__ is None or isinstance(__request_or_options__, IMPORT_reboot_aio_call.Options)
                    __options__ = __request_or_options__

                    __request__ = QueueEmptyRequestFromInputFields(
                    )

                __schedule__: IMPORT_typing.Optional[IMPORT_reboot_time_DateTimeWithTimeZone] = (IMPORT_reboot_time_DateTimeWithTimeZone.now() + __this__._when) if isinstance(
                    __this__._when, IMPORT_datetime_timedelta
                ) else __this__._when

                __metadata__: IMPORT_typing.Optional[IMPORT_reboot_aio_types.GrpcMetadata] = None
                __idempotency__: IMPORT_typing.Optional[IMPORT_reboot_aio_idempotency.Idempotency] = __this__._idempotency
                __bearer_token__: IMPORT_typing.Optional[str] = None

                if __options__ is not None:
                    IMPORT_reboot_aio_types.assert_type(__options__, [IMPORT_reboot_aio_call.Options])
                    if __options__.idempotency:
                        if __idempotency__ is not None:
                            raise RuntimeError(
                                'Found redundant idempotency in `Options`'
                            )
                        __idempotency__ = __options__.idempotency
                    if __options__.metadata is not None:
                        __metadata__ = __options__.metadata
                    if __options__.bearer_token is not None:
                        __bearer_token__ = __options__.bearer_token

                # Add scheduling information to the metadata.
                __metadata__ = (
                    (IMPORT_reboot_aio_headers.TASK_SCHEDULE,
                    __schedule__.isoformat() if __schedule__ else ''),
                ) + (__metadata__ or tuple())

                __task_id__ = await __this__._tasks(
                    __context__
                ).Empty(
                    __request__,
                    idempotency=__idempotency__,
                    metadata=__metadata__,
                    bearer_token=__bearer_token__,
                )

                return __task_id__

            # Keep the original functions on the client, so old code will
            # continue to work, but use the new 'snake_case' method in
            # the new code.
            empty = Empty

        # A `WriterContext` can not call any methods in `_Schedule` to
        # prevent a writer from doing a `Foo.ref()` and trying to
        # schedule. However, we want to allow a writer to schedule
        # when we are constructing a `WeakReference` from
        # `self.ref()` so instead we return a `_WriterSchedule` to
        # provide type safety that allows a `WriterContext` to
        # schedule (for itself).
        class _WriterSchedule:

            def __init__(
                self,
                application_id: IMPORT_typing.Optional[IMPORT_reboot_aio_types.ApplicationId],
                tasks: IMPORT_typing.Callable[[IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext], QueueTasksStub],
                *,
                when: IMPORT_typing.Optional[IMPORT_datetime_datetime | IMPORT_datetime_timedelta] = None,
                idempotency: IMPORT_typing.Optional[IMPORT_reboot_aio_idempotency.Idempotency] = None,
            ) -> None:
                self._tasks = tasks
                self._when = ensure_has_timezone(when=when)
                self._idempotency = idempotency

            # Queue callable tasks:
            @IMPORT_typing.overload
            async def Enqueue(
                __this__,
                __context__: IMPORT_reboot_aio_contexts.WriterContext | IMPORT_reboot_aio_contexts.TransactionContext,
                __request_or_options__: Queue.EnqueueRequest,
                __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
            ) -> IMPORT_rbt_v1alpha1.tasks_pb2.TaskId:
                ...

            @IMPORT_typing.overload
            async def Enqueue(
                __this__,
                __context__: IMPORT_reboot_aio_contexts.WriterContext | IMPORT_reboot_aio_contexts.TransactionContext,
                __request_or_options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
                *,
                value: IMPORT_typing.Optional[google.protobuf.struct_pb2.Value] | Unset = UNSET,
                bytes: IMPORT_typing.Optional[bytes] | Unset = UNSET,
                any: IMPORT_typing.Optional[google.protobuf.any_pb2.Any] | Unset = UNSET,
                items: IMPORT_typing.Optional[IMPORT_typing.Iterable[rbt.std.item.v1.item_pb2.Item]] | Unset = UNSET,
            ) -> IMPORT_rbt_v1alpha1.tasks_pb2.TaskId:
                ...

            async def Enqueue( # type: ignore[misc]
                __this__,
                __context__: IMPORT_reboot_aio_contexts.WriterContext | IMPORT_reboot_aio_contexts.TransactionContext,
                __request_or_options__: IMPORT_typing.Optional[Queue.EnqueueRequest | IMPORT_reboot_aio_call.Options] = None,
                __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
                *,
                value: IMPORT_typing.Optional[google.protobuf.struct_pb2.Value] | Unset = UNSET,
                bytes: IMPORT_typing.Optional[bytes] | Unset = UNSET,
                any: IMPORT_typing.Optional[google.protobuf.any_pb2.Any] | Unset = UNSET,
                items: IMPORT_typing.Optional[IMPORT_typing.Iterable[rbt.std.item.v1.item_pb2.Item]] | Unset = UNSET,
            ) -> IMPORT_rbt_v1alpha1.tasks_pb2.TaskId:
                # Only `writer`s and `transaction`s should ``schedule()`, a
                # `workflow` should `spawn()`.
                IMPORT_reboot_aio_types.assert_type(__context__, [IMPORT_reboot_aio_contexts.WriterContext, IMPORT_reboot_aio_contexts.TransactionContext])

                # UX improvement: check that neither positional argument was accidentally
                # given a gRPC request type.
                IMPORT_reboot_aio_types.assert_not_request_type(__context__, request_type=Queue.EnqueueRequest)
                IMPORT_reboot_aio_types.assert_not_request_type(__options__, request_type=Queue.EnqueueRequest)

                __request__: IMPORT_typing.Optional[Queue.EnqueueRequest] = None
                if isinstance(__request_or_options__, Queue.EnqueueRequest):
                    assert __request_or_options__ is not None
                    assert __options__ is None or isinstance(__options__, IMPORT_reboot_aio_call.Options)

                    assert value is UNSET
                    assert bytes is UNSET
                    assert any is UNSET
                    assert items is UNSET

                    __request__ = __request_or_options__
                else:
                    assert __options__ is None
                    assert __request_or_options__ is None or isinstance(__request_or_options__, IMPORT_reboot_aio_call.Options)
                    __options__ = __request_or_options__

                    __request__ = QueueEnqueueRequestFromInputFields(
                        value=value,
                        bytes=bytes,
                        any=any,
                        items=items,
                    )

                if isinstance(__context__, IMPORT_reboot_aio_contexts.WriterContext):
                    return (await QueueServicerTasks(
                        context=__context__,
                        state_ref=__context__._state_ref,
                    ).Enqueue(
                        __request__,
                        schedule=__this__._when,
                    )).task_id

                __schedule__: IMPORT_typing.Optional[IMPORT_reboot_time_DateTimeWithTimeZone] = (IMPORT_reboot_time_DateTimeWithTimeZone.now() + __this__._when) if isinstance(
                    __this__._when, IMPORT_datetime_timedelta
                ) else __this__._when

                __metadata__: IMPORT_typing.Optional[IMPORT_reboot_aio_types.GrpcMetadata] = None
                __idempotency__: IMPORT_typing.Optional[IMPORT_reboot_aio_idempotency.Idempotency] = __this__._idempotency
                __bearer_token__: IMPORT_typing.Optional[str] = None

                if __options__ is not None:
                    IMPORT_reboot_aio_types.assert_type(__options__, [IMPORT_reboot_aio_call.Options])
                    if __options__.idempotency is not None:
                        if __idempotency__ is not None:
                            raise RuntimeError(
                                'Found redundant idempotency in `Options`'
                            )
                        __idempotency__ = __options__.idempotency
                    if __options__.metadata is not None:
                        __metadata__ = __options__.metadata
                    if __options__.bearer_token is not None:
                        __bearer_token__ = __options__.bearer_token

                # Add scheduling information to the metadata.
                __metadata__ = (
                    (IMPORT_reboot_aio_headers.TASK_SCHEDULE,
                    __schedule__.isoformat() if __schedule__ else ''),
                ) + (__metadata__ or tuple())

                return await __this__._tasks(
                    __context__
                ).Enqueue(
                    __request__,
                    idempotency=__idempotency__,
                    metadata=__metadata__,
                    bearer_token=__bearer_token__,
                )

            # Keep the original functions on the client, so old code will
            # continue to work, but use the new 'snake_case' method in
            # the new code.
            enqueue = Enqueue
            @IMPORT_typing.overload
            async def Dequeue(
                __this__,
                __context__: IMPORT_reboot_aio_contexts.WriterContext | IMPORT_reboot_aio_contexts.TransactionContext,
                __request_or_options__: Queue.DequeueRequest,
                __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
            ) -> IMPORT_rbt_v1alpha1.tasks_pb2.TaskId:
                ...

            @IMPORT_typing.overload
            async def Dequeue(
                __this__,
                __context__: IMPORT_reboot_aio_contexts.WriterContext | IMPORT_reboot_aio_contexts.TransactionContext,
                __request_or_options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
                *,
                bulk: IMPORT_typing.Optional[bool] | Unset = UNSET,
                at_most: IMPORT_typing.Optional[int] | Unset = UNSET,
            ) -> IMPORT_rbt_v1alpha1.tasks_pb2.TaskId:
                ...

            async def Dequeue( # type: ignore[misc]
                __this__,
                __context__: IMPORT_reboot_aio_contexts.WriterContext | IMPORT_reboot_aio_contexts.TransactionContext,
                __request_or_options__: IMPORT_typing.Optional[Queue.DequeueRequest | IMPORT_reboot_aio_call.Options] = None,
                __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
                *,
                bulk: IMPORT_typing.Optional[bool] | Unset = UNSET,
                at_most: IMPORT_typing.Optional[int] | Unset = UNSET,
            ) -> IMPORT_rbt_v1alpha1.tasks_pb2.TaskId:
                # Only `writer`s and `transaction`s should ``schedule()`, a
                # `workflow` should `spawn()`.
                IMPORT_reboot_aio_types.assert_type(__context__, [IMPORT_reboot_aio_contexts.WriterContext, IMPORT_reboot_aio_contexts.TransactionContext])

                # UX improvement: check that neither positional argument was accidentally
                # given a gRPC request type.
                IMPORT_reboot_aio_types.assert_not_request_type(__context__, request_type=Queue.DequeueRequest)
                IMPORT_reboot_aio_types.assert_not_request_type(__options__, request_type=Queue.DequeueRequest)

                __request__: IMPORT_typing.Optional[Queue.DequeueRequest] = None
                if isinstance(__request_or_options__, Queue.DequeueRequest):
                    assert __request_or_options__ is not None
                    assert __options__ is None or isinstance(__options__, IMPORT_reboot_aio_call.Options)

                    assert bulk is UNSET
                    assert at_most is UNSET

                    __request__ = __request_or_options__
                else:
                    assert __options__ is None
                    assert __request_or_options__ is None or isinstance(__request_or_options__, IMPORT_reboot_aio_call.Options)
                    __options__ = __request_or_options__

                    __request__ = QueueDequeueRequestFromInputFields(
                        bulk=bulk,
                        at_most=at_most,
                    )

                if isinstance(__context__, IMPORT_reboot_aio_contexts.WriterContext):
                    return (await QueueServicerTasks(
                        context=__context__,
                        state_ref=__context__._state_ref,
                    ).Dequeue(
                        __request__,
                        schedule=__this__._when,
                    )).task_id

                __schedule__: IMPORT_typing.Optional[IMPORT_reboot_time_DateTimeWithTimeZone] = (IMPORT_reboot_time_DateTimeWithTimeZone.now() + __this__._when) if isinstance(
                    __this__._when, IMPORT_datetime_timedelta
                ) else __this__._when

                __metadata__: IMPORT_typing.Optional[IMPORT_reboot_aio_types.GrpcMetadata] = None
                __idempotency__: IMPORT_typing.Optional[IMPORT_reboot_aio_idempotency.Idempotency] = __this__._idempotency
                __bearer_token__: IMPORT_typing.Optional[str] = None

                if __options__ is not None:
                    IMPORT_reboot_aio_types.assert_type(__options__, [IMPORT_reboot_aio_call.Options])
                    if __options__.idempotency is not None:
                        if __idempotency__ is not None:
                            raise RuntimeError(
                                'Found redundant idempotency in `Options`'
                            )
                        __idempotency__ = __options__.idempotency
                    if __options__.metadata is not None:
                        __metadata__ = __options__.metadata
                    if __options__.bearer_token is not None:
                        __bearer_token__ = __options__.bearer_token

                # Add scheduling information to the metadata.
                __metadata__ = (
                    (IMPORT_reboot_aio_headers.TASK_SCHEDULE,
                    __schedule__.isoformat() if __schedule__ else ''),
                ) + (__metadata__ or tuple())

                return await __this__._tasks(
                    __context__
                ).Dequeue(
                    __request__,
                    idempotency=__idempotency__,
                    metadata=__metadata__,
                    bearer_token=__bearer_token__,
                )

            # Keep the original functions on the client, so old code will
            # continue to work, but use the new 'snake_case' method in
            # the new code.
            dequeue = Dequeue
            @IMPORT_typing.overload
            async def TryDequeue(
                __this__,
                __context__: IMPORT_reboot_aio_contexts.WriterContext | IMPORT_reboot_aio_contexts.TransactionContext,
                __request_or_options__: Queue.TryDequeueRequest,
                __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
            ) -> IMPORT_rbt_v1alpha1.tasks_pb2.TaskId:
                ...

            @IMPORT_typing.overload
            async def TryDequeue(
                __this__,
                __context__: IMPORT_reboot_aio_contexts.WriterContext | IMPORT_reboot_aio_contexts.TransactionContext,
                __request_or_options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
                *,
                bulk: IMPORT_typing.Optional[bool] | Unset = UNSET,
                at_most: IMPORT_typing.Optional[int] | Unset = UNSET,
            ) -> IMPORT_rbt_v1alpha1.tasks_pb2.TaskId:
                ...

            async def TryDequeue( # type: ignore[misc]
                __this__,
                __context__: IMPORT_reboot_aio_contexts.WriterContext | IMPORT_reboot_aio_contexts.TransactionContext,
                __request_or_options__: IMPORT_typing.Optional[Queue.TryDequeueRequest | IMPORT_reboot_aio_call.Options] = None,
                __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
                *,
                bulk: IMPORT_typing.Optional[bool] | Unset = UNSET,
                at_most: IMPORT_typing.Optional[int] | Unset = UNSET,
            ) -> IMPORT_rbt_v1alpha1.tasks_pb2.TaskId:
                # Only `writer`s and `transaction`s should ``schedule()`, a
                # `workflow` should `spawn()`.
                IMPORT_reboot_aio_types.assert_type(__context__, [IMPORT_reboot_aio_contexts.WriterContext, IMPORT_reboot_aio_contexts.TransactionContext])

                # UX improvement: check that neither positional argument was accidentally
                # given a gRPC request type.
                IMPORT_reboot_aio_types.assert_not_request_type(__context__, request_type=Queue.TryDequeueRequest)
                IMPORT_reboot_aio_types.assert_not_request_type(__options__, request_type=Queue.TryDequeueRequest)

                __request__: IMPORT_typing.Optional[Queue.TryDequeueRequest] = None
                if isinstance(__request_or_options__, Queue.TryDequeueRequest):
                    assert __request_or_options__ is not None
                    assert __options__ is None or isinstance(__options__, IMPORT_reboot_aio_call.Options)

                    assert bulk is UNSET
                    assert at_most is UNSET

                    __request__ = __request_or_options__
                else:
                    assert __options__ is None
                    assert __request_or_options__ is None or isinstance(__request_or_options__, IMPORT_reboot_aio_call.Options)
                    __options__ = __request_or_options__

                    __request__ = QueueTryDequeueRequestFromInputFields(
                        bulk=bulk,
                        at_most=at_most,
                    )

                if isinstance(__context__, IMPORT_reboot_aio_contexts.WriterContext):
                    return (await QueueServicerTasks(
                        context=__context__,
                        state_ref=__context__._state_ref,
                    ).TryDequeue(
                        __request__,
                        schedule=__this__._when,
                    )).task_id

                __schedule__: IMPORT_typing.Optional[IMPORT_reboot_time_DateTimeWithTimeZone] = (IMPORT_reboot_time_DateTimeWithTimeZone.now() + __this__._when) if isinstance(
                    __this__._when, IMPORT_datetime_timedelta
                ) else __this__._when

                __metadata__: IMPORT_typing.Optional[IMPORT_reboot_aio_types.GrpcMetadata] = None
                __idempotency__: IMPORT_typing.Optional[IMPORT_reboot_aio_idempotency.Idempotency] = __this__._idempotency
                __bearer_token__: IMPORT_typing.Optional[str] = None

                if __options__ is not None:
                    IMPORT_reboot_aio_types.assert_type(__options__, [IMPORT_reboot_aio_call.Options])
                    if __options__.idempotency is not None:
                        if __idempotency__ is not None:
                            raise RuntimeError(
                                'Found redundant idempotency in `Options`'
                            )
                        __idempotency__ = __options__.idempotency
                    if __options__.metadata is not None:
                        __metadata__ = __options__.metadata
                    if __options__.bearer_token is not None:
                        __bearer_token__ = __options__.bearer_token

                # Add scheduling information to the metadata.
                __metadata__ = (
                    (IMPORT_reboot_aio_headers.TASK_SCHEDULE,
                    __schedule__.isoformat() if __schedule__ else ''),
                ) + (__metadata__ or tuple())

                return await __this__._tasks(
                    __context__
                ).TryDequeue(
                    __request__,
                    idempotency=__idempotency__,
                    metadata=__metadata__,
                    bearer_token=__bearer_token__,
                )

            # Keep the original functions on the client, so old code will
            # continue to work, but use the new 'snake_case' method in
            # the new code.
            try_dequeue = TryDequeue
            @IMPORT_typing.overload
            async def Empty(
                __this__,
                __context__: IMPORT_reboot_aio_contexts.WriterContext | IMPORT_reboot_aio_contexts.TransactionContext,
                __request_or_options__: Queue.EmptyRequest,
                __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
            ) -> IMPORT_rbt_v1alpha1.tasks_pb2.TaskId:
                ...

            @IMPORT_typing.overload
            async def Empty(
                __this__,
                __context__: IMPORT_reboot_aio_contexts.WriterContext | IMPORT_reboot_aio_contexts.TransactionContext,
                __request_or_options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
            ) -> IMPORT_rbt_v1alpha1.tasks_pb2.TaskId:
                ...

            async def Empty( # type: ignore[misc]
                __this__,
                __context__: IMPORT_reboot_aio_contexts.WriterContext | IMPORT_reboot_aio_contexts.TransactionContext,
                __request_or_options__: IMPORT_typing.Optional[Queue.EmptyRequest | IMPORT_reboot_aio_call.Options] = None,
                __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
            ) -> IMPORT_rbt_v1alpha1.tasks_pb2.TaskId:
                # Only `writer`s and `transaction`s should ``schedule()`, a
                # `workflow` should `spawn()`.
                IMPORT_reboot_aio_types.assert_type(__context__, [IMPORT_reboot_aio_contexts.WriterContext, IMPORT_reboot_aio_contexts.TransactionContext])

                # UX improvement: check that neither positional argument was accidentally
                # given a gRPC request type.
                IMPORT_reboot_aio_types.assert_not_request_type(__context__, request_type=Queue.EmptyRequest)
                IMPORT_reboot_aio_types.assert_not_request_type(__options__, request_type=Queue.EmptyRequest)

                __request__: IMPORT_typing.Optional[Queue.EmptyRequest] = None
                if isinstance(__request_or_options__, Queue.EmptyRequest):
                    assert __request_or_options__ is not None
                    assert __options__ is None or isinstance(__options__, IMPORT_reboot_aio_call.Options)


                    __request__ = __request_or_options__
                else:
                    assert __options__ is None
                    assert __request_or_options__ is None or isinstance(__request_or_options__, IMPORT_reboot_aio_call.Options)
                    __options__ = __request_or_options__

                    __request__ = QueueEmptyRequestFromInputFields(
                    )

                if isinstance(__context__, IMPORT_reboot_aio_contexts.WriterContext):
                    return (await QueueServicerTasks(
                        context=__context__,
                        state_ref=__context__._state_ref,
                    ).Empty(
                        __request__,
                        schedule=__this__._when,
                    )).task_id

                __schedule__: IMPORT_typing.Optional[IMPORT_reboot_time_DateTimeWithTimeZone] = (IMPORT_reboot_time_DateTimeWithTimeZone.now() + __this__._when) if isinstance(
                    __this__._when, IMPORT_datetime_timedelta
                ) else __this__._when

                __metadata__: IMPORT_typing.Optional[IMPORT_reboot_aio_types.GrpcMetadata] = None
                __idempotency__: IMPORT_typing.Optional[IMPORT_reboot_aio_idempotency.Idempotency] = __this__._idempotency
                __bearer_token__: IMPORT_typing.Optional[str] = None

                if __options__ is not None:
                    IMPORT_reboot_aio_types.assert_type(__options__, [IMPORT_reboot_aio_call.Options])
                    if __options__.idempotency is not None:
                        if __idempotency__ is not None:
                            raise RuntimeError(
                                'Found redundant idempotency in `Options`'
                            )
                        __idempotency__ = __options__.idempotency
                    if __options__.metadata is not None:
                        __metadata__ = __options__.metadata
                    if __options__.bearer_token is not None:
                        __bearer_token__ = __options__.bearer_token

                # Add scheduling information to the metadata.
                __metadata__ = (
                    (IMPORT_reboot_aio_headers.TASK_SCHEDULE,
                    __schedule__.isoformat() if __schedule__ else ''),
                ) + (__metadata__ or tuple())

                return await __this__._tasks(
                    __context__
                ).Empty(
                    __request__,
                    idempotency=__idempotency__,
                    metadata=__metadata__,
                    bearer_token=__bearer_token__,
                )

            # Keep the original functions on the client, so old code will
            # continue to work, but use the new 'snake_case' method in
            # the new code.
            empty = Empty

        def spawn(
            self,
            *,
            when: IMPORT_typing.Optional[IMPORT_datetime_datetime | IMPORT_datetime_timedelta] = None,
        ) -> Queue.WeakReference._Spawn:
            # Within a `workflow`, all "bare" `spawn()` calls are
            # syntactic sugar for `per_workflow()`, unless we're
            # within a control loop, in which case they are syntactic
            # sugar for `per_iteration()`.
            context = IMPORT_reboot_aio_contexts.Context.get()
            if context is not None:
                if isinstance(context, IMPORT_reboot_aio_contexts.WorkflowContext):
                    return (
                        self.per_iteration() if context.within_loop()
                        else self.per_workflow()
                    ).spawn(when=when)
                elif isinstance(context, IMPORT_reboot_aio_external.InitializeContext):
                    return self.idempotently().spawn(when=when)

            return Queue.WeakReference._Spawn(
                self._application_id, self._tasks, when=when
            )

        class _Spawn:

            def __init__(
                self,
                application_id: IMPORT_typing.Optional[IMPORT_reboot_aio_types.ApplicationId],
                tasks: IMPORT_typing.Callable[[IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext], QueueTasksStub],
                *,
                when: IMPORT_typing.Optional[IMPORT_datetime_datetime | IMPORT_datetime_timedelta] = None,
                idempotency: IMPORT_typing.Optional[IMPORT_reboot_aio_idempotency.Idempotency] = None,
            ) -> None:
                self._application_id = application_id
                self._tasks = tasks
                self._when = ensure_has_timezone(when=when)
                self._idempotency = idempotency

            # Queue callable tasks:
            @IMPORT_typing.overload
            async def Enqueue(
                __this__,
                __context__: IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
                __request_or_options__: Queue.EnqueueRequest,
                __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
            ) -> Queue.EnqueueTask:
                ...

            @IMPORT_typing.overload
            async def Enqueue(
                __this__,
                __context__: IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
                __request_or_options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
                *,
                value: IMPORT_typing.Optional[google.protobuf.struct_pb2.Value] | Unset = UNSET,
                bytes: IMPORT_typing.Optional[bytes] | Unset = UNSET,
                any: IMPORT_typing.Optional[google.protobuf.any_pb2.Any] | Unset = UNSET,
                items: IMPORT_typing.Optional[IMPORT_typing.Iterable[rbt.std.item.v1.item_pb2.Item]] | Unset = UNSET,
            ) -> Queue.EnqueueTask:
                ...

            async def Enqueue( # type: ignore[misc]
                __this__,
                __context__: IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
                __request_or_options__: IMPORT_typing.Optional[Queue.EnqueueRequest | IMPORT_reboot_aio_call.Options] = None,
                __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
                *,
                value: IMPORT_typing.Optional[google.protobuf.struct_pb2.Value] | Unset = UNSET,
                bytes: IMPORT_typing.Optional[bytes] | Unset = UNSET,
                any: IMPORT_typing.Optional[google.protobuf.any_pb2.Any] | Unset = UNSET,
                items: IMPORT_typing.Optional[IMPORT_typing.Iterable[rbt.std.item.v1.item_pb2.Item]] | Unset = UNSET,
            ) -> Queue.EnqueueTask:
                IMPORT_reboot_aio_types.assert_type(__context__, [IMPORT_reboot_aio_contexts.WorkflowContext, IMPORT_reboot_aio_external.ExternalContext])
                # UX improvement: check that neither positional argument was accidentally
                # given a gRPC request type.
                IMPORT_reboot_aio_types.assert_not_request_type(__context__, request_type=Queue.EnqueueRequest)
                IMPORT_reboot_aio_types.assert_not_request_type(__options__, request_type=Queue.EnqueueRequest)


                __request__: IMPORT_typing.Optional[Queue.EnqueueRequest] = None
                if isinstance(__request_or_options__, Queue.EnqueueRequest):
                    assert __request_or_options__ is not None
                    assert __options__ is None or isinstance(__options__, IMPORT_reboot_aio_call.Options)

                    assert value is UNSET
                    assert bytes is UNSET
                    assert any is UNSET
                    assert items is UNSET

                    __request__ = __request_or_options__
                else:
                    assert __options__ is None
                    assert __request_or_options__ is None or isinstance(__request_or_options__, IMPORT_reboot_aio_call.Options)
                    __options__ = __request_or_options__

                    __request__ = QueueEnqueueRequestFromInputFields(
                        value=value,
                        bytes=bytes,
                        any=any,
                        items=items,
                    )
                __schedule__: IMPORT_typing.Optional[IMPORT_reboot_time_DateTimeWithTimeZone] = (IMPORT_reboot_time_DateTimeWithTimeZone.now() + __this__._when) if isinstance(
                    __this__._when, IMPORT_datetime_timedelta
                ) else __this__._when

                __metadata__: IMPORT_typing.Optional[IMPORT_reboot_aio_types.GrpcMetadata] = None
                __idempotency__: IMPORT_typing.Optional[IMPORT_reboot_aio_idempotency.Idempotency] = __this__._idempotency
                __bearer_token__: IMPORT_typing.Optional[str] = None

                if __options__ is not None:
                    IMPORT_reboot_aio_types.assert_type(__options__, [IMPORT_reboot_aio_call.Options])
                    if __options__.idempotency:
                        if __idempotency__ is not None:
                            raise RuntimeError(
                                'Found redundant idempotency in `Options`'
                            )
                        __idempotency__ = __options__.idempotency
                    if __options__.metadata is not None:
                        __metadata__ = __options__.metadata
                    if __options__.bearer_token is not None:
                        __bearer_token__ = __options__.bearer_token

                # Add scheduling information to the metadata.
                __metadata__ = (
                    (IMPORT_reboot_aio_headers.TASK_SCHEDULE,
                    __schedule__.isoformat() if __schedule__ else ''),
                ) + (__metadata__ or tuple())

                __task_id__ = await __this__._tasks(
                    __context__
                ).Enqueue(
                    __request__,
                    idempotency=__idempotency__,
                    metadata=__metadata__,
                    bearer_token=__bearer_token__,
                )

                return Queue.EnqueueTask(
                    __context__,
                    task_id=__task_id__,
                )

            # Keep the original functions on the client, so old code will
            # continue to work, but use the new 'snake_case' method in
            # the new code.
            enqueue = Enqueue
            @IMPORT_typing.overload
            async def Dequeue(
                __this__,
                __context__: IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
                __request_or_options__: Queue.DequeueRequest,
                __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
            ) -> Queue.DequeueTask:
                ...

            @IMPORT_typing.overload
            async def Dequeue(
                __this__,
                __context__: IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
                __request_or_options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
                *,
                bulk: IMPORT_typing.Optional[bool] | Unset = UNSET,
                at_most: IMPORT_typing.Optional[int] | Unset = UNSET,
            ) -> Queue.DequeueTask:
                ...

            async def Dequeue( # type: ignore[misc]
                __this__,
                __context__: IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
                __request_or_options__: IMPORT_typing.Optional[Queue.DequeueRequest | IMPORT_reboot_aio_call.Options] = None,
                __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
                *,
                bulk: IMPORT_typing.Optional[bool] | Unset = UNSET,
                at_most: IMPORT_typing.Optional[int] | Unset = UNSET,
            ) -> Queue.DequeueTask:
                IMPORT_reboot_aio_types.assert_type(__context__, [IMPORT_reboot_aio_contexts.WorkflowContext, IMPORT_reboot_aio_external.ExternalContext])
                # UX improvement: check that neither positional argument was accidentally
                # given a gRPC request type.
                IMPORT_reboot_aio_types.assert_not_request_type(__context__, request_type=Queue.DequeueRequest)
                IMPORT_reboot_aio_types.assert_not_request_type(__options__, request_type=Queue.DequeueRequest)


                __request__: IMPORT_typing.Optional[Queue.DequeueRequest] = None
                if isinstance(__request_or_options__, Queue.DequeueRequest):
                    assert __request_or_options__ is not None
                    assert __options__ is None or isinstance(__options__, IMPORT_reboot_aio_call.Options)

                    assert bulk is UNSET
                    assert at_most is UNSET

                    __request__ = __request_or_options__
                else:
                    assert __options__ is None
                    assert __request_or_options__ is None or isinstance(__request_or_options__, IMPORT_reboot_aio_call.Options)
                    __options__ = __request_or_options__

                    __request__ = QueueDequeueRequestFromInputFields(
                        bulk=bulk,
                        at_most=at_most,
                    )
                __schedule__: IMPORT_typing.Optional[IMPORT_reboot_time_DateTimeWithTimeZone] = (IMPORT_reboot_time_DateTimeWithTimeZone.now() + __this__._when) if isinstance(
                    __this__._when, IMPORT_datetime_timedelta
                ) else __this__._when

                __metadata__: IMPORT_typing.Optional[IMPORT_reboot_aio_types.GrpcMetadata] = None
                __idempotency__: IMPORT_typing.Optional[IMPORT_reboot_aio_idempotency.Idempotency] = __this__._idempotency
                __bearer_token__: IMPORT_typing.Optional[str] = None

                if __options__ is not None:
                    IMPORT_reboot_aio_types.assert_type(__options__, [IMPORT_reboot_aio_call.Options])
                    if __options__.idempotency:
                        if __idempotency__ is not None:
                            raise RuntimeError(
                                'Found redundant idempotency in `Options`'
                            )
                        __idempotency__ = __options__.idempotency
                    if __options__.metadata is not None:
                        __metadata__ = __options__.metadata
                    if __options__.bearer_token is not None:
                        __bearer_token__ = __options__.bearer_token

                # Add scheduling information to the metadata.
                __metadata__ = (
                    (IMPORT_reboot_aio_headers.TASK_SCHEDULE,
                    __schedule__.isoformat() if __schedule__ else ''),
                ) + (__metadata__ or tuple())

                __task_id__ = await __this__._tasks(
                    __context__
                ).Dequeue(
                    __request__,
                    idempotency=__idempotency__,
                    metadata=__metadata__,
                    bearer_token=__bearer_token__,
                )

                return Queue.DequeueTask(
                    __context__,
                    task_id=__task_id__,
                )

            # Keep the original functions on the client, so old code will
            # continue to work, but use the new 'snake_case' method in
            # the new code.
            dequeue = Dequeue
            @IMPORT_typing.overload
            async def TryDequeue(
                __this__,
                __context__: IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
                __request_or_options__: Queue.TryDequeueRequest,
                __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
            ) -> Queue.TryDequeueTask:
                ...

            @IMPORT_typing.overload
            async def TryDequeue(
                __this__,
                __context__: IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
                __request_or_options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
                *,
                bulk: IMPORT_typing.Optional[bool] | Unset = UNSET,
                at_most: IMPORT_typing.Optional[int] | Unset = UNSET,
            ) -> Queue.TryDequeueTask:
                ...

            async def TryDequeue( # type: ignore[misc]
                __this__,
                __context__: IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
                __request_or_options__: IMPORT_typing.Optional[Queue.TryDequeueRequest | IMPORT_reboot_aio_call.Options] = None,
                __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
                *,
                bulk: IMPORT_typing.Optional[bool] | Unset = UNSET,
                at_most: IMPORT_typing.Optional[int] | Unset = UNSET,
            ) -> Queue.TryDequeueTask:
                IMPORT_reboot_aio_types.assert_type(__context__, [IMPORT_reboot_aio_contexts.WorkflowContext, IMPORT_reboot_aio_external.ExternalContext])
                # UX improvement: check that neither positional argument was accidentally
                # given a gRPC request type.
                IMPORT_reboot_aio_types.assert_not_request_type(__context__, request_type=Queue.TryDequeueRequest)
                IMPORT_reboot_aio_types.assert_not_request_type(__options__, request_type=Queue.TryDequeueRequest)


                __request__: IMPORT_typing.Optional[Queue.TryDequeueRequest] = None
                if isinstance(__request_or_options__, Queue.TryDequeueRequest):
                    assert __request_or_options__ is not None
                    assert __options__ is None or isinstance(__options__, IMPORT_reboot_aio_call.Options)

                    assert bulk is UNSET
                    assert at_most is UNSET

                    __request__ = __request_or_options__
                else:
                    assert __options__ is None
                    assert __request_or_options__ is None or isinstance(__request_or_options__, IMPORT_reboot_aio_call.Options)
                    __options__ = __request_or_options__

                    __request__ = QueueTryDequeueRequestFromInputFields(
                        bulk=bulk,
                        at_most=at_most,
                    )
                __schedule__: IMPORT_typing.Optional[IMPORT_reboot_time_DateTimeWithTimeZone] = (IMPORT_reboot_time_DateTimeWithTimeZone.now() + __this__._when) if isinstance(
                    __this__._when, IMPORT_datetime_timedelta
                ) else __this__._when

                __metadata__: IMPORT_typing.Optional[IMPORT_reboot_aio_types.GrpcMetadata] = None
                __idempotency__: IMPORT_typing.Optional[IMPORT_reboot_aio_idempotency.Idempotency] = __this__._idempotency
                __bearer_token__: IMPORT_typing.Optional[str] = None

                if __options__ is not None:
                    IMPORT_reboot_aio_types.assert_type(__options__, [IMPORT_reboot_aio_call.Options])
                    if __options__.idempotency:
                        if __idempotency__ is not None:
                            raise RuntimeError(
                                'Found redundant idempotency in `Options`'
                            )
                        __idempotency__ = __options__.idempotency
                    if __options__.metadata is not None:
                        __metadata__ = __options__.metadata
                    if __options__.bearer_token is not None:
                        __bearer_token__ = __options__.bearer_token

                # Add scheduling information to the metadata.
                __metadata__ = (
                    (IMPORT_reboot_aio_headers.TASK_SCHEDULE,
                    __schedule__.isoformat() if __schedule__ else ''),
                ) + (__metadata__ or tuple())

                __task_id__ = await __this__._tasks(
                    __context__
                ).TryDequeue(
                    __request__,
                    idempotency=__idempotency__,
                    metadata=__metadata__,
                    bearer_token=__bearer_token__,
                )

                return Queue.TryDequeueTask(
                    __context__,
                    task_id=__task_id__,
                )

            # Keep the original functions on the client, so old code will
            # continue to work, but use the new 'snake_case' method in
            # the new code.
            try_dequeue = TryDequeue
            @IMPORT_typing.overload
            async def Empty(
                __this__,
                __context__: IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
                __request_or_options__: Queue.EmptyRequest,
                __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
            ) -> Queue.EmptyTask:
                ...

            @IMPORT_typing.overload
            async def Empty(
                __this__,
                __context__: IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
                __request_or_options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
            ) -> Queue.EmptyTask:
                ...

            async def Empty( # type: ignore[misc]
                __this__,
                __context__: IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
                __request_or_options__: IMPORT_typing.Optional[Queue.EmptyRequest | IMPORT_reboot_aio_call.Options] = None,
                __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
            ) -> Queue.EmptyTask:
                IMPORT_reboot_aio_types.assert_type(__context__, [IMPORT_reboot_aio_contexts.WorkflowContext, IMPORT_reboot_aio_external.ExternalContext])
                # UX improvement: check that neither positional argument was accidentally
                # given a gRPC request type.
                IMPORT_reboot_aio_types.assert_not_request_type(__context__, request_type=Queue.EmptyRequest)
                IMPORT_reboot_aio_types.assert_not_request_type(__options__, request_type=Queue.EmptyRequest)


                __request__: IMPORT_typing.Optional[Queue.EmptyRequest] = None
                if isinstance(__request_or_options__, Queue.EmptyRequest):
                    assert __request_or_options__ is not None
                    assert __options__ is None or isinstance(__options__, IMPORT_reboot_aio_call.Options)


                    __request__ = __request_or_options__
                else:
                    assert __options__ is None
                    assert __request_or_options__ is None or isinstance(__request_or_options__, IMPORT_reboot_aio_call.Options)
                    __options__ = __request_or_options__

                    __request__ = QueueEmptyRequestFromInputFields(
                    )
                __schedule__: IMPORT_typing.Optional[IMPORT_reboot_time_DateTimeWithTimeZone] = (IMPORT_reboot_time_DateTimeWithTimeZone.now() + __this__._when) if isinstance(
                    __this__._when, IMPORT_datetime_timedelta
                ) else __this__._when

                __metadata__: IMPORT_typing.Optional[IMPORT_reboot_aio_types.GrpcMetadata] = None
                __idempotency__: IMPORT_typing.Optional[IMPORT_reboot_aio_idempotency.Idempotency] = __this__._idempotency
                __bearer_token__: IMPORT_typing.Optional[str] = None

                if __options__ is not None:
                    IMPORT_reboot_aio_types.assert_type(__options__, [IMPORT_reboot_aio_call.Options])
                    if __options__.idempotency:
                        if __idempotency__ is not None:
                            raise RuntimeError(
                                'Found redundant idempotency in `Options`'
                            )
                        __idempotency__ = __options__.idempotency
                    if __options__.metadata is not None:
                        __metadata__ = __options__.metadata
                    if __options__.bearer_token is not None:
                        __bearer_token__ = __options__.bearer_token

                # Add scheduling information to the metadata.
                __metadata__ = (
                    (IMPORT_reboot_aio_headers.TASK_SCHEDULE,
                    __schedule__.isoformat() if __schedule__ else ''),
                ) + (__metadata__ or tuple())

                __task_id__ = await __this__._tasks(
                    __context__
                ).Empty(
                    __request__,
                    idempotency=__idempotency__,
                    metadata=__metadata__,
                    bearer_token=__bearer_token__,
                )

                return Queue.EmptyTask(
                    __context__,
                    task_id=__task_id__,
                )

            # Keep the original functions on the client, so old code will
            # continue to work, but use the new 'snake_case' method in
            # the new code.
            empty = Empty

        async def read(
            self,
            context: IMPORT_reboot_aio_contexts.WorkflowContext,
        ) -> Queue.State:
            return await (
                self.always() if context.within_until()
                else (
                    self.per_iteration() if context.within_loop()
                    else self.per_workflow()
                )
            ).read(context)

        @IMPORT_typing.overload
        async def write(
            self,
            context: IMPORT_reboot_aio_contexts.WorkflowContext,
            writer: QueueBaseServicer.InlineWriterCallable[None],
            *,
            type: type = type(None),
        ) -> None:
            ...

        @IMPORT_typing.overload
        async def write(
            self,
            context: IMPORT_reboot_aio_contexts.WorkflowContext,
            writer: QueueBaseServicer.InlineWriterCallable[QueueBaseServicer.InlineWriterCallableResult],
            *,
            type: type[QueueBaseServicer.InlineWriterCallableResult],
        ) -> QueueBaseServicer.InlineWriterCallableResult:
            ...

        async def write(
            self,
            context: IMPORT_reboot_aio_contexts.WorkflowContext,
            writer: QueueBaseServicer.InlineWriterCallable[QueueBaseServicer.InlineWriterCallableResult],
            *,
            type: type = type(None),
        ) -> QueueBaseServicer.InlineWriterCallableResult:
            """Perform an "inline write" within a workflow."""
            return await (
                self.always() if context.within_until()
                else (
                    self.per_iteration() if context.within_loop()
                    else self.per_workflow()
                )
            ).write(
                context, writer, type=type
            )

        # Queue specific methods:
        @IMPORT_typing.overload
        async def Enqueue(
            __this__,
            __context__: IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
            __request_or_options__: Queue.EnqueueRequest,
            __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
        ) -> Queue.EnqueueResponse:
            ...

        @IMPORT_typing.overload
        async def Enqueue(
            __this__,
            __context__: IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
            __request_or_options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
            *,
            value: IMPORT_typing.Optional[google.protobuf.struct_pb2.Value] | Unset = UNSET,
            bytes: IMPORT_typing.Optional[bytes] | Unset = UNSET,
            any: IMPORT_typing.Optional[google.protobuf.any_pb2.Any] | Unset = UNSET,
            items: IMPORT_typing.Optional[IMPORT_typing.Iterable[rbt.std.item.v1.item_pb2.Item]] | Unset = UNSET,
        ) -> Queue.EnqueueResponse:
            ...

        async def Enqueue( # type: ignore[misc]
            __this__,
            __context__: IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
            __request_or_options__: IMPORT_typing.Optional[Queue.EnqueueRequest | IMPORT_reboot_aio_call.Options] = None,
            __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
            *,
            value: IMPORT_typing.Optional[google.protobuf.struct_pb2.Value] | Unset = UNSET,
            bytes: IMPORT_typing.Optional[bytes] | Unset = UNSET,
            any: IMPORT_typing.Optional[google.protobuf.any_pb2.Any] | Unset = UNSET,
            items: IMPORT_typing.Optional[IMPORT_typing.Iterable[rbt.std.item.v1.item_pb2.Item]] | Unset = UNSET,
        ) -> Queue.EnqueueResponse:
            # UX improvement: check that neither positional argument was accidentally
            # given a gRPC request type.
            IMPORT_reboot_aio_types.assert_not_request_type(__context__, request_type=Queue.EnqueueRequest)
            IMPORT_reboot_aio_types.assert_not_request_type(__options__, request_type=Queue.EnqueueRequest)

            __request__: IMPORT_typing.Optional[Queue.EnqueueRequest] = None
            if isinstance(__request_or_options__, Queue.EnqueueRequest):
                assert __request_or_options__ is not None
                assert __options__ is None or isinstance(__options__, IMPORT_reboot_aio_call.Options)

                assert value is UNSET
                assert bytes is UNSET
                assert any is UNSET
                assert items is UNSET

                __request__ = __request_or_options__
            else:
                assert __options__ is None
                assert __request_or_options__ is None or isinstance(__request_or_options__, IMPORT_reboot_aio_call.Options)
                __options__ = __request_or_options__

                __request__ = QueueEnqueueRequestFromInputFields(
                    value=value,
                    bytes=bytes,
                    any=any,
                    items=items,
                )

            # Within a `workflow`, all "bare" calls are
            # `per_workflow()` calls, unless we're within a control
            # loop, in which case they are syntactic sugar for
            # `per_iteration()`.
            if __options__ is None or __options__.idempotency is None:
                if isinstance(__context__, IMPORT_reboot_aio_contexts.WorkflowContext):
                    return await (
                        __this__.per_iteration() if __context__.within_loop()
                        else __this__.per_workflow()
                    ).Enqueue(
                        __context__,
                        __request__,
                        __options__ or IMPORT_reboot_aio_call.Options(),
                    )
                elif isinstance(__context__, IMPORT_reboot_aio_external.InitializeContext):
                    return await __this__.idempotently().Enqueue(
                        __context__,
                        __request__,
                        __options__ or IMPORT_reboot_aio_call.Options(),
                    )

            __idempotency__: IMPORT_typing.Optional[IMPORT_reboot_aio_idempotency.Idempotency] = None
            __metadata__: IMPORT_typing.Optional[IMPORT_reboot_aio_types.GrpcMetadata] = None
            __bearer_token__: IMPORT_typing.Optional[str] = None
            if __options__ is not None:
                IMPORT_reboot_aio_types.assert_type(__options__, [IMPORT_reboot_aio_call.Options])
                if __options__.idempotency is not None:
                    __idempotency__ = __options__.idempotency
                if __options__.metadata is not None:
                    __metadata__ = __options__.metadata
                if __options__.bearer_token is not None:
                    __bearer_token__ = __options__.bearer_token

            return QueueEnqueueResponseFromProto(
                await __this__._workflow(__context__).Enqueue(
                    __request__,
                    idempotency=__idempotency__,
                    metadata=__metadata__,
                    bearer_token=__bearer_token__,
                )
            )

        # Keep the original functions on the client, so old code will
        # continue to work, but use the new 'snake_case' method in
        # the new code.
        enqueue = Enqueue
        @IMPORT_typing.overload
        async def Dequeue(
            __this__,
            __context__: IMPORT_reboot_aio_external.ExternalContext | IMPORT_reboot_aio_contexts.WorkflowContext,
            __request_or_options__: Queue.DequeueRequest,
            __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
        ) -> Queue.DequeueResponse:
            ...

        @IMPORT_typing.overload
        async def Dequeue(
            __this__,
            __context__: IMPORT_reboot_aio_external.ExternalContext | IMPORT_reboot_aio_contexts.WorkflowContext,
            __request_or_options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
            *,
            bulk: IMPORT_typing.Optional[bool] | Unset = UNSET,
            at_most: IMPORT_typing.Optional[int] | Unset = UNSET,
        ) -> Queue.DequeueResponse:
            ...

        async def Dequeue( # type: ignore[misc]
            # In methods which are dealing with user input, (i.e.,
            # proto message field names), we should use '__double_underscored__'
            # variables to avoid any potential name conflicts with the method's
            # parameters.
            # The '__self__' parameter is a convention in Python to
            # indicate that this method is a bound method, so we use
            # '__this__' instead.
            __this__,
            __context__: IMPORT_reboot_aio_external.ExternalContext | IMPORT_reboot_aio_contexts.WorkflowContext,
            __request_or_options__: IMPORT_typing.Optional[Queue.DequeueRequest | IMPORT_reboot_aio_call.Options] = None,
            __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
            *,
            bulk: IMPORT_typing.Optional[bool] | Unset = UNSET,
            at_most: IMPORT_typing.Optional[int] | Unset = UNSET,
        ) -> Queue.DequeueResponse:
            def error_message_supplement():
                if any([isinstance(__context__, t) for t in [IMPORT_reboot_aio_contexts.WriterContext, IMPORT_reboot_aio_contexts.TransactionContext]]):
                    return f"'Dequeue' is a workflow and must be scheduled from a '{type(__context__).__name__}' via `await [...].schedule([...]).Dequeue(context, [...])`"
                else:
                    return f"'Dequeue' is a workflow and can not be called from a '{type(__context__).__name__}'"

            IMPORT_reboot_aio_types.assert_type(
                __context__,
                [IMPORT_reboot_aio_external.ExternalContext, IMPORT_reboot_aio_contexts.WorkflowContext],
                error_message_supplement=error_message_supplement(),
            )

            # UX improvement: check that neither positional argument was accidentally
            # given a gRPC request type.
            IMPORT_reboot_aio_types.assert_not_request_type(__context__, request_type=Queue.DequeueRequest)
            IMPORT_reboot_aio_types.assert_not_request_type(__options__, request_type=Queue.DequeueRequest)

            if isinstance(__request_or_options__, Queue.DequeueRequest):
                assert __request_or_options__ is not None
                assert __options__ is None or isinstance(__options__, IMPORT_reboot_aio_call.Options)
                __options__ = __options__ or IMPORT_reboot_aio_call.Options()

                assert bulk is UNSET
                assert at_most is UNSET

                return await (
                    await __this__.spawn().Dequeue(
                        __context__,
                        __request_or_options__,
                        __options__,
                    )
                )
            else:
                assert __options__ is None
                assert __request_or_options__ is None or isinstance(__request_or_options__, IMPORT_reboot_aio_call.Options)
                __options__ = __request_or_options__ or IMPORT_reboot_aio_call.Options()

                return await (
                    await __this__.spawn().Dequeue(
                        __context__,
                        QueueDequeueRequestFromInputFields(
                            bulk=bulk,
                            at_most=at_most,
                        ),
                        __options__,
                    )
                )

        # Keep the original functions on the client, so old code will
        # continue to work, but use the new 'snake_case' method in
        # the new code.
        dequeue = Dequeue
        @IMPORT_typing.overload
        async def TryDequeue(
            __this__,
            __context__: IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
            __request_or_options__: Queue.TryDequeueRequest,
            __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
        ) -> Queue.TryDequeueResponse:
            ...

        @IMPORT_typing.overload
        async def TryDequeue(
            __this__,
            __context__: IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
            __request_or_options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
            *,
            bulk: IMPORT_typing.Optional[bool] | Unset = UNSET,
            at_most: IMPORT_typing.Optional[int] | Unset = UNSET,
        ) -> Queue.TryDequeueResponse:
            ...

        async def TryDequeue( # type: ignore[misc]
            __this__,
            __context__: IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
            __request_or_options__: IMPORT_typing.Optional[Queue.TryDequeueRequest | IMPORT_reboot_aio_call.Options] = None,
            __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
            *,
            bulk: IMPORT_typing.Optional[bool] | Unset = UNSET,
            at_most: IMPORT_typing.Optional[int] | Unset = UNSET,
        ) -> Queue.TryDequeueResponse:
            # UX improvement: check that neither positional argument was accidentally
            # given a gRPC request type.
            IMPORT_reboot_aio_types.assert_not_request_type(__context__, request_type=Queue.TryDequeueRequest)
            IMPORT_reboot_aio_types.assert_not_request_type(__options__, request_type=Queue.TryDequeueRequest)

            __request__: IMPORT_typing.Optional[Queue.TryDequeueRequest] = None
            if isinstance(__request_or_options__, Queue.TryDequeueRequest):
                assert __request_or_options__ is not None
                assert __options__ is None or isinstance(__options__, IMPORT_reboot_aio_call.Options)

                assert bulk is UNSET
                assert at_most is UNSET

                __request__ = __request_or_options__
            else:
                assert __options__ is None
                assert __request_or_options__ is None or isinstance(__request_or_options__, IMPORT_reboot_aio_call.Options)
                __options__ = __request_or_options__

                __request__ = QueueTryDequeueRequestFromInputFields(
                    bulk=bulk,
                    at_most=at_most,
                )

            # Within a `workflow`, all "bare" calls are
            # `per_workflow()` calls, unless we're within a control
            # loop, in which case they are syntactic sugar for
            # `per_iteration()`.
            if __options__ is None or __options__.idempotency is None:
                if isinstance(__context__, IMPORT_reboot_aio_contexts.WorkflowContext):
                    return await (
                        __this__.per_iteration() if __context__.within_loop()
                        else __this__.per_workflow()
                    ).TryDequeue(
                        __context__,
                        __request__,
                        __options__ or IMPORT_reboot_aio_call.Options(),
                    )
                elif isinstance(__context__, IMPORT_reboot_aio_external.InitializeContext):
                    return await __this__.idempotently().TryDequeue(
                        __context__,
                        __request__,
                        __options__ or IMPORT_reboot_aio_call.Options(),
                    )

            __idempotency__: IMPORT_typing.Optional[IMPORT_reboot_aio_idempotency.Idempotency] = None
            __metadata__: IMPORT_typing.Optional[IMPORT_reboot_aio_types.GrpcMetadata] = None
            __bearer_token__: IMPORT_typing.Optional[str] = None
            if __options__ is not None:
                IMPORT_reboot_aio_types.assert_type(__options__, [IMPORT_reboot_aio_call.Options])
                if __options__.idempotency is not None:
                    __idempotency__ = __options__.idempotency
                if __options__.metadata is not None:
                    __metadata__ = __options__.metadata
                if __options__.bearer_token is not None:
                    __bearer_token__ = __options__.bearer_token

            return QueueTryDequeueResponseFromProto(
                await __this__._workflow(__context__).TryDequeue(
                    __request__,
                    idempotency=__idempotency__,
                    metadata=__metadata__,
                    bearer_token=__bearer_token__,
                )
            )

        # Keep the original functions on the client, so old code will
        # continue to work, but use the new 'snake_case' method in
        # the new code.
        try_dequeue = TryDequeue
        @IMPORT_typing.overload
        async def Empty(
            __this__,
            __context__: IMPORT_reboot_aio_contexts.ReaderContext | IMPORT_reboot_aio_contexts.WriterContext | IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
            __request_or_options__: Queue.EmptyRequest,
            __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
        ) -> Queue.EmptyResponse:
            ...

        @IMPORT_typing.overload
        async def Empty(
            __this__,
            __context__: IMPORT_reboot_aio_contexts.ReaderContext | IMPORT_reboot_aio_contexts.WriterContext | IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
            __request_or_options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
        ) -> Queue.EmptyResponse:
            ...

        async def Empty( # type: ignore[misc]
            __this__,
            __context__: IMPORT_reboot_aio_contexts.ReaderContext | IMPORT_reboot_aio_contexts.WriterContext | IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
            __request_or_options__: IMPORT_typing.Optional[Queue.EmptyRequest | IMPORT_reboot_aio_call.Options] = None,
            __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
        ) -> Queue.EmptyResponse:
            # UX improvement: check that neither positional argument was accidentally
            # given a gRPC request type.
            IMPORT_reboot_aio_types.assert_not_request_type(__context__, request_type=Queue.EmptyRequest)
            IMPORT_reboot_aio_types.assert_not_request_type(__options__, request_type=Queue.EmptyRequest)

            __request__: IMPORT_typing.Optional[Queue.EmptyRequest] = None

            if isinstance(__request_or_options__, Queue.EmptyRequest):
                assert __request_or_options__ is not None
                assert __options__ is None or isinstance(__options__, IMPORT_reboot_aio_call.Options)


                __request__ = __request_or_options__
            else:
                assert __options__ is None
                assert __request_or_options__ is None or isinstance(__request_or_options__, IMPORT_reboot_aio_call.Options)
                __options__ = __request_or_options__

                __request__ = QueueEmptyRequestFromInputFields(
                )

            # Within a `workflow`, all "bare" calls are
            # `per_workflow()` calls, unless we're within a control
            # loop, in which case they are syntactic sugar for
            # `per_iteration()`.
            #
            # Unless we are "within until" in which case all "bare"
            # calls are `.always().
            if __options__ is None or __options__.idempotency is None:
                if isinstance(__context__, IMPORT_reboot_aio_contexts.WorkflowContext):
                    return await (
                        __this__.always() if __context__.within_until()
                        else (
                            __this__.per_iteration() if __context__.within_loop()
                            else __this__.per_workflow()
                        )
                    ).Empty(
                        __context__,
                        __request__,
                        __options__ or IMPORT_reboot_aio_call.Options(),
                    )
                elif isinstance(__context__, IMPORT_reboot_aio_external.InitializeContext):
                    return await __this__.idempotently().Empty(
                        __context__,
                        __request__,
                        __options__ or IMPORT_reboot_aio_call.Options(),
                    )

            __metadata__: IMPORT_typing.Optional[IMPORT_reboot_aio_types.GrpcMetadata] = None
            __bearer_token__: IMPORT_typing.Optional[str] = None
            if __options__ is not None:
                IMPORT_reboot_aio_types.assert_type(__options__, [IMPORT_reboot_aio_call.Options])
                if __options__.metadata is not None:
                    __metadata__ = __options__.metadata
                if __options__.bearer_token is not None:
                    __bearer_token__ = __options__.bearer_token
            return QueueEmptyResponseFromProto(
                await __this__._reader(__context__).Empty(
                    __request__,
                    metadata=__metadata__,
                    bearer_token=__bearer_token__,
                    idempotency=__options__.idempotency if __options__ is not None else None,
                )
            )
        # Keep the original functions on the client, so old code will
        # continue to work, but use the new 'snake_case' method in
        # the new code.
        empty = Empty

    class _Forall:

        _ids: list[str]

        def __init__(self, ids: list[str]):
            self._ids = ids

        @IMPORT_typing.overload
        async def Enqueue(
            __this__,
            __context__: IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
            __request_or_options__: Queue.EnqueueRequest,
            __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
        ) -> list[Queue.EnqueueResponse]:
            ...

        @IMPORT_typing.overload
        async def Enqueue(
            __this__,
            __context__: IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
            __request_or_options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
            *,
            value: IMPORT_typing.Optional[google.protobuf.struct_pb2.Value] | Unset = UNSET,
            bytes: IMPORT_typing.Optional[bytes] | Unset = UNSET,
            any: IMPORT_typing.Optional[google.protobuf.any_pb2.Any] | Unset = UNSET,
            items: IMPORT_typing.Optional[IMPORT_typing.Iterable[rbt.std.item.v1.item_pb2.Item]] | Unset = UNSET,
        ) -> list[Queue.EnqueueResponse]:
            ...

        async def Enqueue( # type: ignore[misc]
            # In methods which are dealing with user input, (i.e.,
            # proto message field names), we should use '__double_underscored__'
            # variables to avoid any potential name conflicts with the method's
            # parameters.
            # The '__self__' parameter is a convention in Python to
            # indicate that this method is a bound method, so we use
            # '__this__' instead.
            __this__,
            __context__: IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
            __request_or_options__: IMPORT_typing.Optional[Queue.EnqueueRequest | IMPORT_reboot_aio_call.Options] = None,
            __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
            *,
            value: IMPORT_typing.Optional[google.protobuf.struct_pb2.Value] | Unset = UNSET,
            bytes: IMPORT_typing.Optional[bytes] | Unset = UNSET,
            any: IMPORT_typing.Optional[google.protobuf.any_pb2.Any] | Unset = UNSET,
            items: IMPORT_typing.Optional[IMPORT_typing.Iterable[rbt.std.item.v1.item_pb2.Item]] | Unset = UNSET,
        ) -> list[Queue.EnqueueResponse]:
            if isinstance(__request_or_options__, Queue.EnqueueRequest):
                assert __request_or_options__ is not None
                assert __options__ is None or isinstance(__options__, IMPORT_reboot_aio_call.Options)
                __options__ = __options__ or IMPORT_reboot_aio_call.Options()

                assert value is UNSET
                assert bytes is UNSET
                assert any is UNSET
                assert items is UNSET

                return await IMPORT_asyncio.gather(
                    *[
                        Queue.ref(
                            id
                        ).Enqueue(
                            __context__,
                            __request_or_options__,
                            __options__,
                        ) for id in __this__._ids
                    ]
                )
            else:
                assert __options__ is None
                assert __request_or_options__ is None or isinstance(__request_or_options__, IMPORT_reboot_aio_call.Options)
                __options__ = __request_or_options__ or IMPORT_reboot_aio_call.Options()

                return await IMPORT_asyncio.gather(
                    *[
                        Queue.ref(
                            id
                        ).Enqueue(
                            __context__,
                            QueueEnqueueRequestFromInputFields(
                                value=value,
                                bytes=bytes,
                                any=any,
                                items=items,
                            ),
                            __options__,
                        ) for id in __this__._ids
                    ]
                )

        # Keep the original functions on the client, so old code will
        # continue to work, but use the new 'snake_case' method in
        # the new code.
        enqueue = Enqueue
        @IMPORT_typing.overload
        async def TryDequeue(
            __this__,
            __context__: IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
            __request_or_options__: Queue.TryDequeueRequest,
            __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
        ) -> list[Queue.TryDequeueResponse]:
            ...

        @IMPORT_typing.overload
        async def TryDequeue(
            __this__,
            __context__: IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
            __request_or_options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
            *,
            bulk: IMPORT_typing.Optional[bool] | Unset = UNSET,
            at_most: IMPORT_typing.Optional[int] | Unset = UNSET,
        ) -> list[Queue.TryDequeueResponse]:
            ...

        async def TryDequeue( # type: ignore[misc]
            # In methods which are dealing with user input, (i.e.,
            # proto message field names), we should use '__double_underscored__'
            # variables to avoid any potential name conflicts with the method's
            # parameters.
            # The '__self__' parameter is a convention in Python to
            # indicate that this method is a bound method, so we use
            # '__this__' instead.
            __this__,
            __context__: IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
            __request_or_options__: IMPORT_typing.Optional[Queue.TryDequeueRequest | IMPORT_reboot_aio_call.Options] = None,
            __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
            *,
            bulk: IMPORT_typing.Optional[bool] | Unset = UNSET,
            at_most: IMPORT_typing.Optional[int] | Unset = UNSET,
        ) -> list[Queue.TryDequeueResponse]:
            if isinstance(__request_or_options__, Queue.TryDequeueRequest):
                assert __request_or_options__ is not None
                assert __options__ is None or isinstance(__options__, IMPORT_reboot_aio_call.Options)
                __options__ = __options__ or IMPORT_reboot_aio_call.Options()

                assert bulk is UNSET
                assert at_most is UNSET

                return await IMPORT_asyncio.gather(
                    *[
                        Queue.ref(
                            id
                        ).TryDequeue(
                            __context__,
                            __request_or_options__,
                            __options__,
                        ) for id in __this__._ids
                    ]
                )
            else:
                assert __options__ is None
                assert __request_or_options__ is None or isinstance(__request_or_options__, IMPORT_reboot_aio_call.Options)
                __options__ = __request_or_options__ or IMPORT_reboot_aio_call.Options()

                return await IMPORT_asyncio.gather(
                    *[
                        Queue.ref(
                            id
                        ).TryDequeue(
                            __context__,
                            QueueTryDequeueRequestFromInputFields(
                                bulk=bulk,
                                at_most=at_most,
                            ),
                            __options__,
                        ) for id in __this__._ids
                    ]
                )

        # Keep the original functions on the client, so old code will
        # continue to work, but use the new 'snake_case' method in
        # the new code.
        try_dequeue = TryDequeue
        @IMPORT_typing.overload
        async def Empty(
            __this__,
            __context__: IMPORT_reboot_aio_contexts.ReaderContext | IMPORT_reboot_aio_contexts.WriterContext | IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
            __request_or_options__: Queue.EmptyRequest,
            __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
        ) -> list[Queue.EmptyResponse]:
            ...

        @IMPORT_typing.overload
        async def Empty(
            __this__,
            __context__: IMPORT_reboot_aio_contexts.ReaderContext | IMPORT_reboot_aio_contexts.WriterContext | IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
            __request_or_options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
        ) -> list[Queue.EmptyResponse]:
            ...

        async def Empty( # type: ignore[misc]
            # In methods which are dealing with user input, (i.e.,
            # proto message field names), we should use '__double_underscored__'
            # variables to avoid any potential name conflicts with the method's
            # parameters.
            # The '__self__' parameter is a convention in Python to
            # indicate that this method is a bound method, so we use
            # '__this__' instead.
            __this__,
            __context__: IMPORT_reboot_aio_contexts.ReaderContext | IMPORT_reboot_aio_contexts.WriterContext | IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
            __request_or_options__: IMPORT_typing.Optional[Queue.EmptyRequest | IMPORT_reboot_aio_call.Options] = None,
            __options__: IMPORT_typing.Optional[IMPORT_reboot_aio_call.Options] = None,
        ) -> list[Queue.EmptyResponse]:
            if isinstance(__request_or_options__, Queue.EmptyRequest):
                assert __request_or_options__ is not None
                assert __options__ is None or isinstance(__options__, IMPORT_reboot_aio_call.Options)
                __options__ = __options__ or IMPORT_reboot_aio_call.Options()


                return await IMPORT_asyncio.gather(
                    *[
                        Queue.ref(
                            id
                        ).Empty(
                            __context__,
                            __request_or_options__,
                            __options__,
                        ) for id in __this__._ids
                    ]
                )
            else:
                assert __options__ is None
                assert __request_or_options__ is None or isinstance(__request_or_options__, IMPORT_reboot_aio_call.Options)
                __options__ = __request_or_options__ or IMPORT_reboot_aio_call.Options()

                return await IMPORT_asyncio.gather(
                    *[
                        Queue.ref(
                            id
                        ).Empty(
                            __context__,
                            QueueEmptyRequestFromInputFields(
                            ),
                            __options__,
                        ) for id in __this__._ids
                    ]
                )

        # Keep the original functions on the client, so old code will
        # continue to work, but use the new 'snake_case' method in
        # the new code.
        empty = Empty

    @classmethod
    def forall(cls, ids: list[str]) -> Queue._Forall:
        return Queue._Forall(ids)

    @classmethod
    def ref(
        cls,
        state_id: IMPORT_typing.Optional[IMPORT_reboot_aio_types.StateId] = None,
        *,
        bearer_token: IMPORT_typing.Optional[str] = None,
    ) -> Queue.WeakReference[Queue.WeakReference._Schedule] | Queue.WeakReference[Queue.WeakReference._WriterSchedule]:
        # We support calling `Queue.ref()` with
        # no `state_id` __only__ inside a workflow to be able to call an
        # inline writer, inline reader or other method call, since
        # workflow is a `classmethod` and therefor we can't get a
        # reference to outselves as `self.ref()`.
        if state_id is None:
            context = IMPORT_reboot_aio_contexts.Context.get()

            if context is None:
                raise RuntimeError(
                    'Missing asyncio context variable `context`; '
                    'are you using this class without Reboot?'
                )

            if not isinstance(context, IMPORT_reboot_aio_contexts.WorkflowContext):
                raise RuntimeError(
                    '`ref()` called without a `state_id` can only be used within a Workflow.'
                )

            servicer = QueueBaseServicer.__servicer__.get()

            if servicer is None:
                raise RuntimeError(
                    'Missing asyncio context variable `servicer`; '
                    'are you using this class without Reboot?'
                )

            return Queue.WeakReference(
                # TODO(https://github.com/reboot-dev/mono/issues/3226): add support for calling other applications.
                # For now this always stays within the application that creates the context.
                application_id=None,
                state_id=context._state_ref.id,
                schedule_type=Queue.WeakReference._WriterSchedule,
                # If the user didn't specify a bearer token we may still end up using the app-internal bearer token,
                # but that's decided at the time of the call.
                bearer_token=bearer_token,
                servicer=servicer,
            )

        return Queue.WeakReference(
            # TODO(https://github.com/reboot-dev/mono/issues/3226): add support for calling other applications.
            # For now this always stays within the application that creates the context.
            application_id=None,
            state_id=state_id,
            schedule_type=Queue.WeakReference._Schedule,
            bearer_token=bearer_token,
        )


    @IMPORT_typing.overload
    @classmethod
    def idempotently(cls, alias: IMPORT_typing.Optional[str] = None, *, each_iteration: bool = False) -> Queue._ConstructIdempotently:
        ...

    @IMPORT_typing.overload
    @classmethod
    def idempotently(cls, *, key: IMPORT_uuid.UUID, generated: bool = False) -> Queue._ConstructIdempotently:
        ...

    @classmethod
    def idempotently(
        cls,
        alias: IMPORT_typing.Optional[str] = None,
        *,
        key: IMPORT_typing.Optional[IMPORT_uuid.UUID] = None,
        each_iteration: IMPORT_typing.Optional[bool] = None,
        generated: bool = False,
    ) -> Queue._ConstructIdempotently:
        return Queue._ConstructIdempotently(
            _idempotency=IMPORT_reboot_aio_contexts.Context.idempotency(
                alias=alias,
                key=key,
                each_iteration=each_iteration,
                generated=generated,
            ),
        )

    @classmethod
    def per_workflow(
        cls,
        alias: IMPORT_typing.Optional[str] = None,
    ):
        return cls.idempotently(alias)

    @classmethod
    def per_iteration(
        cls,
        alias: IMPORT_typing.Optional[str] = None,
    ):
        return cls.idempotently(alias, each_iteration=True)

    @classmethod
    def always(cls):
        return cls.idempotently(key=IMPORT_uuid.uuid4(), generated=True)

    @IMPORT_dataclasses.dataclass(frozen=True)
    class _ConstructIdempotently:

        _idempotency: IMPORT_reboot_aio_idempotency.Idempotency



############################ Servicer Node adapters ############################
# Used by Node.js servicer implementations to access Python code and vice-versa.
# Relevant to servicers, irrelevant to clients.

class QueueServicerNodeAdaptor(Queue.singleton.Servicer):

    @classmethod
    async def _wait_for_cancelled(
        cls,
        future: IMPORT_asyncio.Future,
        method: str,
    ):
        while True:
            done, pending = await IMPORT_asyncio.wait(
                [future],
                timeout=5,  # seconds
            )
            # Check if we've timed out and log a warning that their
            # call has been cancelled but it is still running.
            if len(done) == 0:
                logger.warning(
                    f"Call to method '{method}' has been cancelled by the caller, "
                    "BUT WE ARE STILL WAITING for it complete. You can use the promise "
                    "`context.cancelled` to check if the caller has cancelled so you "
                    "don't do unnecessary work or wait for something that may never occur."
                )
                continue
            break

        # Now need to actually `await` the future so that we don't
        # have an unretrieved exception that gets logged.
        #
        # NOTE: this will raise an exception if the method raised even
        # though the call has already been cancelled but it makes it
        # more clear that the method raised so that is why we're not
        # catching and swallowing any exception.
        await future

    def __init__(self):
        self._js_servicer_reference = self._construct_js_servicer()  # type: ignore[attr-defined]

    def authorizer(self) -> IMPORT_typing.Optional[IMPORT_rebootdev.aio.auth.authorizers.Authorizer]:
        return self._construct_authorizer(self._js_servicer_reference)  # type: ignore[attr-defined]

    async def _read(
        self,
        context: IMPORT_reboot_aio_contexts.WorkflowContext,
        json_options: str,
    ) -> str:
        options = IMPORT_json.loads(json_options)

        alias = options.get('alias')

        assert 'how' in options
        how = options['how']
        if how == IMPORT_reboot_aio_workflows.ALWAYS:
            assert alias is None
            return IMPORT_google_protobuf_json_format.MessageToJson(
                await super().state.always().read(context)
            )

        assert how in [
            IMPORT_reboot_aio_workflows.PER_WORKFLOW,
            IMPORT_reboot_aio_workflows.PER_ITERATION,
        ]

        return IMPORT_google_protobuf_json_format.MessageToJson(
            await (
                super().state.per_workflow(alias)
                if how == IMPORT_reboot_aio_workflows.PER_WORKFLOW
                else super().state.per_iteration(alias)
            ).read(context)
        )

    async def _write(
        self,
        context: IMPORT_reboot_aio_contexts.WorkflowContext,
        writer: IMPORT_typing.Callable[[str], IMPORT_typing.Awaitable[str]],
        json_options: str,
    ) -> str:

        async def _writer(state: IMPORT_google_protobuf_message.Message):
            with IMPORT_reboot_aio_tracing.span(
                state_name=f"{context.state_type_name}('{context.state_id}')",
                span_name="_writer on NodeAdaptor",
                # The naming above matches Python, but not TypeScript.
                python_specific=True,
                level=IMPORT_reboot_aio_tracing.TraceLevel.CUSTOMER,
            ):
                json_result_state = await writer(
                    IMPORT_google_protobuf_json_format.MessageToJson(state)
                )

                with IMPORT_reboot_aio_tracing.span(
                    state_name=f"{context.state_type_name}('{context.state_id}')",
                    span_name="_write - State Copy on NodeAdaptor",
                    # The naming above matches Python, but not TypeScript.
                    python_specific=True,
                    level=IMPORT_reboot_aio_tracing.TraceLevel.CUSTOMER,
                ):
                    result_state = IMPORT_json.loads(json_result_state)

                    state.CopyFrom(
                        IMPORT_google_protobuf_json_format.ParseDict(
                            result_state['state'],
                            self.__state_type__(),
                        )
                    )

                    assert 'result' in result_state
                    result = result_state['result']
                    assert type(result) == str
                    return result

        options = IMPORT_json.loads(json_options)

        alias = options.get('alias')

        assert 'how' in options
        how = options['how']

        if how == IMPORT_reboot_aio_workflows.ALWAYS:
            assert alias is None
            return await super().state.always().write(
                context,
                _writer,
            )

        assert how in [
            IMPORT_reboot_aio_workflows.PER_WORKFLOW,
            IMPORT_reboot_aio_workflows.PER_ITERATION,
        ]

        return await (
            super().state.per_workflow(alias)
            if how == IMPORT_reboot_aio_workflows.PER_WORKFLOW
            else super().state.per_iteration(alias)
        ).write(context, _writer, type=str)

    # Queue specific methods:
    async def Enqueue(
        self,
        context: IMPORT_reboot_aio_contexts.TransactionContext,
        state: rbt.std.collections.queue.v1.queue_pb2.Queue,
        request: rbt.std.collections.queue.v1.queue_pb2.EnqueueRequest,
    ) -> rbt.std.collections.queue.v1.queue_pb2.EnqueueResponse:
        with IMPORT_reboot_aio_tracing.span(
                state_name=f"{context.state_type_name}('{context.state_id}')",
                span_name="NodeAdaptor Enqueue",
                # The naming above matches Python, but not TypeScript.
                python_specific=True,
                level=IMPORT_reboot_aio_tracing.TraceLevel.CUSTOMER,
        ):
            with IMPORT_reboot_aio_tracing.span(
                state_name=f"{context.state_type_name}('{context.state_id}')",
                span_name="Create and serialize `TrampolineCall`",
                # The naming above matches Python, but not TypeScript.
                python_specific=True,
                level=IMPORT_reboot_aio_tracing.TraceLevel.CUSTOMER,
            ):
                bytes_call = IMPORT_rbt_v1alpha1_nodejs_pb2.TrampolineCall(
                    kind=IMPORT_rbt_v1alpha1_nodejs_pb2.transaction,
                    context=IMPORT_rbt_v1alpha1_nodejs_pb2.Context(
                        method='Enqueue',
                        state_id=context.state_id,
                        state_type_name=context.state_type_name,
                        caller_bearer_token=context.caller_bearer_token,
                        cookie=context.cookie,
                        app_internal=context.app_internal,
                        auth=(
                            None if context.auth is None
                            else context.auth.to_proto_bytes()
                        ),
                    ),
                    state=state.SerializeToString(),
                    request=request.SerializeToString(),
                ).SerializeToString()

            cancelled: IMPORT_asyncio.Future[None] = IMPORT_asyncio.Future()

            bytes_result_future: IMPORT_typing.Optional[IMPORT_asyncio.Future[str]] = None

            try:
                with IMPORT_reboot_aio_tracing.span(
                    state_name=f"{context.state_type_name}('{context.state_id}')",
                    span_name="trampoline",
                    # The naming above matches Python, but not TypeScript.
                    python_specific=True,
                    level=IMPORT_reboot_aio_tracing.TraceLevel.CUSTOMER,
                ):
                    bytes_result_future = self._trampoline(  # type: ignore[attr-defined]
                        self._js_servicer_reference,
                        context,
                        cancelled,
                        bytes_call,
                    )
                    # NOTE: we need to `asyncio.shield` so that we can still
                    # correctly wait for this future to complete even if we
                    # are cancelled.
                    assert bytes_result_future is not None
                    bytes_result = await IMPORT_asyncio.shield(bytes_result_future)
            except IMPORT_asyncio.CancelledError:
                cancelled.set_result(None)

                # NOTE: we MUST wait for `bytes_result_future` because this
                # is a `writer` or `transaction` and we CAN NOT execute
                # multiple simultaneously.
                if bytes_result_future is not None:
                    await self._wait_for_cancelled(
                        bytes_result_future,
                        'Queue.Enqueue',
                    )

                raise
            except:
                # Make sure we cancel the `cancelled` future either if an
                # exception is thrown or if the result is reeturned so
                # that we don't keep around resources related to it that
                # might cause us to run out of memory or worse, keep Node
                # from exiting because it is waiting for Python.
                cancelled.cancel()
                raise
            else:
                cancelled.cancel()

                with IMPORT_reboot_aio_tracing.span(
                    state_name=f"{context.state_type_name}('{context.state_id}')",
                    span_name="result ParseFromString",
                    # The naming above matches Python, but not TypeScript.
                    python_specific=True,
                    level=IMPORT_reboot_aio_tracing.TraceLevel.CUSTOMER,
                ):
                    result = IMPORT_rbt_v1alpha1_nodejs_pb2.TrampolineResult.FromString(
                        bytes_result
                    )

                if result.HasField('state'):
                    with IMPORT_reboot_aio_tracing.span(
                        state_name=f"{context.state_type_name}('{context.state_id}')",
                        span_name="state ParseFromString",
                        # The naming above matches Python, but not TypeScript.
                        python_specific=True,
                        level=IMPORT_reboot_aio_tracing.TraceLevel.CUSTOMER,
                    ):
                        state.CopyFrom(
                            rbt.std.collections.queue.v1.queue_pb2.Queue.FromString(
                                result.state
                            )
                        )

                if result.HasField('status_json'):
                    raise (
                        Queue
                        .EnqueueAborted
                        .from_status(
                            IMPORT_google_protobuf_json_format.Parse(
                                result.status_json,
                                IMPORT_google_rpc_status_pb2.Status(),
                            )
                        )
                    )

                assert result.HasField('response')

                with IMPORT_reboot_aio_tracing.span(
                    state_name=f"{context.state_type_name}('{context.state_id}')",
                    span_name="response ParseFromString",
                ):
                    return rbt.std.collections.queue.v1.queue_pb2.EnqueueResponse.FromString(result.response)
        raise RuntimeError("Unexpected result from Enqueue")

    @classmethod
    async def Dequeue(
        cls,
        context: IMPORT_reboot_aio_contexts.WorkflowContext,
        request: rbt.std.collections.queue.v1.queue_pb2.DequeueRequest,
    ) -> rbt.std.collections.queue.v1.queue_pb2.DequeueResponse:
        bytes_call = IMPORT_rbt_v1alpha1_nodejs_pb2.TrampolineCall(
            kind=IMPORT_rbt_v1alpha1_nodejs_pb2.workflow,
            context=IMPORT_rbt_v1alpha1_nodejs_pb2.Context(
                method='Dequeue',
                state_id=context.state_id,
                state_type_name=context.state_type_name,
                caller_bearer_token=context.caller_bearer_token,
                cookie=context.cookie,
                app_internal=context.app_internal,
                auth=(
                    None if context.auth is None
                    else context.auth.to_proto_bytes()
                ),
            ),
            request=request.SerializeToString(),
        ).SerializeToString()

        cancelled: IMPORT_asyncio.Future[None] = IMPORT_asyncio.Future()

        # Link up this `cancelled` future with the context so that it
        # waiting within Python via `context.wait()` will correctly
        # propagate `CancelledError` back through Node.js.
        context._cancelled = cancelled

        bytes_result_future: IMPORT_typing.Optional[IMPORT_asyncio.Future[str]] = None

        servicer = cls.__servicer__.get()
        assert servicer is not None

        try:
            bytes_result_future = servicer._trampoline(  # type: ignore[attr-defined]
                servicer._js_servicer_reference,
                context,
                cancelled,
                bytes_call,
            )
            # NOTE: we need to `asyncio.shield` so that we can still
            # correctly wait for this future to complete even if we
            # are cancelled.
            assert bytes_result_future is not None
            bytes_result = await IMPORT_asyncio.shield(bytes_result_future)
        except IMPORT_asyncio.CancelledError:
            cancelled.set_result(None)

            # NOTE: unlike for a `writer` or `transaction`, we DO NOT
            # _need_ to wait for `bytes_result_future` because this is
            # a workflow and we can execute multiple workflows
            # simultaneously. That being said, we still want to give
            # good feedback that the RPC has been cancelled, and there
            # is no harm waiting because other writers can still be
            # called.
            if bytes_result_future is not None:
                await cls._wait_for_cancelled(
                    bytes_result_future,
                    'Queue.Dequeue',
                )

            raise
        except:
            # Make sure we cancel the `cancelled` future either if an
            # exception is thrown or if the result is reeturned so
            # that we don't keep around resources related to it that
            # might cause us to run out of memory or worse, keep Node
            # from exiting because it is waiting for Python.
            cancelled.cancel()
            raise
        else:
            cancelled.cancel()

            result = IMPORT_rbt_v1alpha1_nodejs_pb2.TrampolineResult.FromString(
                bytes_result
            )

            if result.HasField('status_json'):
                raise (
                    Queue
                    .DequeueAborted
                    .from_status(
                        IMPORT_google_protobuf_json_format.Parse(
                            result.status_json,
                            IMPORT_google_rpc_status_pb2.Status(),
                        )
                    )
                )

            assert result.HasField('response')
            return rbt.std.collections.queue.v1.queue_pb2.DequeueResponse.FromString(result.response)
        raise RuntimeError("Unexpected result from Dequeue")

    async def TryDequeue(
        self,
        context: IMPORT_reboot_aio_contexts.TransactionContext,
        state: rbt.std.collections.queue.v1.queue_pb2.Queue,
        request: rbt.std.collections.queue.v1.queue_pb2.DequeueRequest,
    ) -> rbt.std.collections.queue.v1.queue_pb2.DequeueResponse:
        with IMPORT_reboot_aio_tracing.span(
                state_name=f"{context.state_type_name}('{context.state_id}')",
                span_name="NodeAdaptor TryDequeue",
                # The naming above matches Python, but not TypeScript.
                python_specific=True,
                level=IMPORT_reboot_aio_tracing.TraceLevel.CUSTOMER,
        ):
            with IMPORT_reboot_aio_tracing.span(
                state_name=f"{context.state_type_name}('{context.state_id}')",
                span_name="Create and serialize `TrampolineCall`",
                # The naming above matches Python, but not TypeScript.
                python_specific=True,
                level=IMPORT_reboot_aio_tracing.TraceLevel.CUSTOMER,
            ):
                bytes_call = IMPORT_rbt_v1alpha1_nodejs_pb2.TrampolineCall(
                    kind=IMPORT_rbt_v1alpha1_nodejs_pb2.transaction,
                    context=IMPORT_rbt_v1alpha1_nodejs_pb2.Context(
                        method='TryDequeue',
                        state_id=context.state_id,
                        state_type_name=context.state_type_name,
                        caller_bearer_token=context.caller_bearer_token,
                        cookie=context.cookie,
                        app_internal=context.app_internal,
                        auth=(
                            None if context.auth is None
                            else context.auth.to_proto_bytes()
                        ),
                    ),
                    state=state.SerializeToString(),
                    request=request.SerializeToString(),
                ).SerializeToString()

            cancelled: IMPORT_asyncio.Future[None] = IMPORT_asyncio.Future()

            bytes_result_future: IMPORT_typing.Optional[IMPORT_asyncio.Future[str]] = None

            try:
                with IMPORT_reboot_aio_tracing.span(
                    state_name=f"{context.state_type_name}('{context.state_id}')",
                    span_name="trampoline",
                    # The naming above matches Python, but not TypeScript.
                    python_specific=True,
                    level=IMPORT_reboot_aio_tracing.TraceLevel.CUSTOMER,
                ):
                    bytes_result_future = self._trampoline(  # type: ignore[attr-defined]
                        self._js_servicer_reference,
                        context,
                        cancelled,
                        bytes_call,
                    )
                    # NOTE: we need to `asyncio.shield` so that we can still
                    # correctly wait for this future to complete even if we
                    # are cancelled.
                    assert bytes_result_future is not None
                    bytes_result = await IMPORT_asyncio.shield(bytes_result_future)
            except IMPORT_asyncio.CancelledError:
                cancelled.set_result(None)

                # NOTE: we MUST wait for `bytes_result_future` because this
                # is a `writer` or `transaction` and we CAN NOT execute
                # multiple simultaneously.
                if bytes_result_future is not None:
                    await self._wait_for_cancelled(
                        bytes_result_future,
                        'Queue.TryDequeue',
                    )

                raise
            except:
                # Make sure we cancel the `cancelled` future either if an
                # exception is thrown or if the result is reeturned so
                # that we don't keep around resources related to it that
                # might cause us to run out of memory or worse, keep Node
                # from exiting because it is waiting for Python.
                cancelled.cancel()
                raise
            else:
                cancelled.cancel()

                with IMPORT_reboot_aio_tracing.span(
                    state_name=f"{context.state_type_name}('{context.state_id}')",
                    span_name="result ParseFromString",
                    # The naming above matches Python, but not TypeScript.
                    python_specific=True,
                    level=IMPORT_reboot_aio_tracing.TraceLevel.CUSTOMER,
                ):
                    result = IMPORT_rbt_v1alpha1_nodejs_pb2.TrampolineResult.FromString(
                        bytes_result
                    )

                if result.HasField('state'):
                    with IMPORT_reboot_aio_tracing.span(
                        state_name=f"{context.state_type_name}('{context.state_id}')",
                        span_name="state ParseFromString",
                        # The naming above matches Python, but not TypeScript.
                        python_specific=True,
                        level=IMPORT_reboot_aio_tracing.TraceLevel.CUSTOMER,
                    ):
                        state.CopyFrom(
                            rbt.std.collections.queue.v1.queue_pb2.Queue.FromString(
                                result.state
                            )
                        )

                if result.HasField('status_json'):
                    raise (
                        Queue
                        .TryDequeueAborted
                        .from_status(
                            IMPORT_google_protobuf_json_format.Parse(
                                result.status_json,
                                IMPORT_google_rpc_status_pb2.Status(),
                            )
                        )
                    )

                assert result.HasField('response')

                with IMPORT_reboot_aio_tracing.span(
                    state_name=f"{context.state_type_name}('{context.state_id}')",
                    span_name="response ParseFromString",
                ):
                    return rbt.std.collections.queue.v1.queue_pb2.DequeueResponse.FromString(result.response)
        raise RuntimeError("Unexpected result from TryDequeue")

    async def Empty(
        self,
        context: IMPORT_reboot_aio_contexts.ReaderContext,
        state: rbt.std.collections.queue.v1.queue_pb2.Queue,
        request: rbt.std.collections.queue.v1.queue_pb2.EmptyRequest,
    ) -> rbt.std.collections.queue.v1.queue_pb2.EmptyResponse:
        bytes_call = IMPORT_rbt_v1alpha1_nodejs_pb2.TrampolineCall(
            kind=IMPORT_rbt_v1alpha1_nodejs_pb2.reader,
            context=IMPORT_rbt_v1alpha1_nodejs_pb2.Context(
                method='Empty',
                state_id=context.state_id,
                state_type_name=context.state_type_name,
                caller_bearer_token=context.caller_bearer_token,
                cookie=context.cookie,
                app_internal=context.app_internal,
                auth=(
                    None if context.auth is None
                    else context.auth.to_proto_bytes()
                ),
            ),
            state=state.SerializeToString(),
            request=request.SerializeToString(),
        ).SerializeToString()

        cancelled: IMPORT_asyncio.Future[None] = IMPORT_asyncio.Future()

        bytes_result_future: IMPORT_typing.Optional[IMPORT_asyncio.Future[str]] = None

        try:
            bytes_result_future = self._trampoline(  # type: ignore[attr-defined]
                self._js_servicer_reference,
                context,
                cancelled,
                bytes_call,
            )
            # NOTE: we need to `asyncio.shield` so that we can still
            # correctly wait for this future to complete even if we
            # are cancelled.
            assert bytes_result_future is not None
            bytes_result = await IMPORT_asyncio.shield(bytes_result_future)
        except IMPORT_asyncio.CancelledError:
            cancelled.set_result(None)

            # NOTE: unlike for a `writer` or `transaction`, we DO NOT
            # _need_ to wait for `bytes_result_future` because this is a
            # reader and we can execute multiple readers
            # simultaneously. That being said, we still want to give
            # good feedback that the RPC has been cancelled, and there
            # is no harm waiting because other readers can still be
            # called.
            if bytes_result_future is not None:
                await self._wait_for_cancelled(
                    bytes_result_future,
                    'Queue.Empty',
                )

            raise
        except:
            # Make sure we cancel the `cancelled` future either if an
            # exception is thrown or if the result is reeturned so
            # that we don't keep around resources related to it that
            # might cause us to run out of memory or worse, keep Node
            # from exiting because it is waiting for Python.
            cancelled.cancel()
            raise
        else:
            cancelled.cancel()

            result = IMPORT_rbt_v1alpha1_nodejs_pb2.TrampolineResult.FromString(
                bytes_result
            )

            if result.HasField('status_json'):
                raise (
                    Queue
                    .EmptyAborted
                    .from_status(
                        IMPORT_google_protobuf_json_format.Parse(
                            result.status_json,
                            IMPORT_google_rpc_status_pb2.Status(),
                        )
                    )
                )

            assert result.HasField('response')

            return rbt.std.collections.queue.v1.queue_pb2.EmptyResponse.FromString(result.response)
        raise RuntimeError("Unexpected result from Empty")



############################ Reference Node adapters ############################
# Used by Node.js WeakReference implementations to access Python code and
# vice-versa. Relevant to clients.

class QueueWeakReferenceNodeAdaptor(Queue.WeakReference[Queue.WeakReference._Schedule]):

    async def _call(  # type: ignore[override]
        self,
        *,
        callable: IMPORT_typing.Callable[[IMPORT_google_protobuf_message.Message], IMPORT_typing.Awaitable],
        aborted_type: type[IMPORT_rebootdev.aio.aborted.Aborted],
        request_type: type[IMPORT_google_protobuf_message.Message],
        json_request: str,
    ) -> str:
        request = request_type()

        try:
            IMPORT_google_protobuf_json_format.Parse(json_request, request)
            response = await callable(request)
        except IMPORT_google_protobuf_json_format.ParseError as parse_error:
            aborted_error = IMPORT_rebootdev.aio.aborted.SystemAborted(
                IMPORT_rbt_v1alpha1.errors_pb2.Unknown(),
                message=f"{parse_error}; "
                       "This is usually caused by a deeply nested protobuf message, which is not supported by protobuf.\n"
                        "See the limits here: https://protobuf.dev/programming-guides/proto-limits/"
                )

            return IMPORT_json.dumps(
                {
                    'status': IMPORT_google_protobuf_json_format.MessageToDict(
                        aborted_error.to_status()
                    )
                }
            )
        except BaseException as exception:
            if isinstance(exception, aborted_type):
                return IMPORT_json.dumps(
                    {
                        'status': IMPORT_google_protobuf_json_format.MessageToDict(
                            exception.to_status()
                        )
                    }
                )
            raise
        else:
            return IMPORT_json.dumps(
                {
                    'response': IMPORT_google_protobuf_json_format.MessageToDict(
                        response
                    )
                }
            )

    async def _schedule(  # type: ignore[override]
        self,
        *,
        method: str,
        context: IMPORT_reboot_aio_contexts.WriterContext | IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
        schedule: IMPORT_reboot_time_DateTimeWithTimeZone,
        idempotency: IMPORT_typing.Optional[IMPORT_reboot_aio_idempotency.Idempotency],
        request_type: type[IMPORT_google_protobuf_message.Message],
        json_request: str,
    ) -> str:
        request = request_type()

        IMPORT_google_protobuf_json_format.Parse(json_request, request)

        if isinstance(context, IMPORT_reboot_aio_contexts.WriterContext):
            task = await getattr(
                QueueServicerTasks(
                    context=context,
                    state_ref=context._state_ref,
                ),
                method,
            )(request, schedule=schedule)

            return IMPORT_json.dumps(
                {
                    'taskId': IMPORT_google_protobuf_json_format.MessageToDict(
                        task.task_id
                    )
                }
            )

        # Add scheduling information to the metadata.
        metadata: IMPORT_reboot_aio_types.GrpcMetadata = (
            (IMPORT_reboot_aio_headers.TASK_SCHEDULE, schedule.isoformat()),
        )

        task_id = await getattr(super()._tasks(context), method)(
            request,
            idempotency=idempotency,
            metadata=metadata,
        )

        return IMPORT_json.dumps(
            {
                'taskId': IMPORT_google_protobuf_json_format.MessageToDict(task_id)
            }
        )

    async def _reader(  # type: ignore[override]
        self,
        method: str,
        context: IMPORT_reboot_aio_contexts.ReaderContext | IMPORT_reboot_aio_contexts.WriterContext | IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
        request_type: type[IMPORT_google_protobuf_message.Message],
        json_request: str,
        json_options: str,
    ) -> str:
        options = IMPORT_json.loads(json_options)

        idempotency: IMPORT_typing.Optional[IMPORT_reboot_aio_idempotency.Idempotency] = None

        if 'idempotency' in options:
            idempotency = IMPORT_reboot_aio_contexts.Context.idempotency(
                alias=options['idempotency'].get('alias'),
                key=options['idempotency'].get('key'),
                each_iteration=options['idempotency'].get('eachIteration'),
                generated=options['idempotency'].get('generated', False),
            )

        method_handle = IMPORT_functools.partial(
            getattr(super()._reader(context), method),
            bearer_token=options.get("bearerToken"),
            idempotency=idempotency,
        )
        return await self._call(
            callable=method_handle,
            aborted_type=getattr(
                Queue, method + 'Aborted'
            ),
            request_type=request_type,
            json_request=json_request,
        )

    async def _writer(  # type: ignore[override]
        self,
        method: str,
        context: IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
        request_type: type[IMPORT_google_protobuf_message.Message],
        json_request: str,
        json_options: str,
    ) -> str:
        options = IMPORT_json.loads(json_options)

        idempotency: IMPORT_typing.Optional[IMPORT_reboot_aio_idempotency.Idempotency] = None

        if 'idempotency' in options:
            idempotency = IMPORT_reboot_aio_contexts.Context.idempotency(
                alias=options['idempotency'].get('alias'),
                key=options['idempotency'].get('key'),
                each_iteration=options['idempotency'].get('eachIteration'),
                generated=options['idempotency'].get('generated', False),
            )

        if 'schedule' in options:
            when = IMPORT_google_protobuf_timestamp_pb2.Timestamp()
            when.FromJsonString(options['schedule']['when'])
            return await self._schedule(
                method=method,
                context=context,
                schedule=IMPORT_reboot_time_DateTimeWithTimeZone.from_protobuf_timestamp(when),
                idempotency=idempotency,
                request_type=request_type,
                json_request=json_request,
            )

        method_handle = IMPORT_functools.partial(
            getattr(super()._writer(context), method),
            idempotency=idempotency,
            bearer_token=options.get("bearerToken"),
        )
        return await self._call(
            callable=method_handle,
            aborted_type=getattr(
                Queue, method + 'Aborted'
            ),
            request_type=request_type,
            json_request=json_request,
        )

    async def _transaction(  # type: ignore[override]
        self,
        method: str,
        context: IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
        request_type: type[IMPORT_google_protobuf_message.Message],
        json_request: str,
        json_options: str,
    ) -> str:
        options = IMPORT_json.loads(json_options)

        idempotency: IMPORT_typing.Optional[IMPORT_reboot_aio_idempotency.Idempotency] = None

        if 'idempotency' in options:
            idempotency = IMPORT_reboot_aio_contexts.Context.idempotency(
                alias=options['idempotency'].get('alias'),
                key=options['idempotency'].get('key'),
                each_iteration=options['idempotency'].get('eachIteration'),
                generated=options['idempotency'].get('generated', False),
            )

        if 'schedule' in options:
            when = IMPORT_google_protobuf_timestamp_pb2.Timestamp()
            when.FromJsonString(options['schedule']['when'])
            return await self._schedule(
                method=method,
                context=context,
                schedule=IMPORT_reboot_time_DateTimeWithTimeZone.from_protobuf_timestamp(when),
                idempotency=idempotency,
                request_type=request_type,
                json_request=json_request,
            )

        method_handle = IMPORT_functools.partial(
            getattr(super()._workflow(context), method),
            idempotency=idempotency,
            bearer_token=options.get("bearerToken"),
        )
        return await self._call(
            callable=method_handle,
            aborted_type=getattr(
                Queue, method + 'Aborted'
            ),
            request_type=request_type,
            json_request=json_request,
        )

    async def _workflow(  # type: ignore[override]
        self,
        method: str,
        context: IMPORT_reboot_aio_contexts.WriterContext | IMPORT_reboot_aio_contexts.TransactionContext | IMPORT_reboot_aio_contexts.WorkflowContext | IMPORT_reboot_aio_external.ExternalContext,
        request_type: type[IMPORT_google_protobuf_message.Message],
        json_request: str,
        json_options: str,
    ) -> str:
        options = IMPORT_json.loads(json_options)

        idempotency: IMPORT_typing.Optional[IMPORT_reboot_aio_idempotency.Idempotency] = None

        if 'idempotency' in options:
            idempotency = IMPORT_reboot_aio_contexts.Context.idempotency(
                alias=options['idempotency'].get('alias'),
                key=options['idempotency'].get('key'),
                each_iteration=options['idempotency'].get('eachIteration'),
                generated=options['idempotency'].get('generated', False),
            )

        assert 'schedule' in options

        when = IMPORT_google_protobuf_timestamp_pb2.Timestamp()
        when.FromJsonString(options['schedule']['when'])

        return await self._schedule(
            method=method,
            context=context,
            schedule=IMPORT_reboot_time_DateTimeWithTimeZone.from_protobuf_timestamp(when),
            idempotency=idempotency,
            request_type=request_type,
            json_request=json_request,
        )

# yapf: enable
