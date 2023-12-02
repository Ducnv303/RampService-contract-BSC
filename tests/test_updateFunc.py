import pytest
from brownie import RampService, reverts, accounts

import time

# Block testing updateFuncs
class TestUpdate:
    def test_update_service(self, contract):
        # updateService with ADMIN_ROLE getting AccessControl revertion
        with pytest.raises(ValueError):
            contract.updateService({'from': pytest.admin})

        # updateService with OWNER_ROLE
        before_status = contract.serviceActive()
        contract.updateService({'from': pytest.owner})
        time.sleep(5)
        after_status = contract.serviceActive()
        assert after_status is not before_status

        # rollback to the last state
        contract.updateService({'from': pytest.owner})

    def test_update_asset(self, contract):
        # updateService with NO_ROLE
        with pytest.raises(ValueError):
            contract.updateAsset(pytest.asset, {'from': pytest.no_role})

        # updateService with ADMIN_ROLE
        before_status = contract.supportedAssets(pytest.asset)
        contract.updateAsset(pytest.asset, {'from': pytest.admin})
        time.sleep(5)
        after_status = contract.supportedAssets(pytest.asset)
        assert after_status is not before_status

        # rollback to the last state
        contract.updateAsset(pytest.asset, {'from': pytest.admin})

    def test_update_signer(self, contract):
        # updateSigner with ADMIN_ROLE getting AccessControl revertion
        with pytest.raises(ValueError):
            contract.updateSigner(pytest.signer, {'from': pytest.admin})

        # updateSigner with OWNER_ROLE
        before_status = contract.signers(pytest.signer)
        contract.updateSigner(pytest.signer, {'from': pytest.owner})
        time.sleep(5)
        after_status = contract.signers(pytest.signer)
        assert after_status is not before_status

        # rollback to the last state
        contract.updateSigner(pytest.signer, {'from': pytest.owner})

    def test_update_address_book(self, contract):
        # updateSigner with ADMIN_ROLE getting AccessControl revertion
        with pytest.raises(ValueError):
            contract.updateAddressBook(pytest.receiver, {'from': pytest.admin})

        # updateBook with OWNER_ROLE
        before_status = contract.addressBook(pytest.receiver)
        contract.updateAddressBook(pytest.receiver, {'from': pytest.owner})
        time.sleep(5)
        after_status = contract.addressBook(pytest.receiver)
        assert after_status is not before_status

        # rollback to the last state
        contract.updateAddressBook(pytest.receiver, {'from': pytest.owner})