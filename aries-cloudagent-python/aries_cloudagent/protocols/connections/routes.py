"""Connection handling admin routes."""
import base64

from aiohttp import web
from aiohttp_apispec import docs, request_schema, response_schema

from marshmallow import fields, Schema

from ...connections.models.connection_record import (
    ConnectionRecord,
    ConnectionRecordSchema,
)
from ...messaging.valid import IndyDID, UUIDFour
from ...storage.error import StorageNotFoundError

from .manager import ConnectionManager
from .messages.connection_invitation import (
    ConnectionInvitation,
    ConnectionInvitationSchema,
)

from ...wallet.base import BaseWallet
from ...wallet.indy import IndyWallet
from ...config.injection_context import InjectionContext

import indy.anoncreds
import indy.did
import indy.pool
import indy.crypto
import indy.pairwise
import json
from indy.error import IndyError, ErrorCode

class ConnectionListSchema(Schema):
    """Result schema for connection list."""

    results = fields.List(
        fields.Nested(ConnectionRecordSchema()),
        description="List of connection records",
    )


class InvitationResultSchema(Schema):
    """Result schema for a new connection invitation."""

    connection_id = fields.Str(
        description="Connection identifier", example=UUIDFour.EXAMPLE
    )
    invitation = fields.Nested(ConnectionInvitationSchema())
    invitation_url = fields.Str(
        description="Invitation URL",
        example="http://192.168.56.101:8020/invite?c_i=eyJAdHlwZSI6Li4ufQ==",
    )


class ConnectionStaticRequestSchema(Schema):
    """Request schema for a new static connection."""

    my_seed = fields.Str(description="Seed to use for the local DID", required=False)
    my_did = fields.Str(
        description="Local DID", required=False, example=IndyDID.EXAMPLE
    )
    their_seed = fields.Str(
        description="Seed to use for the remote DID", required=False
    )
    their_did = fields.Str(
        description="Remote DID", required=False, example=IndyDID.EXAMPLE
    )
    their_verkey = fields.Str(description="Remote verification key", required=False)
    their_endpoint = fields.Str(
        description="URL endpoint for the other party",
        required=False,
        example="http://192.168.56.101:5000",
    )
    their_role = fields.Str(
        description="Role to assign to this connection", required=False
    )
    alias = fields.Str(description="Alias to assign to this connection", required=False)


def connection_sort_key(conn):
    """Get the sorting key for a particular connection."""
    if conn["state"] == ConnectionRecord.STATE_INACTIVE:
        pfx = "2"
    elif conn["state"] == ConnectionRecord.STATE_INVITATION:
        pfx = "1"
    else:
        pfx = "0"
    return pfx + conn["created_at"]


@docs(
    tags=["connection"],
    summary="Query agent-to-agent connections",
    parameters=[
        {
            "name": "alias",
            "in": "query",
            "schema": {"type": "string"},
            "required": False,
        },
        {
            "name": "initiator",
            "in": "query",
            "schema": {"type": "string", "enum": ["self", "external"]},
            "required": False,
        },
        {
            "name": "invitation_key",
            "in": "query",
            "schema": {"type": "string"},
            "required": False,
        },
        {
            "name": "my_did",
            "in": "query",
            "schema": {"type": "string"},
            "required": False,
        },
        {
            "name": "state",
            "in": "query",
            "schema": {
                "type": "string",
                "enum": [
                    "init",
                    "invitation",
                    "request",
                    "response",
                    "active",
                    "error",
                    "inactive",
                ],
            },
            "required": False,
        },
        {
            "name": "their_did",
            "in": "query",
            "schema": {"type": "string"},
            "required": False,
        },
        {
            "name": "their_role",
            "in": "query",
            "schema": {"type": "string"},
            "required": False,
        },
    ],
)
@response_schema(ConnectionListSchema(), 200)
async def connections_list(request: web.BaseRequest):
    """
    Request handler for searching connection records.

    Args:
        request: aiohttp request object

    Returns:
        The connection list response

    """
    context = request.app["request_context"]
    tag_filter = {}
    for param_name in (
        "invitation_id",
        "my_did",
        "their_did",
        "request_id",
    ):
        if param_name in request.query and request.query[param_name] != "":
            tag_filter[param_name] = request.query[param_name]
    post_filter = {}
    for param_name in (
        "alias",
        "initiator",
        "state",
        "their_role",
    ):
        if param_name in request.query and request.query[param_name] != "":
            post_filter[param_name] = request.query[param_name]
    records = await ConnectionRecord.query(context, tag_filter, post_filter)
    results = []

    for record in records:
        row = record.serialize()
        # row["activity"] = await record.fetch_activity(context)
        results.append(row)
    # results.sort(key=connection_sort_key)
    return web.json_response(results)


