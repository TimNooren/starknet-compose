from typing import Any, Iterator, Tuple

from starkware.cairo.common.hash_state import compute_hash_on_elements
from starkware.crypto.signature.signature import sign
from starkware.starknet.cli.starknet_cli import parse_inputs
from starkware.starknet.compiler.compile import compile_starknet_files
from starkware.starknet.public.abi import get_selector_from_name
from starkware.starknet.services.api.feeder_gateway.feeder_gateway_client import \
    FeederGatewayClient  # NOQA
from starkware.starknet.services.api.gateway import transaction
from starkware.starknet.services.api.gateway.gateway_client import (
    GatewayClient,
)

from app.utils import as_sync, hex_to_int


@as_sync
async def deploy(
    contract_source: str, inputs: list[str], gateway_client: GatewayClient,
) -> Tuple[dict, dict]:
    contract_definition = compile_starknet_files([contract_source])

    tx = transaction.Deploy(
        contract_address_salt=0,  # TODO: set salt
        contract_definition=contract_definition,
        constructor_calldata=parse_inputs(inputs),
    )
    return contract_definition.abi, await gateway_client.add_transaction(tx)


def deploy_from_manifest(
    manifest: dict, gateway_client: GatewayClient,
) -> Iterator[Tuple[dict[str, int], dict[str, Any]]]:
    for contract in manifest:
        abi, response = deploy(
            contract['source'],
            contract['inputs'],
            gateway_client,
        )

        yield response, {
            'name': contract['name'],
            'contract_address': response['address'],
            'abi': abi,
        }


@as_sync
async def invoke(
    contract_address: str, function: str, inputs: list[str],
    signature: Tuple[int, int], gateway_client: GatewayClient,
) -> dict[str, int]:
    tx = transaction.InvokeFunction(
        contract_address=contract_address,
        entry_point_selector=get_selector_from_name(function),
        calldata=inputs,
        signature=list(signature),
    )
    return await gateway_client.add_transaction(tx)


def invoke_through_account(
    account: dict, contract_address: str, function: str, inputs: list[str],
    gateway_client: GatewayClient,
) -> dict[str, int]:
    _inputs = [
        contract_address,
        str(get_selector_from_name(function)),
        str(len(inputs)),
        *inputs,
        '0',
    ]

    # Has to match the hashing method in Account.cairo
    signature = sign(
        msg_hash=compute_hash_on_elements([
            account['contract']['address'],
            hex_to_int(contract_address),
            get_selector_from_name(function),
            compute_hash_on_elements(parse_inputs(inputs)),
            0,
        ]),
        priv_key=account['key']['private'],
    )

    return invoke(
        account['contract']['address'],
        'execute',
        parse_inputs(_inputs),
        signature,
        gateway_client,
    )


@as_sync
async def call(
    contract_address: str, function: str, inputs: list[str],
    feeder_gateway_client: FeederGatewayClient,
) -> None:
    tx = transaction.InvokeFunction(
        contract_address=contract_address,
        entry_point_selector=get_selector_from_name(function),
        calldata=inputs,
        signature=[],
    )

    return await feeder_gateway_client.call_contract(tx)


@as_sync
async def tx_status(
    hash: str, feeder_gateway_client: FeederGatewayClient,
) -> None:
    return await feeder_gateway_client.get_transaction_status(hash)
