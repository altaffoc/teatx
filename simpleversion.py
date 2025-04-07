from web3 import Web3
import secrets
import random
import json

# Load private key from .evm file
def load_private_key():
    with open(".evm", "r") as file:
        return file.read().strip()

# Connect to TEA Sepolia via Alchemy
RPC_URL = "https://tea-sepolia.g.alchemy.com/public"
web3 = Web3(Web3.HTTPProvider(RPC_URL))

# Load wallet credentials
SENDER_ADDRESS = "0x000000XXXXXXX"  # Your wallet address
PRIVATE_KEY = load_private_key()

# Input Token Details
TOKEN_ADDRESS = Web3.to_checksum_address(input("Enter Token Address: "))
MIN_AMOUNT = float(input("Enter Min Token Amount: "))
MAX_AMOUNT = float(input("Enter Max Token Amount: "))

# ERC-20 Token ABI (for transfer function)
ERC20_ABI = json.loads('[{"constant":false,"inputs":[{"name":"recipient","type":"address"},{"name":"amount","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"}]')

token_contract = web3.eth.contract(address=TOKEN_ADDRESS, abi=ERC20_ABI)

# Generate a random Ethereum address
def generate_random_address():
    priv_key = "0x" + secrets.token_hex(32)  # Random private key
    acct = web3.eth.account.from_key(priv_key)
    return acct.address

# Send token transaction function
def send_token_transaction():
    to_address = generate_random_address()
    value = web3.to_wei(random.uniform(MIN_AMOUNT, MAX_AMOUNT), "ether")  # Random token amount

    nonce = web3.eth.get_transaction_count(SENDER_ADDRESS)
    gas_price = web3.eth.gas_price * 2  # Increase the gas price (doubling the default)

    # Ensure gas price is increased if a transaction with the same nonce exists
    try:
        tx = token_contract.functions.transfer(to_address, value).build_transaction({
            "from": SENDER_ADDRESS,
            "nonce": nonce,
            "gas": 100000,  # Adjust if needed
            "gasPrice": gas_price,
            "chainId": web3.eth.chain_id,
        })

        # Sign and send transaction
        signed_tx = web3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

        log_activity(f"Sent {web3.from_wei(value, 'ether')} tokens to {to_address} | TX: {tx_hash.hex()}")

    except Exception as e:
        log_activity(f"Error sending transaction: {str(e)}")

# Logging function
def log_activity(message):
    with open("activity.log", "a") as log_file:
        log_file.write(message + "\n")
    print(message)

# Monitor latest block and trigger TX
def watch_new_blocks():
    latest_block = web3.eth.block_number
    log_activity(f"Started Watching from Block {latest_block}")

    while True:
        new_block = web3.eth.block_number
        if new_block > latest_block:
            log_activity(f"New Block Detected: {new_block}")
            send_token_transaction()
            latest_block = new_block

# Run the script
if __name__ == "__main__":
    watch_new_blocks()