@docs(tags=["connection"], summary="Fetch a single connection record")
@response_schema(ConnectionRecordSchema(), 200)
async def connections_retrieve(request: web.BaseRequest):
    """
    Request handler for fetching a single connection record.

    Args:
        request: aiohttp request object

    Returns:
        The connection record response

    """
    context = request.app["request_context"]
    connection_id = request.match_info["id"]
    try:
        record = await ConnectionRecord.retrieve_by_id(context, connection_id)
    except StorageNotFoundError:
        raise web.HTTPNotFound()
    return web.json_response(record.serialize())


@docs(
    tags=["connection"],
    summary="Create a new connection invitation",
    parameters=[
        {
            "name": "alias",
            "in": "query",
            "schema": {"type": "string"},
            "required": False,
        },
        {
            "name": "accept",
            "in": "query",
            "schema": {"type": "string", "enum": ["none", "auto"]},
            "required": False,
        },
        {"name": "public", "in": "query", "schema": {"type": "int"}, "required": False},
    ],
)
@response_schema(InvitationResultSchema(), 200)
async def connections_create_invitation(request: web.BaseRequest):
    """
    Request handler for creating a new connection invitation.

    Args:
        request: aiohttp request object

    Returns:
        The connection invitation details

    """
    context = request.app["request_context"]
    accept = request.query.get("accept")
    alias = request.query.get("alias")
    public = request.query.get("public")
    multi_use = request.query.get("multi_use")

    if public and not context.settings.get("public_invites"):
        raise web.HTTPForbidden()
    base_url = context.settings.get("invite_base_url")

    connection_mgr = ConnectionManager(context)
    connection, invitation = await connection_mgr.create_invitation(
        accept=accept, public=bool(public), multi_use=bool(multi_use), alias=alias
    )
    result = {
        "connection_id": connection and connection.connection_id,
        "invitation": invitation.serialize(),
        "invitation_url": invitation.to_url(base_url),
    }

    if connection and connection.alias:
        result["alias"] = connection.alias

    return web.json_response(result)


@docs(
    tags=["connection"],
    summary="Receive a new connection invitation",
    parameters=[
        {
            "name": "alias",
            "in": "query",
            "schema": {"type": "string"},
            "required": False,
        },
        {
            "name": "accept",
            "in": "query",
            "schema": {"type": "string", "enum": ["none", "auto"]},
            "required": False,
        },
    ],
)
@request_schema(ConnectionInvitationSchema())
@response_schema(ConnectionRecordSchema(), 200)
async def connections_receive_invitation(request: web.BaseRequest):
    """
    Request handler for receiving a new connection invitation.

    Args:
        request: aiohttp request object

    Returns:
        The resulting connection record details

    """
    # ##################################################
    # This code is for using signing did as pairwise did
    signing_did = None
    
    context = request.app["request_context"]
    if context.settings.get("admin.no_receive_invites"):
        raise web.HTTPForbidden()
    connection_mgr = ConnectionManager(context)

    data = await request.json()
    invitation_json = data['invitation']
   
    if 'signing_did' in data:
        signing_did = data['signing_did']
    # ##################################################
    invitation = ConnectionInvitation.deserialize(invitation_json)

    accept = request.query.get("accept")
    alias = request.query.get("alias")
    connection = await connection_mgr.receive_invitation(
        invitation=invitation, signing_did=signing_did, accept=accept, alias=alias
    )
    return web.json_response(connection.serialize())


@docs(
    tags=["connection"],
    summary="Accept a stored connection invitation",
    parameters=[
        {
            "name": "my_endpoint",
            "in": "query",
            "schema": {"type": "string"},
            "required": False,
        },
        {
            "name": "my_label",
            "in": "query",
            "schema": {"type": "string"},
            "required": False,
        },
    ],
)
@response_schema(ConnectionRecordSchema(), 200)
async def connections_accept_invitation(request: web.BaseRequest):
    """
    Request handler for accepting a stored connection invitation.

    Args:
        request: aiohttp request object

    Returns:
        The resulting connection record details

    """
    context = request.app["request_context"]
    outbound_handler = request.app["outbound_message_router"]
    connection_id = request.match_info["id"]
    try:
        connection = await ConnectionRecord.retrieve_by_id(context, connection_id)
    except StorageNotFoundError:
        raise web.HTTPNotFound()
    connection_mgr = ConnectionManager(context)
    my_label = request.query.get("my_label") or None
    my_endpoint = request.query.get("my_endpoint") or None
    request = await connection_mgr.create_request(connection, my_label, my_endpoint)
    await outbound_handler(request, connection_id=connection.connection_id)
    return web.json_response(connection.serialize())


