import asyncio
from starknet_py.net.account.account import Account
from starknet_py.contract import Contract
from starknet_py.net.models import StarknetChainId
from starknet_py.net.signer.stark_curve_signer import KeyPair
from starknet_py.net.full_node_client import FullNodeClient
import time
from constants import zklend_mainnet_addresses, starknet_mainnet_tokens, RAY

class Zklend:
    def __init__(self, account_address, private_key, node_url, chain=StarknetChainId.MAINNET, portfolio_tokens=['USDC', 'USDT', 'DAI']):
        self.client = FullNodeClient(node_url=node_url)
        self.account = Account(
            address=account_address,
            client=self.client,
            key_pair=KeyPair.from_private_key(private_key),
            chain=chain,
        )
        self.portfolio_tokens = portfolio_tokens
        self.contracts = {}

    async def async_init(self):
        self.contracts = await self._load_contracts(self.portfolio_tokens)

    async def _load_contracts(self, portfolio_tokens):
        contracts = {}
        contracts['markets'] = await Contract.from_address(provider=self.account, address=zklend_mainnet_addresses["markets"])
        for symbol in portfolio_tokens:
            token_address = starknet_mainnet_tokens[symbol]
            ztoken_address = zklend_mainnet_addresses[f"z{symbol}"]
            token = await Contract.from_address(provider=self.account, address=token_address)
            ztoken = await Contract.from_address(provider=self.account, address=ztoken_address)
            token_decimals = await token.functions["decimals"].call()
            ztoken_decimals = await ztoken.functions["decimals"].call()
            contracts[symbol] = {
                "token": token,
                "ztoken": ztoken,
                "decimals": token_decimals[0],
                "zdecimals": ztoken_decimals[0]
            }
        return contracts

    async def get_portfolio(self):
        portfolio = []
        for symbol in self.portfolio_tokens:
            token = self.contracts[symbol]
            token_balance = await token["token"].functions["balanceOf"].call(self.account.address)
            ztoken_balance = await token["ztoken"].functions["balanceOf"].call(self.account.address)
            token_balance = token_balance[0] / 10**token["decimals"]
            ztoken_balance = ztoken_balance[0] / 10**token["zdecimals"]
            if token_balance > 0 or ztoken_balance > 0:
                portfolio.append({
                    "symbol": symbol,
                    "token_balance": token_balance,
                    "ztoken_balance": ztoken_balance
                })
        return portfolio
    
    async def get_lending_rates(self, tokens=None):
        if tokens is None:
            tokens = self.portfolio_tokens
        rates = {}
        for token in tokens:
            rate = await self.contracts['markets'].functions["get_reserve_data"].call(self.contracts[token]['token'].address)
            rate = rate[0]
            rates[token] = float(rate['current_lending_rate']) / RAY
        return rates
    
    async def withdraw_all(self):
        portfolio = await self.get_portfolio()
        for token in portfolio:
            await self.withdraw_token(token['symbol'])
        pass

    async def withdraw_token(self, token, amount=None):
        # amount should already be parsed in native token decimals
        # TODO: double check the withdraw functions expect underlying and not ztoken
        if amount is None:
            await self.contracts['markets'].functions["withdraw_all"].invoke_v1(
                token=self.contracts[token]['token'].address, max_fee=int(1e16)
            )
        else:
            await self.contracts['markets'].functions["withdraw"].invoke_v1(
                token=self.contracts[token]['token'].address, amount=amount, max_fee=int(1e16)
            )
        pass

    async def deposit_token(self, token, amount=None):
        # amount should already be parsed in native token decimals
        # TODO: double check the deposit functions expect underlying and not ztoken
        if amount is None:
            amount = await self.contracts[token]['token'].functions["balanceOf"].call(self.account.address)
            amount = amount[0]
            # v1 of the agent will run on stables but adding eth handling here for the future
            # we need to leave out some eth for gas
            if token == "ETH":
                amount = max(0, amount - int(1e16))
        
        curr_allowance = await self.contracts[token]['token'].functions["allowance"].call(self.account.address, self.contracts["markets"].address)
        curr_allowance = curr_allowance[0]
        if curr_allowance < amount:
            invocation = await self.contracts[token]['token'].functions["approve"].invoke_v1(
                spender=self.contracts["markets"].address, amount=amount, max_fee=int(1e16)
            )
            # await invocation.wait_for_acceptance()
        ### Deposit Token ### 
        invocation = await self.contracts['markets'].functions["deposit"].invoke_v1(
            token=self.contracts[token]['token'].address, amount=amount, max_fee=int(1e16)
        )
        # await invocation.wait_for_acceptance()
        return invocation
    
    async def compound(self, token):
        # TODO
        pass

    # Do you need to enable collateral to be earning yield? If not this func is not needed
    async def enable_collateral(self, token):
        pass


# async def main():
#     node_url = ...
#     address = ...
#     private_key = ...
#     zklend = Zklend(address, private_key, node_url)
#     await zklend.async_init()  # Ensure contracts are loaded
#     lending_rates = await zklend.get_lending_rates()
#     print(lending_rates)
#     portfolio = await zklend.get_portfolio()
#     print(portfolio)
# 
# if __name__ == "__main__":
#     asyncio.run(main())
