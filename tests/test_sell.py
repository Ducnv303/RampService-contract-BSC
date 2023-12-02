import pytest
import time

from eth_account import Account, messages
from brownie import reverts, chain

class TestSell:
    def gen_vrs(self, _contract, _token, _amount, _txId, _pk=pytest.private_key):
        data_buy = {
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"},
                ],
                "Sell": [
                    {"name": "token", "type": "address"},
                    {"name": "amount", "type": "uint"},
                    {"name": "txId", "type": "string"},
                ],
            },
            "domain": {
                "name": "ChainVerse|RampService", 
                "chainId": chain.id,
                "verifyingContract": _contract,
            },
            "primaryType": "Sell",
            "message": {
                "token": _token,
                "amount": _amount,
                "txId": _txId
            },
        }

        signed = Account.sign_message(messages.encode_structured_data(data_buy), _pk)

        v = signed.v
        r = signed.r.to_bytes(32, byteorder='big')
        s = signed.s.to_bytes(32, byteorder='big')

        return v,r,s
    
    def test_sell_unsupported_asset(self, contract, unsupported_erc20_contract):
        txId = 'tx-sell-test'
        sell_struct = {
            'token': pytest.unsupported_asset,
            'amount': pytest.amount,
            'txId': txId
        }
        sell_request = [v for k,v in sell_struct.items()]

        v,r,s = self.gen_vrs(contract.address, 
                        pytest.unsupported_asset,
                        pytest.amount,
                        txId)
        
        with reverts("RampService: asset is not supported"):
            contract.sell(sell_request, v,r,s, {'from': pytest.no_role, 'gas_limit': 100000, 'allow_revert': True})
    
    def test_sell_invalid_signature(self, contract):
        txId = 'tx-sell-test'
        sell_struct = {
            'token': pytest.asset,
            'amount': pytest.amount,
            'txId': txId
        }
        sell_request = [v for k,v in sell_struct.items()]

        v,r,s = self.gen_vrs(contract.address, 
                        pytest.asset,
                        pytest.amount,
                        txId,
                        pytest.random_pk)
        
        with reverts("RampService: invalid signature"):
            contract.sell(sell_request, v,r,s, {'from': pytest.no_role, 'gas_limit': 100000, 'allow_revert': True})

    def test_sell_erc20_missing_allowance(self, contract):
        txId = 'tx-sell-test'

        sell_struct = {
            'token': pytest.asset,
            'amount': pytest.amount,
            'txId': txId
        }

        sell_request = [v for k,v in sell_struct.items()]

        v,r,s = self.gen_vrs(contract.address, 
                        pytest.asset,
                        pytest.amount,
                        txId)

        with reverts("ERC20: insufficient allowance"):
            contract.sell(sell_request, v,r,s, {'from': pytest.deployer,'gas_limit': 100000, 'allow_revert': True})

    def test_sell_erc20_amount_exceed_balance(self, contract):
        from web3 import Web3
        txId = 'tx-sell-test'
        amount = Web3.toWei(100000, 'ether')
        sell_struct = {
            'token': pytest.asset,
            'amount': amount,
            'txId': txId
        }

        sell_request = [v for k,v in sell_struct.items()]

        v,r,s = self.gen_vrs(contract.address, 
                        pytest.asset,
                        amount,
                        txId)
        
        erc20 = contract.erc20_contract
        erc20.approve(contract.address, amount, {'from': pytest.deployer})

        with reverts("ERC20: transfer amount exceeds balance"):
            contract.sell(sell_request, v,r,s, {'from': pytest.deployer,'gas_limit': 100000, 'allow_revert': True})

    def test_sell_erc20_success(self, contract):
        txId = 'tx-sell-test'

        erc20 = contract.erc20_contract
        erc20.approve(contract.address, pytest.amount, {'from': pytest.deployer})
        sender_balance = erc20.balanceOf(pytest.deployer.address)
        contract_balance = erc20.balanceOf(contract.address)

        sell_struct = {
            'token': pytest.asset,
            'amount': pytest.amount,
            'txId': txId
        }

        sell_request = [v for k,v in sell_struct.items()]

        v,r,s = self.gen_vrs(contract.address, 
                        pytest.asset,
                        pytest.amount,
                        txId)

        contract.sell(sell_request, v,r,s, {'from': pytest.deployer})
        time.sleep(5)

        # sender should be lost `pytest.amount` Amount
        assert erc20.balanceOf(pytest.deployer.address) == sender_balance - pytest.amount
        # contract should be received `pytest.amount` Amount
        assert erc20.balanceOf(contract.address) == contract_balance + pytest.amount
        # assert sellTx mapping log
        assert contract.sellTx(txId, pytest.asset) == pytest.amount

    def test_sell_duplicate_txid(self, contract):
        txId = 'tx-test-sell'

        erc20 = contract.erc20_contract
        erc20.approve(contract.address, pytest.amount, {'from': pytest.deployer})

        txid_amount = contract.sellTx(txId, pytest.asset)
        # Run sell func if txId is non-existed
        if txid_amount == 0:
            sell_struct = {
                'token': pytest.asset,
                'amount': pytest.amount,
                'txId': txId
            }

            sell_request = [v for k,v in sell_struct.items()]

            v,r,s = self.gen_vrs(contract.address, 
                        pytest.asset,
                        pytest.amount,
                        txId)

            contract.sell(sell_request, v,r,s, {'from': pytest.deployer})
            time.sleep(5)

       # Run the duplicate txId
        sell_struct = {
            'token': pytest.asset,
            'amount': pytest.amount,
            'txId': txId
        }

        sell_request = [v for k,v in sell_struct.items()]

        v,r,s = self.gen_vrs(contract.address, 
                    pytest.asset,
                    pytest.amount,
                    txId)

        with reverts("RampService: txId is existed"):
            contract.sell(sell_request, v,r,s, {'from': pytest.deployer, 'gas_limit':100000, 'allow_revert':True})

    def test_sell_native_not_sending_ether(self, contract):
        txId = 'tx-test-sell-native'

        sell_struct = {
            'token': pytest.native,
            'amount': pytest.amount,
            'txId': txId
        }

        sell_request = [v for k,v in sell_struct.items()]

        v,r,s = self.gen_vrs(contract.address, 
                        pytest.native,
                        pytest.amount,
                        txId)

        with reverts('RampService: amount is wrong'):
            contract.sell(sell_request, v,r,s, {'from': pytest.deployer, 'gas_limit':100000, 'allow_revert':True})

    def test_sell_native_success(self, contract):
        txId = 'tx-test-sell-native'
        sender_balance = pytest.deployer.balance()
        contract_balance = contract.balance()

        sell_struct = {
            'token': pytest.native,
            'amount': pytest.amount,
            'txId': txId
        }

        sell_request = [v for k,v in sell_struct.items()]

        v,r,s = self.gen_vrs(contract.address, 
                        pytest.native,
                        pytest.amount,
                        txId)

        contract.sell(sell_request, v,r,s, {'from': pytest.deployer, 'amount': pytest.amount})
        time.sleep(5)

        # contract should be received `pytest.amount` ether
        assert contract.balance() == contract_balance + pytest.amount
        # assert sellTx mapping log
        assert contract.sellTx(txId, pytest.native) == pytest.amount