@docs(
    tags=["connection"],
    summary="Accept a stored connection request",
    parameters=[
        {
            "name": "my_endpoint",
            "in": "query",
            "schema": {"type": "string"},
            "required": False,
        }
    ],
)
@response_schema(ConnectionRecordSchema(), 200)
async def connections_accept_request(request: web.BaseRequest):
    """
    Request handler for accepting a stored connection request.

    Args:
        request: aiohttp request object

    Returns:
        The resulting connection record details

    """
    context = request.app["request_context"]
    outbound_handler = request.app["outbound_message_router"]
    connection_id = request.match_info["id"]
    try:
        connection = await ConnectionRecord.retrieve_by_id(context, connection_id)
    except StorageNotFoundError:
        raise web.HTTPNotFound()
    connection_mgr = ConnectionManager(context)
    my_endpoint = request.query.get("my_endpoint") or None
    request = await connection_mgr.create_response(connection, my_endpoint)
    await outbound_handler(request, connection_id=connection.connection_id)
    return web.json_response(connection.serialize())


@docs(
    tags=["connection"], summary="Assign another connection as the inbound connection"
)
async def connections_establish_inbound(request: web.BaseRequest):
    """
    Request handler for setting the inbound connection on a connection record.

    Args:
        request: aiohttp request object
    """
    context = request.app["request_context"]
    connection_id = request.match_info["id"]
    outbound_handler = request.app["outbound_message_router"]
    inbound_connection_id = request.match_info["ref_id"]
    try:
        connection = await ConnectionRecord.retrieve_by_id(context, connection_id)
    except StorageNotFoundError:
        raise web.HTTPNotFound()
    connection_mgr = ConnectionManager(context)
    await connection_mgr.establish_inbound(
        connection, inbound_connection_id, outbound_handler
    )
    return web.json_response({})


@docs(tags=["connection"], summary="Remove an existing connection record")
async def connections_remove(request: web.BaseRequest):
    """
    Request handler for removing a connection record.

    Args:
        request: aiohttp request object
    """
    context = request.app["request_context"]
    connection_id = request.match_info["id"]
    try:
        connection = await ConnectionRecord.retrieve_by_id(context, connection_id)
    except StorageNotFoundError:
        raise web.HTTPNotFound()
    await connection.delete_record(context)
    return web.json_response({})


@docs(tags=["connection"], summary="Create a new static connection")
@request_schema(ConnectionStaticRequestSchema())
@response_schema(ConnectionRecordSchema(), 200)
async def connections_create_static(request: web.BaseRequest):
    """
    Request handler for creating a new static connection.

    Args:
        request: aiohttp request object

    Returns:
        The new connection record

    """
    context = request.app["request_context"]
    body = await request.json()

    connection_mgr = ConnectionManager(context)
    connection = await connection_mgr.create_static_connection(
        my_seed=body.get("my_seed") or None,
        my_did=body.get("my_did") or None,
        their_seed=body.get("their_seed") or None,
        their_did=body.get("their_did") or None,
        their_verkey=body.get("their_verkey") or None,
        their_endpoint=body.get("their_endpoint") or None,
        their_role=body.get("their_role") or None,
        alias=body.get("alias") or None,
    )
    result = connection.serialize()

    return web.json_response(result)


# Placing Verification key into the ledger
async def putVerificationToLedger(request: web.BaseRequest):
    context                   = request.app['request_context']

    pools                     = await indy.pool.list_pools()
    await indy.pool.set_protocol_version(2)
    pool_handle               = await indy.pool.open_pool_ledger(pools[0]["pool"], "{}")

    content                   = await request.json()
    did                       = content["did"]
    signing_vk                = content['signing_vk']
    signing_did               = content['signing_did']
    wallet: BaseWallet        = await context.inject(BaseWallet, required=False)
    nym_request               = await indy.ledger.build_nym_request(did, signing_did, signing_vk, None, None)
    await indy.ledger.sign_and_submit_request(pool_handle, wallet.handle, did, nym_request)
    
    await indy.pool.close_pool_ledger(pool_handle)
    
    return web.json_response({"status" : "true"})

