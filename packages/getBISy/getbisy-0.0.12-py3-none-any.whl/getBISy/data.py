from enum import Enum
from functools import wraps
from typing import Callable, get_type_hints
import inspect

from getBISy.enums import (
    LbsMeasure, Position, Instrument, CurrencyType, Institution, Sector, Region,
    PositionType, CurrencyGroup, Maturity, RateType, IdsMeasure, UnitOfMeasure,
    AccountingEntry, TransactionType, DebtInstrumentType, CurrencyDenomination,
    ValuationMethod, OtcDerivativeType, OtcDerivativeInstrument, OtcDerivativeRisk,
    OtcCounterpartySector, OtcUnderlyingSector, OtcMaturity, OtcRating, OtcBasis
)
from getBISy.fetcher import GenericFetcher, TitleFetcher


def _format_enum_values(enum_class: type) -> str:
    """Format enum values for display in error messages."""
    return ", ".join(f"{member.name}={member.value!r}" for member in enum_class)


def validate_enums(func: Callable) -> Callable:
    """
    Decorator that validates enum parameters at runtime.

    Checks that each argument corresponding to a parameter with an enum type hint
    is a valid member of that enum. Provides helpful error messages showing all
    valid enum values.
    """
    hints = get_type_hints(func)

    # Identify which parameters expect enum types
    enum_params = {
        name: hint for name, hint in hints.items()
        if isinstance(hint, type) and issubclass(hint, Enum)
    }

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Get parameter names from function signature
        sig = inspect.signature(func)
        param_names = list(sig.parameters.keys())

        # Build a dict of all provided arguments
        bound_args = {}
        for i, arg in enumerate(args):
            if i < len(param_names):
                bound_args[param_names[i]] = arg
        bound_args.update(kwargs)

        # Validate enum parameters
        for param_name, enum_class in enum_params.items():
            if param_name in bound_args:
                value = bound_args[param_name]
                if not isinstance(value, enum_class):
                    valid_values = _format_enum_values(enum_class)
                    raise TypeError(
                        f"Parameter '{param_name}' must be a member of {enum_class.__name__}. "
                        f"Got {type(value).__name__}: {value!r}. "
                        f"Valid values are: {valid_values}"
                    )

        return func(*args, **kwargs)

    return wrapper

def get_policy_rate_data(country: str, freq: str) -> str:
    """
    Fetches policy rate data for a given country and frequency.
    
    Args:
        country (str): The country code (e.g., 'US', 'GB').
        freq (str): The frequency of the data (e.g., 'M' for monthly, 'Q' for quarterly).
    
    Returns:
        str: The fetched policy rate data as a string (likely JSON or CSV).
    """
    url = f'WS_CBPOL/~/{freq}.{country}'
    fetcher = GenericFetcher()
    return fetcher.fetch(url)


def get_exchange_rate_data(
    currency: str,
    reference_area: str = None,
    freq: str = 'D',
    collection_indicator: str = 'A'
) -> str:
    """
    Fetches exchange rate data for a given currency, frequency, and collection indicator.
    
    Args:
        currency (str): The currency code (e.g., 'USD', 'EUR').
        freq (str, optional): Data frequency ('D' for daily, 'M' for monthly, etc.). Defaults to 'D'.
        collection_indicator (str, optional): Collection indicator (e.g., 'A'). Defaults to 'A'.
    
    Returns:
        str: The fetched exchange rate data as a string.
    """

    if reference_area is None:
        reference_area = currency[:2]
    url = f'WS_XRU/~/{freq}.{reference_area}.{currency}.{collection_indicator}'
    fetcher = GenericFetcher()
    return fetcher.fetch(url)

def get_effective_exchange_rate_data(
    currency: str,
    type: str = 'R',
    freq: str = 'M',
    basket: str = 'B'
) -> str:
    """
    Fetches effective exchange rate data for a given currency, frequency, and collection indicator.
    
    Args:
        currency (str): The currency code (e.g., 'USD', 'EUR').
        type (str, optional): Type of effective exchange rate ('R' for real, 'N' for nominal). Defaults to 'R'.
        freq (str, optional): Data frequency ('D' for daily, 'M' for monthly, etc.). Defaults to 'M'.
        basket (str, optional): Basket identifier, either broad ('B') or narrow ('N'). Defaults to 'B'.

    Returns:
        str: The fetched effective exchange rate data as a string.
    """
    url = f'WS_EER/~/{freq}.{type}.{basket}.{currency}.'
    fetcher = GenericFetcher()
    return fetcher.fetch(url)


