import json
import secrets

import click
from click.core import Context
from services.external_api.base_client import RetryConfig
from starkware.crypto.signature.signature import private_to_stark_key
from starkware.starknet.cli.starknet_cli import (
    NETWORKS, felt_formatter, parse_inputs,
)
from starkware.starknet.services.api.feeder_gateway.feeder_gateway_client import \
    FeederGatewayClient  # NOQA
from starkware.starknet.services.api.gateway.gateway_client import (
    GatewayClient,
)

from app import RESOURCES_DIR
from app.main import (
    call, deploy, deploy_from_manifest, invoke_through_account, tx_status,
)
from app.utils import hex_to_int


@click.group()
@click.pass_context
@click.option(
    '--starknet-gateway-url', type=str, default=NETWORKS['alpha-goerli'])
def cli(ctx: Context, starknet_gateway_url: str) -> None:
    try:
        with open('manifest.json') as f:
            manifest = json.load(f)
    except FileNotFoundError:
        manifest = None
    try:
        with open('artifacts.json') as f:
            artifacts = json.load(f)
    except FileNotFoundError:
        artifacts = None
    try:
        with open('accounts.json') as f:
            accounts = json.load(f)
    except FileNotFoundError:
        accounts = {}

    ctx.obj = {
        'gateway_client': GatewayClient(
            url=starknet_gateway_url,
            retry_config=RetryConfig(n_retries=1),
        ),
        'feeder_gateway_client': FeederGatewayClient(
            url=starknet_gateway_url,
            retry_config=RetryConfig(n_retries=1),
        ),
        'manifest': manifest,
        'artifacts': artifacts,
        'accounts': {
            name: {
                'key': {
                    'public': hex_to_int(account['key']['public']),
                    'private': hex_to_int(account['key']['private']),
                },
                'contract': {
                    'address': hex_to_int(account['contract']['address']),
                },
            } for name, account in accounts.items()
        },
    }


@cli.command('deploy')
@click.pass_obj
def _deploy(obj: dict) -> None:
    artifacts = []
    for response, artifact in deploy_from_manifest(
            obj['manifest'], obj['gateway_client']):
        artifacts.append(artifact)
        print(f'Deployed {artifact["name"]} to {artifact["contract_address"]}')
        print(f'Transaction: {response["transaction_hash"]}')
    with open('artifacts.json', 'w') as f:
        json.dump(artifacts, f, indent=2)


@cli.command('call')
@click.option('--contract', type=str)
@click.option('--function', type=str)
@click.option('-i', '--input', 'inputs', type=str,  multiple=True)
@click.pass_obj
def _call(
    obj: dict, contract: str, function: str, inputs: list[str],
) -> None:
    contract_address = next((
        hex_to_int(c['contract_address'])
        for c in obj['artifacts']
        if c['name'] == contract))

    response = call(
        contract_address,
        function,
        parse_inputs(inputs),
        obj['feeder_gateway_client'],
    )
    print(*map(felt_formatter, response['result']))


@cli.command('invoke')
@click.option('--contract', type=str)
@click.option('--function', type=str)
@click.option('-i', '--input', 'inputs', type=str,  multiple=True)
@click.option('--account', type=str, default='main')
@click.pass_obj
def _invoke(
    obj: dict, contract: str, function: str, inputs: list[str], account: str,
) -> None:
    contract_address = next((
        c['contract_address']
        for c in obj['artifacts']
        if c['name'] == contract))

    response = invoke_through_account(
        obj['accounts'][account],
        contract_address,
        function,
        inputs,
        obj['gateway_client'],
    )
    print(f"""\
Invoke transaction was sent.
Contract address: {contract_address}
Transaction hash: {response['transaction_hash']}""")


@cli.command('tx_status')
@click.option('--hash', type=str)
@click.pass_obj
def _tx_status(obj: dict, hash: str) -> None:
    response = tx_status(hash, obj['feeder_gateway_client'])
    print(json.dumps(response, indent=4, sort_keys=True))


@cli.command()
@click.option('--account', type=str, default='main')
@click.pass_obj
def generate_key_pair(obj: dict, account: str) -> None:
    private_key = hex_to_int(secrets.token_hex(31))
    public_key = private_to_stark_key(private_key)

    obj['keys'][account] = {
        'public': public_key,
        'private': private_key,
    }

    with open('keys.json', 'w') as f:
        json.dump({
            account: {
                'public': f'0x{pair["public"]:064x}',
                'private': f'0x{pair["private"]:064x}',
            } for account, pair in obj['keys'].items()
        }, f, indent=2)


@cli.group()
def account() -> None:
    pass


@account.command('create')
@click.option('--name', type=str, default='main')
@click.pass_obj
def _create_account(obj: dict, name: str) -> None:
    private_key = hex_to_int(secrets.token_hex(31))
    public_key = private_to_stark_key(private_key)

    _, response = deploy(
        contract_source=(RESOURCES_DIR / 'Account.cairo').as_posix(),
        inputs=[str(public_key)],
        gateway_client=obj['gateway_client'],
    )
    contract_address = hex_to_int(response['address'])
    obj['accounts'][name] = {
        'key': {
            'public': public_key,
            'private': private_key,
        },
        'contract': {
            'address': contract_address,
        },
    }

    with open('accounts.json', 'w') as f:
        json.dump({
            name: {
                'key': {
                    'public': f'0x{account["key"]["public"]:064x}',
                    'private': f'0x{account["key"]["private"]:064x}',
                },
                'contract': {
                    'address': f'0x{account["contract"]["address"]:064x}',
                },
            } for name, account in obj['accounts'].items()
        }, f, indent=2)

    print(f'Created account {name}')
    print(f'Contract address 0x{contract_address:064x}')


@account.command('list')
@click.pass_obj
def _list_accounts(obj: dict) -> None:
    for name, account in obj['accounts'].items():
        print(f'{name}: 0x{account["contract"]["address"]:064x}')
