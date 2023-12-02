import pytest

from brownie import reverts

class TestforceTransfer:
    def test_force_transfer_admin_caller(self, contract):
        with reverts():
            contract.forceTransfer(pytest.asset, 
                                pytest.amount, 
                                pytest.receiver.address,
                                {'from': pytest.admin, 'gas_limit':100000,'allow_revert':True})

    def test_force_transfer_random_receiver(self, contract):
        with reverts('RampService: address not in addressBook'):
            contract.forceTransfer(pytest.asset, 
                                pytest.amount, 
                                pytest.receiver.address,
                                {'from': pytest.owner, 'gas_limit':100000,'allow_revert':True})
            
    def test_force_transfer_erc20_success(self, contract):
        erc20 = contract.erc20_contract
        contract_balance = erc20.balanceOf(contract.address)
        receiver_balance = erc20.balanceOf(pytest.receiver.address)

        is_whitelist = contract.addressBook(pytest.receiver)
        if not is_whitelist:
            contract.updateAddressBook(pytest.receiver, {'from': pytest.owner})

        contract.forceTransfer(pytest.asset, 
                                pytest.amount, 
                                pytest.receiver.address,
                                {'from': pytest.owner})
        
        # receiver should be received `pytest.amount` Amount
        assert erc20.balanceOf(pytest.receiver.address) == receiver_balance + pytest.amount
        # contract should be lost `pytest.amount` Amount
        assert erc20.balanceOf(contract.address) == contract_balance - pytest.amount

    def test_force_transfer_native_success(self, contract):
        contract_balance = contract.balance()
        receiver_balance = pytest.receiver.balance()

        is_whitelist = contract.addressBook(pytest.receiver)
        if not is_whitelist:
            contract.updateAddressBook(pytest.receiver, {'from': pytest.owner})

        contract.forceTransfer(pytest.native, 
                                pytest.amount, 
                                pytest.receiver.address,
                                {'from': pytest.owner})
        
        # receiver should be received `pytest.amount` ether
        assert pytest.receiver.balance() == receiver_balance + pytest.amount
        # contract should be lost `pytest.amount` ether
        assert contract.balance() == contract_balance - pytest.amount

       