@validate_enums
def get_locational_banking_data(
    freq: str = 'Q',
    measure: LbsMeasure = LbsMeasure.Stocks,
    position: Position = Position.Claims,
    instrument: Instrument = Instrument.All,
    currency: str = 'TO1',
    currency_type: CurrencyType = CurrencyType.All,
    parent: str = '5J',
    reporting_institution: Institution = Institution.All,
    reporting_country: str = '5A',
    counterparty_sector: Sector = Sector.All,
    counterparty_country: Region = Region.LiquidityAllCountries,
    position_type: PositionType = PositionType.All
) -> str:
    """
    Fetches Locational Banking statistics data with various filtering options.
    
    Args:
        freq (str, optional): Data frequency ('Q' for quarterly, etc.). Defaults to 'Q'.
        measure (enums.LbsMeasure, optional): Measure type. Defaults to Stocks.
        position (enums.Position, optional): Position type. Defaults to Claims.
        instrument (enums.Instrument, optional): Instrument type. Defaults to All.
        currency (str, optional): Currency code. Defaults to 'TO1'.
        currency_type (enums.CurrencyType, optional): Currency type. Defaults to All.
        parent (str, optional): Parent region code. Defaults to '5J'.
        reporting_institution (enums.Institution, optional): Reporting institution. Defaults to All.
        reporting_country (str, optional): Reporting country code. Defaults to '5A'.
        counterparty_sector (enums.Sector, optional): Counterparty sector. Defaults to All.
        counterparty_country (enums.Region, optional): Counterparty country/region. Defaults to '5J'.
        position_type (enums.PositionType, optional): Position type. Defaults to All.
    
    Returns:
        str: The fetched locational banking data as a string.
    """
    url = f'WS_LBS_D_PUB/~/{freq}.{measure.value}.{position.value}.{instrument.value}.{currency}.{currency_type.value}.{parent}.{reporting_institution.value}.{reporting_country}.{counterparty_sector.value}.{counterparty_country.value}.{position_type.value}'
    fetcher = GenericFetcher()
    return fetcher.fetch(url)


@validate_enums
def get_international_debt_data(
    freq: str = 'Q',
    issuer_res: Region = Region.AllCountries, 
    issuer_nat: Region = Region.AllCountries, 
    issuer_sector_imm: Sector = Sector.All,
    issuer_sector_ult: Sector = Sector.All,
    market: str = 'C',
    issue_type: str = 'A',
    issue_curr_group: CurrencyGroup = CurrencyGroup.All,
    issue_curr: str = 'A',
    issue_orig_mat: Maturity = Maturity.Total,
    issue_re_mat: Maturity = Maturity.Total,
    issue_rate: RateType = RateType.All,
    issue_risk: str = 'A',
    issue_col: str = 'A',
    measure: IdsMeasure = IdsMeasure.Outstanding
) -> str:
    """
    Fetches International Debt Securities data with various filtering options.
    
    Args:
        freq (str, optional): Data frequency ('Q' for quarterly, etc.). Defaults to 'Q'.
        issuer_res (enums.Region, optional): Issuer residence region. Defaults to AllCountries.
        issuer_nat (enums.Region, optional): Issuer nationality region. Defaults to AllCountries.
        issuer_sector_imm (enums.Sector, optional): Immediate issuer sector. Defaults to All.
        issuer_sector_ult (enums.Sector, optional): Ultimate issuer sector. Defaults to All.
        market (str, optional): Market type. Defaults to 'C'.
        issue_type (str, optional): Issue type. Defaults to 'A'.
        issue_curr_group (enums.CurrencyGroup, optional): Currency group. Defaults to 'A'.
        issue_curr (str, optional): Issue currency. Defaults to 'A'.
        issue_orig_mat (enums.Maturity, optional): Original maturity. Defaults to Total.
        issue_re_mat (enums.Maturity, optional): Residual maturity. Defaults to Total.
        issue_rate (enums.RateType, optional): Rate type. Defaults to All.
        issue_risk (str, optional): Issue risk. Defaults to 'A'.
        issue_col (str, optional): Issue collateral. Defaults to 'A'.
        measure (enums.IdsMeasure, optional): Measure type. Defaults to Outstanding.
    
    Returns:
        str: The fetched international debt data as a string.
    """
    url = f'WS_DEBT_SEC2_PUB/~/{freq}.{issuer_res.value}.{issuer_nat.value}.{issuer_sector_imm.value}.{issuer_sector_ult.value}.{market}.{issue_type}.{issue_curr_group.value}.{issue_curr}.{issue_orig_mat.value}.{issue_re_mat.value}.{issue_rate.value}.{issue_risk}.{issue_col}.{measure.value}'
    fetcher = GenericFetcher()
    return fetcher.fetch(url)


