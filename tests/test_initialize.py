import pytest
from brownie import accounts, reverts

class TestInit:
    def test_initializer_role(self, contract):
        assert contract.hasRole(contract.OWNER_ROLE(), pytest.deployer)
        assert contract.hasRole(contract.ADMIN_ROLE(), pytest.deployer)

    def test_is_service_active(self, contract):
        assert contract.serviceActive() == True

    def test_grant_role(self, contract):
        assert contract.grantRole(contract.ADMIN_ROLE(), pytest.admin, {'from': pytest.deployer})
        with pytest.raises(ValueError):
            contract.grantRole(contract.ADMIN_ROLE(), accounts[2], {'from': pytest.admin})
