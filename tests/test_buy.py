import pytest
import time

from eth_account import Account, messages
from brownie import reverts, chain

class TestBuy:
    def gen_vrs(self, _contract, _receiver, _token, _amount, _txId, _pk=pytest.private_key):
        data_buy = {
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"},
                ],
                "Buy": [
                    {"name": "receiver", "type": "address"},
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
            "primaryType": "Buy",
            "message": {
                "receiver": _receiver,
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
    
    def test_buy_unsupported_asset(self, contract, unsupported_erc20_contract):
        buy_struct = {
            'receiver': pytest.receiver.address,
            'token': pytest.unsupported_asset,
            'amount': pytest.amount,
            'txId': pytest.txId
        }
        buy_request = [v for k,v in buy_struct.items()]

        v,r,s = self.gen_vrs(contract.address, 
                        pytest.receiver.address,
                        pytest.unsupported_asset,
                        pytest.amount,
                        pytest.txId)
        
        with reverts("RampService: asset is not supported"):
            contract.buy(buy_request, v,r,s, {'from': pytest.no_role, 'gas_limit': 100000, 'allow_revert': True})

    def test_buy_invalid_signature(self, contract):
        buy_struct = {
            'receiver': pytest.receiver.address,
            'token': pytest.asset,
            'amount': pytest.amount,
            'txId': pytest.txId
        }
        buy_request = [v for k,v in buy_struct.items()]

        v,r,s = self.gen_vrs(contract.address, 
                        pytest.receiver.address,
                        pytest.asset,
                        pytest.amount,
                        pytest.txId,
                        pytest.random_pk)
        
        with reverts("RampService: invalid signature"):
            contract.buy(buy_request, v,r,s, {'from': pytest.owner, 'gas_limit': 100000, 'allow_revert': True})

    def test_buy_erc20_success(self, contract):
        erc20 = contract.erc20_contract
        contract_balance = erc20.balanceOf(contract.address)
        receiver_balance = erc20.balanceOf(pytest.receiver.address)

        buy_struct = {
            'receiver': pytest.receiver.address,
            'token': pytest.asset,
            'amount': pytest.amount,
            'txId': pytest.txId
        }

        buy_request = [v for k,v in buy_struct.items()]

        v,r,s = self.gen_vrs(contract.address, 
                        pytest.receiver.address,
                        pytest.asset,
                        pytest.amount,
                        pytest.txId)

        contract.buy(buy_request, v,r,s, {'from': pytest.owner})
        time.sleep(5)

        # receiver should be received `pytest.amount` Amount
        assert erc20.balanceOf(pytest.receiver.address) == receiver_balance + pytest.amount
        # contract should be lost `pytest.amount` Amount
        assert erc20.balanceOf(contract.address) == contract_balance - pytest.amount
        # assert buyTx mapping log
        assert contract.buyTx(pytest.txId, pytest.asset) == pytest.amount

    def test_buy_duplicate_txid(self, contract):
        txid_amount = contract.buyTx(pytest.txId, pytest.asset)
        # Run buy func if txId is non-existed
        if txid_amount == 0:
            buy_struct = {
                'receiver': pytest.receiver.address,
                'token': pytest.asset,
                'amount': pytest.amount,
                'txId': pytest.txId
            }

            buy_request = [v for k,v in buy_struct.items()]

            v,r,s = self.gen_vrs(contract.address, 
                            pytest.receiver.address,
                            pytest.asset,
                            pytest.amount,
                            pytest.txId)

            contract.buy(buy_request, v,r,s, {'from': pytest.owner})
            time.sleep(5)

        # Run the duplicate txId
        buy_struct = {
                'receiver': pytest.receiver.address,
                'token': pytest.asset,
                'amount': pytest.amount,
                'txId': pytest.txId
            }

        buy_request = [v for k,v in buy_struct.items()]

        v,r,s = self.gen_vrs(contract.address, 
                        pytest.receiver.address,
                        pytest.asset,
                        pytest.amount,
                        pytest.txId)

        with reverts("RampService: txId is existed"):
            contract.buy(buy_request, v,r,s, {'from': pytest.owner, 'gas_limit':100000, 'allow_revert':True})

    def test_buy_native_success(self, contract):
        txId = 'tx-test-native'
        receiver_balance = pytest.receiver.balance()
        contract_balance = contract.balance()

        buy_struct = {
            'receiver': pytest.receiver.address,
            'token': pytest.native,
            'amount': pytest.amount,
            'txId': txId
        }

        buy_request = [v for k,v in buy_struct.items()]

        v,r,s = self.gen_vrs(contract.address, 
                        pytest.receiver.address,
                        pytest.native,
                        pytest.amount,
                        txId)

        contract.buy(buy_request, v,r,s, {'from': pytest.owner})
        time.sleep(5)

        # receiver should be received `pytest.amount` ether
        assert pytest.receiver.balance() == receiver_balance + pytest.amount
        # contract should be lost `pytest.amount` ether
        assert contract.balance() == contract_balance - pytest.amount
        # assert buyTx mapping log
        assert contract.buyTx(txId, pytest.native) == pytest.amount