@validate_enums
def get_global_liquidity_data(
    freq: str = 'Q',
    currency: str = 'USD',
    borrowing_country: Region = Region.LiquidityAllCountries,
    borrowing_sector: Sector = Sector.LiquidityAllSectors,
    lending_sector: Sector = Sector.LiquidityAllSectors,
    position_type: PositionType = PositionType.All,
    instrument_type: Instrument = Instrument.All,
    unit_of_measure: UnitOfMeasure = UnitOfMeasure.USD
) -> str:
    """
    Fetches Global Liquidity data with various filtering options.
    
    Args:
        freq (str, optional): Data frequency ('Q' for quarterly, etc.). Defaults to 'Q'.
        currency (str, optional): Currency code. Defaults to 'USD'.
        borrowing_country (enums.Region, optional): Borrowing country/region. Defaults to '5J'.
        borrowing_sector (enums.Sector, optional): Borrowing sector. Defaults to 'A'.
        lending_sector (enums.Sector, optional): Lending sector. Defaults to 'A'.
        position_type (enums.PositionType, optional): Position type. Defaults to 'A'.
        instrument_type (enums.Instrument, optional): Instrument type. Defaults to 'A'.
        unit_of_measure (enums.UnitOfMeasure, optional): Unit of measure. Defaults to 'USD'.
    
    Returns:
        str: The fetched global liquidity data as a string.
    """
    url = f'WS_GLI/~/{freq}.{currency}.{borrowing_country.value}.{borrowing_sector.value}.{lending_sector.value}.{position_type.value}.{instrument_type.value}.{unit_of_measure.value}'
    fetcher = TitleFetcher()
    return fetcher.fetch(url)


@validate_enums
def get_debt_securities_data(
        freq: str = 'Q',
        reference_area: Region = Region.AllCountries,
        counterparty_area: Region = Region.AllCountries,
        reporting_sector: Sector = Sector.All,
        counterparty_sector: Sector = Sector.All,
        accounting_entry: AccountingEntry = AccountingEntry.Assets,
        transaction_type: TransactionType = TransactionType.Stocks,
        instrument: DebtInstrumentType = DebtInstrumentType.All,
        maturity: Maturity = Maturity.Total,
        unit_of_measure: UnitOfMeasure = UnitOfMeasure.USD,
        currency_denomination: CurrencyDenomination = CurrencyDenomination.All,
        valuation_method: ValuationMethod = ValuationMethod.MarketValue
) -> str:
    """
    Fetches Debt Securities data with various filtering options.
    
    Args:
        freq (str, optional): Data frequency ('Q' for quarterly, etc.). Defaults to 'Q'.
        reference_area (enums.Region, optional): Reference area/region. Defaults to AllCountries.
        counterparty_area (enums.Region, optional): Counterparty area/region. Defaults to AllCountries.
        reporting_sector (enums.Sector, optional): Reporting sector. Defaults to All.
        counterparty_sector (enums.Sector, optional): Counterparty sector. Defaults to All.
        accounting_entry (enums.AccountingEntry, optional): Accounting entry type. Defaults to Assets.
        transaction_type (enums.TransactionType, optional): Transaction type. Defaults to Stocks.
        instrument (enums.DebtInstrumentType, optional): Debt instrument type. Defaults to All.
        maturity (enums.Maturity, optional): Maturity type. Defaults to Total.
        unit_of_measure (enums.UnitOfMeasure, optional): Unit of measure. Defaults to USD.
        currency_denomination (enums.CurrencyDenomination, optional): Currency denomination. Defaults to All.
        valuation_method (enums.ValuationMethod, optional): Valuation method. Defaults to MarketValue.
    
    Returns:
        str: The fetched debt securities data as a string.
    """
    def _get_value(val):
        return val.value if hasattr(val, "value") else val

    url = f'WS_NA_SEC_DSS/~/{freq}.N.{_get_value(reference_area)}.{_get_value(counterparty_area)}.{_get_value(reporting_sector)}.{_get_value(counterparty_sector)}.N.{_get_value(accounting_entry)}.{_get_value(transaction_type)}.{_get_value(instrument)}.{_get_value(maturity)}._Z.{_get_value(unit_of_measure)}.{_get_value(currency_denomination)}.{_get_value(valuation_method)}.V.N._T'
    fetcher = TitleFetcher()
    return fetcher.fetch(url)