# Creating Signing DID
async def createSigningDid(request: web.BaseRequest):
    context                   = request.app['request_context']
    wallet: BaseWallet        = await context.inject(BaseWallet, required=False)
    (signing_did, signing_vk) = await indy.did.create_and_store_my_did(wallet.handle, "{}")
    
    return web.json_response({
        'signing_did' : signing_did,
        'signing_vk'   : signing_vk,
    })


# Obtaining the pool handle
async def openPoolInLedger(request: web.BaseRequest):
    context                         = request.app['request_context']
    pools                           =   await indy.pool.list_pools()
    try:
        await indy.pool.set_protocol_version(2)
        temp                        = await indy.pool.open_pool_ledger(pools[0]["pool"], "{}")
        await indy.pool.close_pool_ledger(temp)
    except:
        content                     = await request.json()
        pool_handle                 = content["pool_handle"]
        await indy.pool.close_pool_ledger(pool_handle)
    finally:
        return web.json_response({
            'pool_handle' : pool_handle
        })


# Signing the transaction proposal
async def getSignedTransaction(request: web.BaseRequest):
    info_json           = None
    info                = None
    result              = "Error while signing"
    context             = request.app['request_context']
    wallet: BaseWallet  = await context.inject(BaseWallet, required=False)

    content             = await request.json()
    signing_did         = str(content['signing_did'])
    message             = bytes(content["message"], 'utf-8')

    try:
        info_json       = await indy.did.get_my_did_with_meta(wallet.handle, signing_did)
        info=json.loads(info_json)

        try:
            signature       = await indy.crypto.crypto_sign(wallet.handle, info["verkey"], message)
            result          = signature.decode('iso-8859-15')
        except IndyError as err:
            print(err)

    except IndyError as err:
        print(err)

    return web.json_response({'signature' : result})

# Verify the Signed transaction proposal
async def verifySignedTransaction(request: web.BaseRequest):
    context                     = request.app['request_context']
    
    info_json                   = None
    their_key                   = None
    signature                   = "signature"
    result                      = "Error occured while verification"

    wallet: BaseWallet          = await context.inject(BaseWallet, required=False)
    content                     = await request.json()
    their_did                   = content["their_did"]
    pool_handle                 = content["pool_handle"] #newly added code

    # Getting pool handle
    try:

        await indy.pool.close_pool_ledger(pool_handle)
    except:
        pools                       =   await indy.pool.list_pools()
        await indy.pool.set_protocol_version(2)
        pool_handle                 = await indy.pool.open_pool_ledger(pools[0]["pool"], "{}")
  

    message                     = bytes(content['message'], 'utf-8')
    try:
        signature                   = content['signature'].encode('iso-8859-15')
    except IndyError as err:
        print(err)

    try:
        their_key               = await indy.did.key_for_did(pool_handle, wallet.handle, their_did)
        try:
            result = str(await indy.crypto.crypto_verify(their_key, message, signature))
        except IndyError as err:
            print(err)
    except IndyError as err:
        print(err)
    

    await indy.pool.close_pool_ledger(pool_handle)

    return web.json_response({'status' : result})  


async def register(app: web.Application):
    """Register routes."""

    app.add_routes(
        [
            web.get("/connections", connections_list),
            web.get("/connections/{id}", connections_retrieve),
            web.post("/connections/create-invitation", connections_create_invitation),
            web.post("/connections/open-pool", openPoolInLedger),
            web.post("/connections/create-signing-did", createSigningDid),
            web.post("/connections/put-key-ledger", putVerificationToLedger),
            web.post("/connections/sign-transaction", getSignedTransaction),
            web.post("/connections/verify-transaction", verifySignedTransaction),
            web.post("/connections/receive-invitation", connections_receive_invitation),
            web.post(
                "/connections/{id}/accept-invitation", connections_accept_invitation
            ),
            web.post("/connections/{id}/accept-request", connections_accept_request),
            web.post(
                "/connections/{id}/establish-inbound/{ref_id}",
                connections_establish_inbound,
            ),
            web.post("/connections/{id}/remove", connections_remove),
        ]
    )







