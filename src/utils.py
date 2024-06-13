from tabulate import tabulate

def print_total_balances(total_balances):
    total_balances_table = [
        [token, balances['wallet'], balances['nostra'], balances['zklend']]
            for token, balances in total_balances.items()
    ]
    print("Total Balances")
    print(tabulate(total_balances_table, headers=["Token", "Wallet", "Nostra", "Zklend"], tablefmt="grid"))

def print_interest_rates(interest_rates):
    interest_rates_table = [
        [token, rates['nostra'], rates['zklend']]
        for token, rates in interest_rates.items()
    ]
    print("Interest Rates")
    print(tabulate(interest_rates_table, headers=["Token", "Nostra", "Zklend"], tablefmt="grid"))