@validate_enums
def get_otc_derivatives_data(
    freq: str = 'H',
    derivative_type: OtcDerivativeType = OtcDerivativeType.NotionalAmounts,
    instrument: OtcDerivativeInstrument = OtcDerivativeInstrument.All,
    risk_category: OtcDerivativeRisk = OtcDerivativeRisk.All,
    reporting_country: str = '5J',
    counterparty_sector: OtcCounterpartySector = OtcCounterpartySector.All,
    counterparty_country: str = '5J',
    underlying_sector: OtcUnderlyingSector = OtcUnderlyingSector.All,
    currency_leg1: str = 'TO1',
    currency_leg2: str = 'TO1',
    maturity: OtcMaturity = OtcMaturity.All,
    rating: OtcRating = OtcRating.All,
    exercise_method: str = '3',
    basis: OtcBasis = OtcBasis.NetNet
) -> str:
    """
    Fetches OTC Derivatives statistics data with various filtering options.

    Args:
        freq (str, optional): Data frequency ('H' for half-yearly). Defaults to 'H'.
        derivative_type (OtcDerivativeType, optional): Type of measure (notional amounts,
            market values, credit exposure, etc.). Defaults to NotionalAmounts.
        instrument (OtcDerivativeInstrument, optional): Derivative instrument type
            (forwards, swaps, options, CDS, etc.). Defaults to All.
        risk_category (OtcDerivativeRisk, optional): Market risk category
            (FX, interest rate, equity, commodities, credit). Defaults to All.
        reporting_country (str, optional): Reporting country code. Defaults to '5J' (all).
        counterparty_sector (OtcCounterpartySector, optional): Counterparty sector
            (dealers, financial institutions, non-financial, CCPs). Defaults to All.
        counterparty_country (str, optional): Counterparty country code. Defaults to '5J' (all).
        underlying_sector (OtcUnderlyingSector, optional): Sector of underlying asset
            (mainly for CDS - sovereigns, financials, etc.). Defaults to All.
        currency_leg1 (str, optional): Currency of first leg. Defaults to 'TO1' (all).
        currency_leg2 (str, optional): Currency of second leg. Defaults to 'TO1' (all).
        maturity (OtcMaturity, optional): Maturity breakdown. Defaults to All.
        rating (OtcRating, optional): Rating classification. Defaults to All.
        exercise_method (str, optional): Execution method ('3' for all methods). Defaults to '3'.
        basis (OtcBasis, optional): Adjustment for double-counting
            (gross-gross, net-gross, net-net). Defaults to NetNet.

    Returns:
        str: The fetched OTC derivatives data as a string.

    Note:
        Data is released semi-annually (May and November). The statistics cover
        notional amounts, market values, and credit exposure for FX, interest rate,
        equity, commodity, and credit derivatives.
    """
    url = (
        f'WS_OTC_DERIV2/~/{freq}.{derivative_type.value}.{instrument.value}.'
        f'{risk_category.value}.{reporting_country}.{counterparty_sector.value}.'
        f'{counterparty_country}.{underlying_sector.value}.{currency_leg1}.'
        f'{currency_leg2}.{maturity.value}.{rating.value}.{exercise_method}.{basis.value}'
    )
    fetcher = GenericFetcher()
    return fetcher.fetch(url)