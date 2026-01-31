<p align="center">
  <img src="logo.svg" alt="getBISy logo" width="400" />
</p>

<p align="center">
  <a href="https://pypi.org/project/getBISy/"><img src="https://badge.fury.io/py/getBISy.svg" alt="PyPI version"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python 3.11+"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="https://pypi.org/project/getBISy/"><img src="https://img.shields.io/pypi/dm/getBISy" alt="Downloads"></a>
</p>

<p align="center">
  <img src="GLI.png" width="49%" />
  <img src="LBS.png" width="49%" />
</p>
<p align="center">
  <img src="OTC.png" width="49%" />
  <img src="DebtSecurities.png" width="49%" />
</p>


A Python package for programmatically fetching and working with Bank for International Settlements (BIS) datasets.

The package currently allows access to the following sets of international financial statistics via the BIS data portal.

- Central Bank policy rates
- Bilateral exchange rates
- Locational banking statistics
- International debt securities
- Global liquidity
- Debt securities
- OTC derivatives
- Exchange-Traded derivatives

All major parameters are declared in custom enums to ensure type safety.

## Installation

```bash
pip install getBISy
```
## Usage

The below covers gathering 4 datasets from the BIS Data Portal using this package: Locational Banking Statistics (LBS); Global Liquidity Indicators (GLI); Over-the-Counter (OTC) Derivatives; and International Debt Securities (IDS).

### Locational Banking Statistics

Import the relevant data functions and enums:

```python
# Test LBS

import getBISy.data as data
import getBISy.enums as enums

# Developing Asia and Pacific, Non-banks, Cross-border Credit, USD
s1 = data.get_locational_banking_data('Q',
                                        enums.LbsMeasure.Stocks,
                                        enums.Position.Claims,
                                        enums.Instrument.LoansAndDeposits,
                                        'USD',
                                        enums.CurrencyType.All,
                                        '5J',
                                        enums.Institution.All,
                                        '5A',
                                        enums.Sector.NonBanks,
                                        enums.Region.DevelopingAsiaAndPacific,
                                        enums.PositionType.CrossBorder)

s1['Description'] = 'Developing Asia and Pacific, Non-banks, Cross-border Credit, USD'

# European Developed Countries, Non-banks, Cross-border Credit, USD
s2 = data.get_locational_banking_data('Q',
                                        enums.LbsMeasure.Stocks,
                                        enums.Position.Claims,
                                        enums.Instrument.LoansAndDeposits,
                                        'USD',
                                        enums.CurrencyType.All,
                                        '5J',
                                        enums.Institution.All,
                                        '5A',
                                        enums.Sector.NonBanks,
                                        enums.Region.EuropeanDevelopedCountries,
                                        enums.PositionType.CrossBorder)
```


### Global Liquidity Indicators

As in the LBS example above, import the relevant functions and enums:

```python 

import getBISy.data as data
import getBISy.enums as enums

s1 = data.get_global_liquidity_data(freq='Q',
                               currency='TO1',
                               borrowing_country=enums.Region.DevelopingAsiaAndPacific,
                               borrowing_sector=enums.Sector.NonFinancialPrivateSector,
                               lending_sector=enums.Sector.Banks,
                               position_type= enums.PositionType.Local,
                               instrument_type=enums.Instrument.Credit,
                               unit_of_measure=enums.UnitOfMeasure.PercentageOfGDP
                               )

s2 = data.get_global_liquidity_data(freq='Q',
                               currency='TO1',
                               borrowing_country=enums.Region.EuroArea,
                               borrowing_sector=enums.Sector.NonFinancialPrivateSector,
                               lending_sector=enums.Sector.Banks,
                               position_type= enums.PositionType.Local,
                               instrument_type=enums.Instrument.Credit,
                               unit_of_measure=enums.UnitOfMeasure.PercentageOfGDP
                               )

```

Given the below plot in the context of the above, we infer that local bank credit to non-financial private sector in Developing Asia is replacing cross-border credit.

### OTC Derivatives

Fetch OTC derivatives notional amounts by risk category (FX vs Interest Rate):

```python
import getBISy.data as data
import getBISy.enums as enums

# Foreign Exchange derivatives
fx_derivatives = data.get_otc_derivatives_data(
    freq='H',
    derivative_type=enums.OtcDerivativeType.NotionalAmounts,
    instrument=enums.OtcDerivativeInstrument.All,
    risk_category=enums.OtcDerivativeRisk.ForeignExchange,
    counterparty_sector=enums.OtcCounterpartySector.All,
    maturity=enums.OtcMaturity.All,
    basis=enums.OtcBasis.NetNet
)

# Interest Rate derivatives
ir_derivatives = data.get_otc_derivatives_data(
    freq='H',
    derivative_type=enums.OtcDerivativeType.NotionalAmounts,
    instrument=enums.OtcDerivativeInstrument.All,
    risk_category=enums.OtcDerivativeRisk.InterestRate,
    counterparty_sector=enums.OtcCounterpartySector.All,
    maturity=enums.OtcMaturity.All,
    basis=enums.OtcBasis.NetNet
)
```

### International Debt Securities

Fetch international debt securities outstanding by issuer residence:

```python
import getBISy.data as data
import getBISy.enums as enums

# Developed Countries
developed = data.get_international_debt_data(
    freq='Q',
    issuer_res=enums.Region.DevelopedCountries,
    issuer_nat=enums.Region.AllCountries,
    issuer_sector_imm=enums.Sector.All,
    issuer_sector_ult=enums.Sector.All,
    issue_curr_group=enums.CurrencyGroup.All,
    issue_orig_mat=enums.Maturity.Total,
    issue_re_mat=enums.Maturity.Total,
    issue_rate=enums.RateType.All,
    measure=enums.IdsMeasure.Outstanding
)

# Emerging & Developing Economies
emerging = data.get_international_debt_data(
    freq='Q',
    issuer_res=enums.Region.EmergingAndDevelopingEconomies,
    issuer_nat=enums.Region.AllCountries,
    issuer_sector_imm=enums.Sector.All,
    issuer_sector_ult=enums.Sector.All,
    issue_curr_group=enums.CurrencyGroup.All,
    issue_orig_mat=enums.Maturity.Total,
    issue_re_mat=enums.Maturity.Total,
    issue_rate=enums.RateType.All,
    measure=enums.IdsMeasure.Outstanding
)
```

Examples of usage of this package can be found on my personal website, [here using the Debt Securities series](https://www.crossbordercode.com/research/U.S.Assets.DuringGFC/U.S.Assets.During.Crisis.html) to comment on the behaviour of foreign capital flows during the GFC, and [here using the Bank Lending series](https://www.crossbordercode.com/research/BankLendingVsCapitalMarkets/BankLendingVsCapitalMarkets.html) to show how cross-border lending has evolved.


## Project Structure
```
getBISy/
├── src/
│   ├── __init__.py
│   ├── data.py         # Main data-fetching functions
│   ├── enums.py        # Enum definitions for all API parameters
│   └── fetcher.py      # Fetcher classes for making API requests
├── requirements.txt
```

## Data Source

This package retrieves data from the [Bank for International Settlements (BIS) Data Portal](https://data.bis.org/). The BIS is an international financial institution that serves central banks and fosters international monetary and financial cooperation.

**Disclaimer:** This package is not affiliated with, endorsed by, or officially connected to the Bank for International Settlements. All data is sourced from publicly available BIS statistics. Users should refer to the [BIS terms of use](https://www.bis.org/terms_conditions.htm) for information about data usage and redistribution.

