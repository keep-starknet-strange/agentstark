import asyncio
from starknet_py.net.account.account import Account
from starknet_py.contract import Contract
from starknet_py.net.models import StarknetChainId
from starknet_py.net.signer.stark_curve_signer import KeyPair
from starknet_py.net.full_node_client import FullNodeClient
from constants import nostra_mainnet_addresses, starknet_mainnet_tokens

class Nostra:
    def __init__(self, account_address, private_key, node_url, chain=StarknetChainId.MAINNET, portfolio_tokens=['USDC', 'USDT']):
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
        interest_rate_model_address = nostra_mainnet_addresses["interestRateModel"]
        interest_rate_model = await Contract.from_address(provider=self.account, address=interest_rate_model_address)
        contracts['interest_rate_model'] = interest_rate_model
        for symbol in portfolio_tokens:
            token_address = starknet_mainnet_tokens[symbol]
            itoken_address = nostra_mainnet_addresses[f"{symbol}nostraInterestBearingTokenAddress"]
            dtoken_address = nostra_mainnet_addresses[f"{symbol}debtTokenAddress"]
            token = await Contract.from_address(provider=self.account, address=token_address)
            itoken = await Contract.from_address(provider=self.account, address=itoken_address)
            dtoken = await Contract.from_address(provider=self.account, address=dtoken_address)
            token_decimals = await token.functions["decimals"].call()
            itoken_decimals = await itoken.functions["decimals"].call()
            dtoken_decimals = await dtoken.functions["decimals"].call()
            contracts[symbol] = {
                "token": token,
                "itoken": itoken,
                "dtoken": dtoken,
                "decimals": token_decimals[0],
                "idecimals": itoken_decimals[0],
                "ddecimals": dtoken_decimals[0]
            }
        return contracts

    async def get_portfolio(self):
        portfolio = []
        for symbol in self.portfolio_tokens:
            token = self.contracts[symbol]
            token_balance = await token["token"].functions["balanceOf"].call(self.account.address)
            itoken_balance = await token["itoken"].functions["balanceOf"].call(self.account.address)
            token_balance = token_balance[0] / 10**token["decimals"]
            itoken_balance = itoken_balance[0] / 10**token["idecimals"]
            if token_balance > 0 or itoken_balance > 0:
                portfolio.append({
                    "symbol": symbol,
                    "token_balance": token_balance,
                    "itoken_balance": itoken_balance
                })
        return portfolio
    
    async def get_lending_rates(self):
        rates = {}
        for symbol in self.portfolio_tokens:
            dtoken = self.contracts[symbol]['dtoken']
            rates_info = await self.contracts['interest_rate_model'].functions["get_interest_state"].call(dtoken.address)
            lending_rate_value = rates_info[0]['lending_rate']
            rates[symbol] = lending_rate_value / 1e18
        return rates

    async def deposit_token(self, token, amount=None):
        # Ensure amount is in the smallest unit of the token (considering decimals, e.g. 1ETH = 1e18)
        if amount is None:
            amount = await self.contracts[token]['token'].functions["balanceOf"].call(self.account.address)
            amount = amount[0]
            # v1 of the agent will run on stables but adding eth handling here for the future
            # we need to leave out some eth for gas
            if token == "ETH":
                amount = max(0, amount - int(1e16))
        
        curr_allowance = await self.contracts[token]['token'].functions["allowance"].call(self.account.address, self.contracts[token]['itoken'].address)
        curr_allowance = curr_allowance[0]
        if curr_allowance < amount:
            await self.contracts[token]['token'].functions["approve"].invoke_v1(
                spender=self.contracts[token]['itoken'].address, amount=amount, max_fee=int(1e16)
            )
        
        invocation = await self.contracts[token]['itoken'].functions["mint"].invoke_v1(
            **{"to": self.account.address, "amount": amount, "max_fee": int(1e16)}
        )
        # await invocation.wait_for_acceptance()
        return invocation

    async def withdraw_token(self, token, amount=None):
        # Withdraw the full balance if no amount is specified
        if amount is None:
            amount = await self.contracts[token]['itoken'].functions["balanceOf"].call(self.account.address)
            amount = amount[0]
        invocation = await self.contracts[token]['itoken'].functions["burn"].invoke_v1(
            **{"from": self.account.address, "to": self.account.address, "amount": amount, "max_fee": int(1e16)}
        )
        # await invocation.wait_for_acceptance()
        return invocation
    
    async def compound(self, token):
        pass
        
        

# Usage
# async def main():
#     node_url = ...
#     address = ...
#     private_key = ...
#     nostra = Nostra(address, private_key, node_url)
#     await nostra.async_init()
#     portfolio = await nostra.get_portfolio()
#     print(portfolio)
#     input()
#     await nostra.deposit_token('USDC', int(1e4))
#     await asyncio.sleep(1)
#     portfolio = await nostra.get_portfolio()
#     print(portfolio)
#     input()
#     await nostra.withdraw_token('USDC', int(1e4)) 
#     await asyncio.sleep(1)
#     portfolio = await nostra.get_portfolio()
#     print(portfolio)
# 
# asyncio.run(main())