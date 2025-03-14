from web3 import Web3
from typing import List, Dict
import json
import os

class FlareVerifier:
    def __init__(self):
        # Connect to Flare network
        self.w3 = Web3(Web3.HTTPProvider(os.getenv('FLARE_RPC_URL')))
        
        # Load contract ABI and address
        with open('artifacts/contracts/RugPullVerifier.sol/RugPullVerifier.json') as f:
            contract_json = json.load(f)
        contract_abi = contract_json['abi']
        contract_address = os.getenv('VERIFIER_CONTRACT_ADDRESS')
        
        # Initialize contract
        self.contract = self.w3.eth.contract(
            address=contract_address,
            abi=contract_abi
        )
        
        # Set up account
        self.account = self.w3.eth.account.from_key(os.getenv('PRIVATE_KEY'))

    async def verify_transactions(self, high_risk_reports: List[Dict]) -> List[Dict]:
        """
        Submit high-risk transactions for verification on Flare
        """
        verification_results = []
        
        for report in high_risk_reports:
            try:
                # Prepare transaction
                tx = self.contract.functions.storeAuditResult(
                    report['transaction_hash'],
                    report['risk_hash']
                ).build_transaction({
                    'from': self.account.address,
                    'nonce': self.w3.eth.get_transaction_count(self.account.address),
                    'gas': 200000,
                    'gasPrice': self.w3.eth.gas_price
                })
                
                # Sign and send transaction
                signed_tx = self.account.sign_transaction(tx)
                tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                
                # Wait for transaction receipt
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
                
                verification_results.append({
                    'transaction_hash': report['transaction_hash'],
                    'verification_tx': receipt.transactionHash.hex(),
                    'status': 'verified' if receipt.status == 1 else 'failed'
                })
                
            except Exception as e:
                print(f"Error verifying transaction {report['transaction_hash']}: {e}")
                verification_results.append({
                    'transaction_hash': report['transaction_hash'],
                    'status': 'error',
                    'error': str(e)
                })
        
        return verification_results 