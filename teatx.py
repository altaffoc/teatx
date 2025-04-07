from web3 import Web3
import secrets
import random
import json
import threading
import time
import sys

# Load private key via .evm file
def load_private_key():
    with open(".evm", "r") as file:
        return file.read().strip()

# Connect TEA Sepolia via Alchemy
RPC_URL = "https://tea-sepolia.g.alchemy.com/public"
web3 = Web3(Web3.HTTPProvider(RPC_URL))

# Load wallet credentials
SENDER_ADDRESS = "0x0000XXXXXXX"  # Wallet sender
PRIVATE_KEY = load_private_key()

# Input Token Details
TOKEN_ADDRESS = Web3.to_checksum_address(input("Enter Smartcontract Address: "))
MIN_AMOUNT = float(input("Enter Min Send Token Amount: "))
MAX_AMOUNT = float(input("Enter Max Send Amount: "))

# ERC-20 Token ABI (for transfer function)
ERC20_ABI = json.loads('[{"constant":false,"inputs":[{"name":"recipient","type":"address"},{"name":"amount","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"}]')

token_contract = web3.eth.contract(address=TOKEN_ADDRESS, abi=ERC20_ABI)

# Show credits at startup
def show_credits():
    print("\n" + "─" * 40)
    print("  TeaTX by Altaffoc")
    print("─" * 40 + "\n")

# Generate a random Ethereum address
def generate_random_address():
    priv_key = "0x" + secrets.token_hex(32)  # Random private key
    acct = web3.eth.account.from_key(priv_key)
    return acct.address

# Logging function
def log_activity(message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open("activity.log", "a") as log_file:
        log_file.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")

# Spinner for loading animation
def spinning_cursor():
    while True:
        for cursor in '|/-\\':
            yield cursor

# Send token transaction function
def send_token_transaction():
    to_address = generate_random_address()
    value = web3.to_wei(random.uniform(MIN_AMOUNT, MAX_AMOUNT), "ether")  # Random token amount

    nonce = web3.eth.get_transaction_count(SENDER_ADDRESS)
    gas_price = web3.eth.gas_price * 2  # Increase the gas price

    try:
        tx = token_contract.functions.transfer(to_address, value).build_transaction({
            "from": SENDER_ADDRESS,
            "nonce": nonce,
            "gas": 100000,  # Adjust if needed
            "gasPrice": gas_price,
            "chainId": web3.eth.chain_id,
        })

        signed_tx = web3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

        # Loading spinner while waiting for receipt
        spinner = spinning_cursor()
        done = False

        def animate():
            while not done:
                sys.stdout.write(next(spinner))
                sys.stdout.flush()
                sys.stdout.write('\b')
                time.sleep(0.1)

        t = threading.Thread(target=animate)
        t.start()

        # Wait for transaction receipt
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        done = True
        t.join()

        # Clear spinner
        sys.stdout.write(' \b')

        if receipt.status == 1:
            log_activity(f"✅ Sent {web3.from_wei(value, 'ether')} tokens to {to_address} | TX: {tx_hash.hex()}")

    except Exception:
        pass  # Silently ignore errors

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
    show_credits()
    watch_new_blocks()
