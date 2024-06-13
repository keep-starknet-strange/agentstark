import asyncio
from nostra import Nostra
from tabulate import tabulate
from utils import print_total_balances, print_interest_rates
from zklend import Zklend

class Agent:
    def __init__(self, account_address, private_key, node_url):
        self.account_address = account_address
        self.private_key = private_key
        self.node_url = node_url

    async def async_init(self):
        self.nostra = Nostra(self.account_address, self.private_key, self.node_url)
        self.zklend = Zklend(self.account_address, self.private_key, self.node_url)
        await self.nostra.async_init()
        await self.zklend.async_init()

    async def total_balance(self):
        nostra_portfolio = await self.nostra.get_portfolio()
        zklend_portfolio = await self.zklend.get_portfolio()
        result = {
            token : {
                "wallet": 0,
                "nostra": 0,
                "zklend": 0
            } for token in self.nostra.portfolio_tokens
        }
        for item in nostra_portfolio:
            symbol = item['symbol']
            result[symbol]['nostra'] = item['itoken_balance']
            result[symbol]['wallet'] = item['token_balance']

        for item in zklend_portfolio:
            symbol = item['symbol']
            result[symbol]['zklend'] = item['ztoken_balance']

        return result

    async def fetch_interest_rates(self):
        nostra_rates = await self.nostra.get_lending_rates()
        zklend_rates = await self.zklend.get_lending_rates()
        interest_rates = {}
        for token in self.nostra.portfolio_tokens:
            if token in interest_rates:
                interest_rates[token]['nostra'] = nostra_rates.get(token, 0)
            else:
                interest_rates[token] = {
                    'nostra': nostra_rates.get(token, 0),
                    'zklend': 0
                }
        for token in self.zklend.portfolio_tokens:
            if token in interest_rates:
                interest_rates[token]['zklend'] = zklend_rates.get(token, 0)
            else:
                interest_rates[token] = {
                    'nostra': nostra_rates.get(token, 0),
                    'zklend': zklend_rates.get(token, 0)
                }
        return interest_rates
    
    async def get_highest_yield(self, interest_rates=None):
        if interest_rates is None:
            interest_rates = await self.fetch_interest_rates()
        curr_highest = 0
        best_protocol = None
        best_yield = 0
        best_token = None
        for token, interest_rates in interest_rates.items():
            for protocol, rate in interest_rates.items():
                if rate > curr_highest:
                    curr_highest = rate
                    best_yield = rate
                    best_protocol = protocol
                    best_token = token

        return {'protocol': best_protocol, 'yield': best_yield, 'token': best_token}
    
    async def swap(self, from_token, to_token, amount = 0):
        # TODO
        pass

    async def deposit(self, token, protocol, amount=None):
        if protocol == 'nostra':
            print(f"depositing {amount} {token} to nostra")
            receipt = await self.nostra.deposit_token(token, amount)
        elif protocol == 'zklend':
            print(f"depositing {amount} {token} to zklend")
            receipt = await self.zklend.deposit_token(token, amount)
        return receipt
    
    def no_open_positions(self, total_balances):
        return all(balance['nostra'] == 0 and balance['zklend'] == 0 for balance in total_balances.values())
    
    def rebalance_needed(self, total_balances, interest_rates, highest_yield):
        return False
    
    async def compounding_profitable(self, total_balances, interest_rates, highest_yield):
        return True
    
    async def compound(self, token, protocol):
        if protocol == 'nostra':
            await self.nostra.compound(token)
        elif protocol == 'zklend':
            await self.zklend.compound(token)

    async def rebalance(self):
        total_balances = await self.total_balance()
        interest_rates = await self.fetch_interest_rates()
        highest_yield = await self.get_highest_yield(interest_rates)

        print_total_balances(total_balances)
        print_interest_rates(interest_rates)
        input("Press Enter to continue...")  # Pause for user input

        # Case 1: No deposits in either market
        if self.no_open_positions(total_balances):
            input(f"Case 1: continue?")
            for token, balance_info in total_balances.items():
                if token != highest_yield['token']:
                    continue
                if balance_info['wallet'] > 0:
                    await self.swap(from_token=token, to_token=highest_yield['token'])
            deposit = await self.deposit(token=highest_yield['token'], protocol=highest_yield['protocol'], amount = total_balances[highest_yield['token']]['wallet'])
            return deposit

        # Case 2: XX
        if self.rebalance_needed(total_balances, highest_yield):
            # TODO
            pass

        else:
            if await self.compounding_profitable(total_balances[highest_yield['token']], highest_yield['yield']):
                # TODO
                receipt = await self.compound(highest_yield['token'], highest_yield['protocol'])
                return receipt
            else:
                # TODO
                pass



        return None


# Usage example
async def main():
    node_url = ...
    address = ...
    private_key = ...
    agent = Agent(address, private_key, node_url)
    await agent.async_init()
    await agent.rebalance()
    await asyncio.sleep(5)
    total_balances = await agent.total_balance()
    print_total_balances(total_balances)


asyncio.run(main())