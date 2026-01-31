from enum import Enum

class CurrencyGroup(Enum):
    Foreign = 'F'
    All = 'A'

class Region(Enum):
    AllCountries = '3P'
    DevelopingAsiaAndPacific = '4Y'
    EmergingAndDevelopingEconomies = '4T'
    EuropeanDevelopedCountries = '5K'
    DevelopedCountries = '5R'
    DevelopingAfricaAndMiddleEast = '4R'
    DevelopingLatinAmericaAndCaribbean = '4U'
    DevelopingEurope = '3C'
    EuroArea = '5C'
    LiquidityAllCountries = '5J'
    LiquidityDevelopingEurope = '2A'
    US = 'US'
    Local = '1E'
    CrossBorder = '5Z'
    World = 'XW'

class Maturity(Enum):
    Total = 'T'
    LongTerm = 'K'
    ShortTerm = 'C'
    LongTermOriginal = 'L'
    ShortTermOriginal = 'S'

class RateType(Enum):
    All = 'A'
    Fixed = 'C'

class IdsMeasure(Enum):
    Outstanding = 'I'
    Gross = 'C'
    Net = 'G'

class LbsMeasure(Enum):
    Stocks = 'S'
    Growth = 'G'
    BreakInStocks = 'B'
    FXAndBreakAdjusted = 'F'

class Position(Enum):
    Claims = 'C'
    Liabilities = 'L'

class Instrument(Enum):
    All = 'A'
    Credit = 'B'
    Debt = 'D'
    ShortTermDebt = 'M'
    Derivatives = 'I'
    LoansAndDeposits = 'G'
    Unallocated = 'U'

class Institution(Enum):
    All = 'A'
    DomesticBanks = 'D'
    ForeignBranches = 'B'
    ForeignSubsidiaries = 'S'

class PositionType(Enum):
    All = 'A'
    CrossBorder = 'N'
    CrossBorderAndLocal = 'I'
    Local = 'R'
    Unallocated = 'U'

class Sector(Enum):
    All = '1'
    Banks = 'B'
    Government = 'G'
    FinancialSector = 'S12'
    GeneralGovernment = 'S13'
    NonBanks = 'N'
    NonFinancialPrivateSector = 'S'
    NonFinancialSector = 'P'
    NonBankFinancialInstitution = 'F'
    LiquidityAllSectors = 'A'
    TotalEconomy = 'S1'

class CurrencyType(Enum):
    All = 'A'
    Domestic = 'D'
    Foreign = 'F'

class UnitOfMeasure(Enum):
    EUR = 'EUR'
    PercentageOfGDP = '770'
    USD = 'USD'
    PercentageOfGDPYoY = '771'
    JPY = 'JPY'

class AccountingEntry(Enum):
    Assets = 'A'
    Liabilities = 'L'

class TransactionType(Enum):
    Stocks = 'LE'
    Flows = 'F'

class DebtInstrumentType(Enum):
    All = 'F3'
    FixedRate = 'F3FR'
    FloatingRate = 'F3B'
    VariableRate = 'F3VR'
    InflationLinkedVariableRate = 'F3VRA'
    InterestRateLinkedVariableRate = 'F3VRB'

class CurrencyDenomination(Enum):
    All = '_T'
    AllExceptDomestic = 'X1'
    Domestic = 'XDC'

class ValuationMethod(Enum):
    FaceValue = 'F'
    MarketValue = 'M'
    NominalValue = 'N'

class OtcDerivativeType(Enum):
    """Type of derivative measure/statistic."""
    NotionalAmounts = 'A'
    GrossPositiveMarketValue = 'B'
    GrossNegativeMarketValue = 'C'
    GrossMarketValue = 'D'
    GrossPositiveCreditExposure = 'E'
    GrossNegativeCreditExposure = 'F'
    GrossCreditExposure = 'H'
    TurnoverNotional = 'K'
    NumberOfContracts = 'L'
    TurnoverContracts = 'M'
    HerfindahlIndex = 'Q'
    NumberOfDealers = 'R'
    NotionalBought = 'S'
    NotionalSold = 'T'


