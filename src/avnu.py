import asyncio
from starknet_py.net.account.account import Account
from starknet_py.contract import Contract
from starknet_py.net.models import StarknetChainId
from starknet_py.net.signer.stark_curve_signer import KeyPair
from starknet_py.net.full_node_client import FullNodeClient
import time

from constants import starknet_mainnet_tokens

RAY = 1e27

# First, make sure to generate private key and salt
node_url = ...
address = ...
private_key = ...
client = FullNodeClient(node_url=node_url)

async def main():

    exchange = 0x04270219d365d6b017231b52e92b3fb5d7c8378b05e9abc97724537a80e93b0f

    account = Account(
        address=address,
        client=client,
        key_pair=KeyPair.from_private_key(private_key),
        chain=StarknetChainId.MAINNET,
    )
    exchange = await Contract.from_address(provider=account, address=exchange, proxy_config=True)
    ETH = await Contract.from_address(provider=account, address=starknet_mainnet_tokens["ETH"])
    USDC = await Contract.from_address(provider=account, address=starknet_mainnet_tokens["USDC"])
    swap_amount = int(1e17)

    invocation = await ETH.functions["approve"].invoke_v1(
        spender=exchange.address, amount=swap_amount, max_fee=int(1e16)
    )
    time.sleep(2)
    routes= [
      {
        "token_from": 0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7,
        "token_to": 0x53c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8,
        "exchange_address": 0x5dd3d2f4429af886cd1a3b08289dbcea99a294197e9eb43b0e0325b4b,
        "percent": 1,
        "additional_swap_params": [0x0],
      }
    ]
    invocation = await exchange.functions["swap_exact_token_to"].invoke_v1(
        token_from_address=ETH.address, 
        token_from_amount=swap_amount, 
        token_from_max_amount=swap_amount, 
        token_to_address=USDC.address, 
        token_to_amount=0, 
        beneficiary=account.address, 
        routes=routes, 
        max_fee=int(1e16)
    )
    time.sleep(5)
    usdc_balance = await USDC.functions["balanceOf"].call(account.address)
    print(usdc_balance)

asyncio.run(main())

