from pathlib import Path

import pytest
from starkware.starknet.definitions.error_codes import StarknetErrorCode
from starkware.starknet.testing.contract import StarknetContract
from starkware.starknet.testing.starknet import Starknet
from starkware.starkware_utils.error_handling import StarkException

CONTRACTS_DIR = Path('contracts')
DEFAULT_CALLER_ADDRESS = 0


@pytest.fixture
async def contract(starknet: Starknet) -> StarknetContract:
    starknet = await Starknet.empty()

    return await starknet.deploy(
        source=(CONTRACTS_DIR / 'contract.cairo').as_posix(),
        constructor_calldata=[DEFAULT_CALLER_ADDRESS],
    )


@pytest.mark.asyncio
async def test_increase_balance(contract: StarknetContract) -> None:
    response = await contract.get_balance(DEFAULT_CALLER_ADDRESS).call()
    assert response.result[0] == 0

    await contract.increase_balance(amount=10).invoke()

    response = await contract.get_balance(DEFAULT_CALLER_ADDRESS).call()
    assert response.result[0] == 10

    await contract.increase_balance(amount=20).invoke()

    response = await contract.get_balance(DEFAULT_CALLER_ADDRESS).call()
    assert response.result[0] == 30


@pytest.mark.asyncio
async def test_set_owner(contract: StarknetContract) -> None:
    response = await contract.get_owner().call()
    assert response.result == (DEFAULT_CALLER_ADDRESS,)

    # We're allowed to change the owner since get_caller_address() returns to 0
    # and that is the owner we set during contract construction.
    new_owner = 1
    await contract.set_owner(new_owner=new_owner).invoke()

    response = await contract.get_owner().call()
    assert response.result[0] == new_owner

    # Now that we have set the owner to `new_owner`, we are not allowed to
    # change it back since get_caller_address() will still return 0.
    with pytest.raises(StarkException) as e:
        await contract.set_owner(new_owner=new_owner).invoke()
    assert e.value.code == StarknetErrorCode.TRANSACTION_FAILED
    assert f'{new_owner} != {DEFAULT_CALLER_ADDRESS}' in e.value.message