class OtcDerivativeInstrument(Enum):
    """Type of derivative instrument."""
    All = 'A'
    Spot = 'B'
    ForwardsAndSwaps = 'C'
    OutrightForwardsAndFXSwaps = 'D'
    OutrightForwards = 'E'
    FXSwaps = 'H'
    CurrencySwaps = 'I'
    FRAAndIRSwaps = 'L'
    ForwardRateAgreements = 'M'
    InterestRateSwaps = 'N'
    Futures = 'Q'
    Options = 'R'
    OptionsSold = 'S'
    OptionsBought = 'T'
    CreditDefaultSwaps = 'U'
    SingleNameCDS = 'V'
    MultiNameCDS = 'W'
    IndexProducts = 'X'
    OtherInstruments = 'Z'


class OtcDerivativeRisk(Enum):
    """Market risk category of the derivative."""
    All = 'A'
    ForeignExchange = 'B'
    ForeignExchangeIncludingGold = 'C'
    InterestRate = 'D'
    Equity = 'E'
    SingleEquity = 'F'
    EquityIndex = 'G'
    Commodities = 'J'
    PreciousMetals = 'K'
    Gold = 'L'
    OtherPreciousMetals = 'M'
    NonPreciousMetals = 'N'
    AgriculturalCommodities = 'O'
    EnergyProducts = 'P'
    OtherCommodities = 'Q'
    CreditDerivatives = 'T'
    OtherDerivatives = 'U'
    Unallocated = 'Z'


class OtcCounterpartySector(Enum):
    """Counterparty sector classification."""
    All = 'A'
    ReportingDealers = 'B'
    OtherFinancialInstitutions = 'C'
    NonReportingBanks = 'D'
    InstitutionalInvestors = 'E'
    HedgeFundsAndPTFs = 'F'
    OfficialSectorFinancial = 'G'
    Undistributed = 'H'
    CentralCounterparties = 'K'
    BanksAndSecuritiesFirms = 'L'
    InsuranceAndFinancialGuaranty = 'M'
    SPVs = 'N'
    HedgeFunds = 'O'
    OtherResidualFinancial = 'P'
    NonFinancialCustomers = 'U'
    PrimeBrokered = 'V'
    RetailDriven = 'W'
    RelatedPartyTrades = 'X'
    OwnBranchesAndSubsidiaries = 'Y'
    NonReporters = 'Z'


class OtcUnderlyingSector(Enum):
    """Sector of the underlying asset (mainly for CDS)."""
    All = 'A'
    Sovereigns = 'B'
    NonSovereigns = 'C'
    FinancialFirms = 'F'
    NonFinancialFirms = 'G'
    PortfolioOrStructured = 'J'
    SecuritisedProducts = 'K'
    ABSAndMBS = 'L'
    Other = 'M'
    MultipleSectors = 'N'


class OtcMaturity(Enum):
    """Maturity breakdown for derivatives."""
    All = 'A'
    ShortTerm = 'C'
    OneToFiveYears = 'D'
    OverFiveYears = 'F'
    SevenDaysOrLess = 'G'
    SevenDaysToOneMonth = 'H'
    OneToThreeMonths = 'J'
    LongTerm = 'K'
    ThreeMonthsToOneYear = 'L'
    OneToTwoYears = 'M'
    OverTwoYears = 'N'
    UpToOneYear = 'U'
    OverOneYear = 'W'
    Unallocated = 'X'


class OtcRating(Enum):
    """Rating classification."""
    All = 'A'
    InvestmentGrade = 'B'
    UpperInvestmentGrade = 'D'
    LowerInvestmentGrade = 'F'
    BelowInvestmentGrade = 'H'
    NonRated = 'Z'


class OtcBasis(Enum):
    """Basis for counting (adjustment for double-counting)."""
    GrossGross = 'A'
    NetGross = 'B'
    NetNet = 'C'

