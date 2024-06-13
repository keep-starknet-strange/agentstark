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

    router_address = 0x041fd22b238fa21cfcf5dd45a8548974d8263b3a531a60388411c5e230f97023

    account = Account(
        address=address,
        client=client,
        key_pair=KeyPair.from_private_key(private_key),
        chain=StarknetChainId.MAINNET,
    )
    router = await Contract.from_address(provider=account, address=router_address, proxy_config=True)
    ETH = await Contract.from_address(provider=account, address=starknet_mainnet_tokens["ETH"])
    USDC = await Contract.from_address(provider=account, address=starknet_mainnet_tokens["USDC"])
    swap_amount = int(1e17)

    invocation = await ETH.functions["approve"].invoke_v1(
        spender=router.address, amount=swap_amount, max_fee=int(1e16)
    )
    time.sleep(2)
    path = [ETH.address, USDC.address]
    invocation = await router.functions["swap_exact_tokens_for_tokens"].invoke_v1(
        amountIn=swap_amount, 
        amountOutMin=1, 
        # path_len=2, 
        path=path, 
        to=account.address, 
        deadline=int(time.time()) + 100, 
        max_fee=int(1e16)
    )
    time.sleep(5)
    usdc_balance = await USDC.functions["balanceOf"].call(account.address)
    print(usdc_balance)

asyncio.run(main())

