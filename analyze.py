"""
Analyze a specific company
"""

import yfinance as yf
import yaml
from datetime import datetime
import re

# import pandas as pd

def fill(company: dict, verbose = True) -> None:
    """
    Fills company with info from Yahoo Finance
    Prints the updated info
    
    c must have at least a ticker key, in lowercase
    
    """
    stock = yf.Ticker(company["ticker"])
    
    # Attributes to extract and their new names in the dictionary
    atts = [
        ("cap", "marketCap"),
        ("gross", "grossProfits"),
        ("shares", "sharesOutstanding"),
        ("fcf", "freeCashflow"),
        ("margin_gross", "grossMargins"),
        ("margin_operating", "operatingMargins"),
        ("margin_earnings", "profitMargins"),
        ("revenue_growth", "revenueGrowth"),
        ("price_to_earnings_1yr", "trailingPE"),
        ("name", "longName"),
        ("income","operatingIncome"),
    ]
    # Other attributes: profitMargins, floatShares, , sharesShort, sharesShortPriorMonth, sharesShortPreviousMonthDate, sharesPercentSharesOut, impliedSharesOutstanding, , revenueGrowth
    
    # Extracting and assigning data
    company["did_not_update"] = None
    for new_name, att in atts:
        value = stock.info.get(att)
        if value is not None:  # Check if the value is not None
            company[new_name] = value
        else:
            company["did_not_update"] = att
    
    # Custom fields
    company["stock_price"] = stock.info.get("previousClose") # $/share
    company["price_to_gross"] = company['cap'] / company['gross']
    company["shares"] = company["cap"] / company["stock_price"]
    company["equity"] = stock.balance_sheet.loc["Common Stock Equity"].iloc[0]
    company["total_debt"] = stock.balance_sheet.loc['Total Debt'].iloc[0]
    company["earnings"] = stock.financials.loc["Net Income"].iloc[0]
    
    # Update last_updated, formatted like 202311272013
    company["last_updated"] = datetime.now().strftime("%Y.%m.%d %H:%M")
    company["equity_per_share"] = company.get("equity", 0) / company["shares"]
    
    
    # Print all parameters of company
    if verbose:
        for i in company:
            print(f'{i:>36}: {company[i]}')

# TODO PRETTY PRINT
def update(file_path: str = "companies.yaml", verbose = False) -> None:
    """
    Updates the companies in the YAML file with data from Yahoo Finance. Keeps custom names, and ignores invalid results.
    
    Args:
        file_path (str): _description_
        verbose (bool, optional): _description_. Defaults to False.
    """
    # Reading the YAML file
    with open(file_path, 'r') as file:
        companies = yaml.safe_load(file)

    # Modifying the values
    for company in companies.values():
        fill(company, verbose=False)

    # Saving the modified company back to the YAML file
    with open(file_path, 'w') as file:
        yaml.dump(companies, file)


def analyze_company(c: dict) -> None:
    """
    Calculates valorations from the c company dictionary
    Adds or modifies the values in c
    
    Args:
        c (dict): company dictionary
    
    """
    # TODO price_to_net
    # Valoration - value_to_gross is subjective
    if 'valoration' not in c:
        c['valoration'] = {}
    c_val = c['valoration']
    c_val['value'] = c['equity'] + c_val.get('value_to_gross', -1e15) * c['gross']
    c_val['target_stock_price'] = c_val['value'] / c['shares']
    
    c_val['gain_factor'] = c_val['target_stock_price'] / c['stock_price']
    
    # Add warnings
    c_val['warnings']: str = ""
    
    if (c['cap']/c['gross']) > 10.:
        c_val['warnings'] += f"cap/gross > 10, = {c['cap']/c['gross']:.2f}\n"
    if c['gross'] < .1:
        c_val['warnings'] += f"gross < .1, = {c['gross']:.2f}\n"
    if c['equity'] < 0:
        c_val['warnings'] += f"equity < 0, = {c['equity']/1e6:.2f} million\n"


def update_analysis(file_path: str = "companies.yaml", verbose = False) -> None:
    # Reading the YAML file
    with open(file_path, 'r') as file:
        companies = yaml.safe_load(file)

    # Modifying the values
    for company in companies.values():
        analyze_company(company)

    # Saving the modified company back to the YAML file
    with open(file_path, 'w') as file:
        yaml.dump(companies, file)


if __name__ == "__main__":
    update()
    update_analysis()
    
    # TODO SHOULD MATCH THE PRICE