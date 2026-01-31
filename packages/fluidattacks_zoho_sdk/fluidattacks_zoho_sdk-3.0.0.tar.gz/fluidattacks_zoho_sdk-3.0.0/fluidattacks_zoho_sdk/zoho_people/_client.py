import inspect
import logging
from dataclasses import dataclass

from fa_purity import Cmd, FrozenList, Maybe, ResultE, Stream, Unsafe, cast_exception
from fa_purity.json import Primitive, UnfoldedFactory
from fluidattacks_etl_utils.bug import Bug
from fluidattacks_etl_utils.paginate import cursor_pagination

from fluidattacks_zoho_sdk._decoders import assert_single
from fluidattacks_zoho_sdk._http_client import (
    ClientFactory,
    HttpJsonClient,
    RelativeEndpoint,
    TokenManager,
)
from fluidattacks_zoho_sdk._http_client.paginate import FromIndex, Limit, validate_next_page
from fluidattacks_zoho_sdk.auth import Credentials
from fluidattacks_zoho_sdk.zoho_people.core import Leave, LeaveClient, LeaveDay

from ._decode import decode_leaves

LOG = logging.getLogger(__name__)


def get_batch_of_leaves(
    client: HttpJsonClient,
    from_filter: str,
    until_filter: str,
    start_index: Maybe[FromIndex],
    limit: Limit,
) -> Cmd[ResultE[tuple[FrozenList[tuple[Leave, FrozenList[LeaveDay]]], Maybe[FromIndex]]]]:
    current_index = start_index.value_or(FromIndex(0))
    endpoint = RelativeEndpoint.new("people.zoho.com", "v2", "leavetracker", "leaves", "records")
    params: dict[str, Primitive] = {
        "from": from_filter,
        "to": until_filter,
        "startIndex": start_index.value_or(0),
        "limit": limit,
    }

    return client.get(
        endpoint,
        UnfoldedFactory.from_dict(params),
    ).map(
        lambda result: (
            result.alt(
                lambda e: cast_exception(Bug.new("_get_leaves", inspect.currentframe(), e, ())),
            )
            .bind(assert_single)
            .bind(lambda leaves: decode_leaves(leaves))
            .bind(lambda items: validate_next_page(current_index, items, limit))
        ),
    )


def get_batch(
    client: HttpJsonClient,
    from_filter: str,
    until_filter: str,
    start_index: Maybe[FromIndex],
    limit: Limit,
) -> Cmd[tuple[FrozenList[tuple[Leave, FrozenList[LeaveDay]]], Maybe[FromIndex]]]:
    return get_batch_of_leaves(client, from_filter, until_filter, start_index, limit).map(
        lambda r: r.alt(Unsafe.raise_exception).to_union(),
    )


def get_all_leaves(
    client: HttpJsonClient,
    from_filter: str,
    until_filter: str,
    limit: Limit,
) -> Cmd[Stream[FrozenList[tuple[Leave, FrozenList[LeaveDay]]]]]:
    stream = cursor_pagination(
        lambda maybe_nex_batch: get_batch(
            client,
            from_filter,
            until_filter,
            maybe_nex_batch,
            limit,
        ),
    )
    return Cmd.wrap_value(stream)


def _from_client(client: HttpJsonClient) -> LeaveClient:
    return LeaveClient(lambda s, f, j: get_all_leaves(client, s, f, j))


@dataclass(frozen=True)
class LeavesClientFactory:
    @staticmethod
    def new(creds: Credentials, token: TokenManager) -> LeaveClient:
        return _from_client(ClientFactory.new(creds, Maybe.empty(), token))
