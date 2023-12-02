import pytest
from brownie import ERC20_Token, RampService, accounts

import web3
from web3 import Web3

pytest.private_key = '0x416b8a7d9290502f5661da81f0cf43893e3d19cb9aea3c426cfb36e8186e9c09'
pytest.random_pk = 'b83208f80f5d885f84f87bb9010a4a28aa99277c6294d9f0ddc2b172965742d1'
pytest.native = web3.constants.ADDRESS_ZERO
pytest.amount = Web3.toWei(0.1, 'ether')
pytest.txId = 'tx-test'


# Block fixture deploy contract
## Ramp contract
@pytest.fixture(scope='session')
def contract():
    pytest.owner = accounts[-1]
    pytest.deployer = accounts[0]
    pytest.admin = accounts[1]
    pytest.signer = accounts.add(pytest.private_key)
    pytest.receiver = accounts[3]
    pytest.no_role = accounts[5]

    contract = RampService.deploy({'from':pytest.deployer})
    ## Grant role
    contract.grantRole(contract.OWNER_ROLE(), pytest.owner, {'from': pytest.deployer})
    contract.grantRole(contract.ADMIN_ROLE(), pytest.admin, {'from': pytest.deployer})

    ## Update signer
    contract.updateSigner(pytest.signer, {'from': pytest.owner})

    # supported erc20_asset
    erc20 = ERC20_Token.deploy(contract.address, Web3.toWei(10000, 'ether'), {'from': pytest.deployer})
    contract.erc20_contract = erc20
    pytest.asset = erc20.address
    contract.updateAsset(pytest.asset, {'from': pytest.admin})
    contract.updateAsset(pytest.native, {'from': pytest.admin})

    pytest.deployer.transfer(contract.address, "2 ether")

    return contract

## ERC20 contract
@pytest.fixture
def erc20_contract(contract):
    erc20 = ERC20_Token.deploy(contract.address, Web3.toWei(10000, 'ether'), {'from': pytest.deployer})
    pytest.asset = erc20.address
    return erc20

## Unsupported ERC20 contract
@pytest.fixture
def unsupported_erc20_contract(contract):
    erc20 = ERC20_Token.deploy(contract.address, Web3.toWei(10000, 'ether'), {'from': pytest.deployer})
    pytest.unsupported_asset = erc20.address
    return erc20

