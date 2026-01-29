
# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=line-too-long
from enum import StrEnum, IntEnum, auto


class AutoLower(StrEnum):
    """
    StrEnum contrary to simple Enum is of type `str`, so it can be used as a string.
    StrEnum whose `auto()  # type: ignore` values are lower-case.
    (Identical to StrEnum's own default, but keeps naming symmetrical.)
    """
    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        return name.lower()            # StrEnum already does this

class AutoUpper(StrEnum):
    """
    StrEnum contrary to simple Enum is of type `str`, so it can be used as a string.
    StrEnum whose `auto()  # type: ignore` values stay as-is (UPPER_CASE).
    """
    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        return name                    # keep original upper-case


class Layer(StrEnum):
    PULSE_APP="papp"
    PULSE_MSG="pmsg"
    DATA_PLATFORM="dp"
    EXTERNAL ="external"

class Module(AutoLower):
    SHARED=auto()  # type: ignore  # type: ignore
    CORE=auto()  # type: ignore  # type: ignore  #User and Organization management, Authentication, Authorization, Access Control, Billing, Subscriptions
    ORACLE=auto()  # type: ignore  # type: ignore #Prediction engine for both assets and state of the world. Combines Historical data, Derived Analytical Data and AI Predictions.

     # ----future sectors, comment for now--------
     #PORTFOLIO=auto()  # type: ignore
     #SCENARIO=auto()  # type: ignore
     #AIRESEARCH=auto()  # type: ignore # Previously Gym
     #TRADING=auto()  # type: ignore # High frequency short term prediction, and perhaps plugged into control-action system like a digital broker
     #SIMULATION=auto()  # type: ignore
     #MEHEALTH = auto()  # type: ignore
    # RISK=auto()  # type: ignore # builtin part of ORACLE, PORTFOLIO, SCNEARIO

class PulseSector(AutoLower): 
    # --- SUBJECTS ARE MOSTLY ASSETS, COMPANIES ----
    FINCORE=auto()  # type: ignore #  financial markets data : stocks, bonds and derivatives, FX, Commodities
    # --- SUBJECTS ARE MOSTLY COUNTRIES, CITIES. IT IS STATE OF THE WORLD, NOT ASSETS ------
    MACROECONOMY=auto()  # type: ignore # # ;eg. US , Automobile etc. includes economic indicators and geopolitical events, includes Society ie demographics, population, employment, income, education, health, crime, social unrest etc.
    ENVIRONMENT=auto()  # type: ignore # ; could be location and phenomena including climate, weather, pollution, etc.
    # --- SHARED ------
    SHARED=auto()  # type: ignore # ; shared data, like user profiles, organization profiles, etc.

    # ----future sectors, comment for now--------
    # REALESTATE=auto()  # type: ignore #  real estate data
    # REALASSET=auto()  # type: ignore #  tangible assets like art, collectibles, etc.
    # SCIENCE=auto()  # type: ignore # ; scientific data, research papers, clinical trials, patents, etc.
    # SPORTS=auto()  # type: ignore #  like team or individual; sports teams, players, events
    # HEALTH=auto()  # type: ignore #  with subject_id ; individual, animal, personal health data, nutrition etc.

class SectorRecordsCategory(AutoLower):
    
    # FACT DATA
    ALL              = auto()  # type: ignore   #  all categories   
    MARKET           = auto()  # type: ignore   #  relates to $$ ie prices, trades, quotes; structured time series data; Can include derived data like Technical Analysis
    FUNDAMENTAL      = auto()  # type: ignore   #  financial statements , revenue, earnings, etc. Can be structured (annual revenues) or unstructured - balance sheet, income statement, etc.; Can include derived data like Analysis
    INDICATOR      = auto()  # type: ignore   #  GDP, Unemp.Rate, etc. relates to a Health of a State, usually Derived from transactions; structured time series data
    EVENT           = auto()  # type: ignore   #  dividends, splits, M&A, flood, tariff announcement , declaration of war etc.
    NEWSFEED         = auto()  # type: ignore   #  news, tweets, analysis, social media posts, podcasts, etc.; unstructured text data
    SENTIMENT        = auto()  # type: ignore   # DERIVED from NEWSFEED;
    TRANSACTION       = auto()  # type: ignore   #  raw trade records or raw weather records (transaction logs)
    KNOWLEDGE        = auto()  # type: ignore   #  encyclopedic body of knowledge, knowledge graphs, ontologies, taxonomies, etc.; semi-structured graph data
    CODE          = auto()  # type: ignore   #  source code, scripts, models, algorithms, etc.
    SCIENTIFIC        = auto()  # type: ignore   #  mathematical equations, formulas, etc.
    ALTERNATIVE      = auto()  # type: ignore   #  satellite, shipping data, etc.
    

    # GOVERNANCE AND SUPPORT DATA
    REFERENCE        = auto()  # type: ignore   # static ids, calendars
    SPECIFICATIONS  = auto()  # type: ignore   # technical specifications, used for describing data, ai_model and its structure. In some ways similar to SCHEMAS but more focused on models, subjects, controls and processes
    SCHEMAS          = auto()  # type: ignore  # Dataset used for schema definitions . In some ways similar to SPECIFICATIONS but more focused on data structure
    CATALOG          = auto()  # type: ignore   #  Catalogs, used for cataloging data and metadata
    BILLING         = auto()  # type: ignore   # Billing records, used for billing and payments
    METADATA         = auto()  # type: ignore   # Metadata, used for describing data and its structure
    XREF            = auto()  # type: ignore   # Cross-reference tables, used for mapping and relationships
    #LOGS
    CHANGELOGS      = auto()  # type: ignore   #  Change logs, used for tracking changes and versions
    LOGS             = auto()  # type: ignore   #  Logs, used for tracking events and changes

    MULTIPLE         = auto()  # type: ignore   #  Used when multiple categories apply, e.g., a dataset that includes both MARKET and FUNDAMENTAL data
    OTHER            = auto()  # type: ignore

class SubjectCategory(AutoLower):

    # ASSETS
    ALL            = auto()  # type: ignore  # all categories
    EQUITY         = auto()  # type: ignore # Stocks, shares of a company
    FIXEDINCOME   = auto()  # type: ignore # Bonds, loans, things that pay a coupon
    COMMODITY      = auto()  # type: ignore # Raw materials like oil and gold
    REALESTATE    = auto()  # type: ignore # Physical property
    CRYPTO         = auto()  # type: ignore # Digital currencies and tokens
    CASH           = auto()  # type: ignore # Money in bank accounts, money market funds
    FX             = auto()  # type: ignore # Foreign currencies
    FUND           = auto()  # type: ignore # Pooled investments like ETFs and Mutual Funds
    DERIVATIVE     = auto()  # type: ignore # Contracts whose value is derived from an underlying asset
    REALASSET     = auto()  # type: ignore # Other tangible assets like art, cars, collectibles
    INDEX          = auto()  # type: ignore # For tracking non-tradable benchmarks (e.g., S&P 500)

    # STATES OF THE WORLD, TO BE PROPERLY DESIGNED LATER IN ACCORDANCE WITH A DETAILED CATEGORY
    # COMPANIES AND ORGANIZATIONS    
    # INDUSTRY       = auto()  # type: ignore # Sector or industry classification like Technology, Healthcare, Finance, etc.
    # ORGANIZATION   = auto()  # type: ignore # Company, Financial_Exchange, Non-profits, governments, NGOs, etc.

    # FOR ENVIRONMENT AND MACROECONOMY
    # COUNTRY        = auto()  # type: ignore # Countries like USA, China
    # REGION         = auto()  # type: ignore # Regions like North America, Europe
    # CITY           = auto()  # type: ignore # Cities like New York, London
    # LANDOFRM      = auto()  # type: ignore # Physical locations like mountains, rivers, etc.


    MULTIPLE       = auto()  # type: ignore
    OTHER          = auto()  # type: ignore


class SystemSubject(AutoLower):
    USER=auto()  # type: ignore
    ASSET=auto()  # type: ignore
    ORGANIZATION=auto()  # type: ignore
    DATASET=auto()  # type: ignore
    DEPARTMENT = auto()  # type: ignore
    WORKSPACE = auto()  # type: ignore
    GROUP=auto()  # type: ignore
    SUBSCRIPTION=auto()  # type: ignore
    CATALOG=auto()  # type: ignore
    PAYMENT=auto()  # type: ignore 
    ACTION=auto()  # type: ignore
    RESOURCE=auto()  # type: ignore
    SERVICE=auto()  # type: ignore
    ROLE=auto()  # type: ignore


class ChargeType(AutoLower):
    FREE=auto()  # type: ignore
    STATIC_UNIFORM=auto()  # type: ignore #STATIC means the price is fixed and doesn’t change regardless of access factors ; UNIFORM means all datasets within a specific boundary have same uniform price; 
    STATIC_CUSTOM=auto()  # type: ignore #STATIC means the price is fixed and doesn’t change regardless of access factors ; CUSTOM means datasets within dataset group have their own custom price calculation formula;
    DYNAMIC_UNIFORM=auto()  # type: ignore #DYNAMIC means the price can change based on access factors ; UNIFORM means all datasets within a specific boundary have same uniform price;
    DYNAMIC_CUSTOM=auto()  # type: ignore #DYNAMIC means the price can change based on access factors ; CUSTOM means datasets within dataset group have their own custom price calculation formula;


class SubscriptionPlanName(AutoLower):
    NO_SUBSCRIPTION=auto()  # type: ignore
    FREE_SUBSCRIPTION=auto()  # type: ignore
    BASE_SUBSCRIPTION=auto()  # type: ignore
    PREMIUM_SUBSCRIPTION=auto()  # type: ignore
    ADVANCED_SUBSCRIPTION=auto()  # type: ignore
    PROFESSIONAL_SUBSCRIPTION=auto()  # type: ignore
    ENTERPRISE_SUBSCRIPTION=auto()  # type: ignore


class SubjectTier(IntEnum):
    """
    Asset tier for pipeline prioritization and user interest level.
    Lower values = higher priority, more important subjects (assets, economic indicators, etc.).
    Uses sparse integers (multiples of 100) for flexibility in adding tiers.
    
    Guidelines:
    - CRITICAL (100): Highest priority - major indices, key economic indicators (GDP, CPI), mega-cap equities, major commodities (Gold, Oil)
    - MAJOR (200): High priority - large cap equities, major currencies, widely-followed indicators
    - STANDARD (300): Standard priority - mid-cap equities, common commodities, standard indicators [DEFAULT]
    - SECONDARY (400): Secondary priority - small-cap equities, emerging markets, specialized indicators
    - NICHE (500): Niche priority - specialized subjects, regional indicators, alternative data
    - EXPERIMENTAL (600): Experimental - new subjects, test data, low-volume assets
    - ARCHIVED (900): Archived - deprecated subjects, no active processing
    """

    SHOWCASE = 10         # Showcase - Flagship assets or indicators used for demos and marketing
    MAJOR = 30        # Highest priority - major indices, key economic indicators (GDP, CPI), mega-cap equities, major commodities (Gold, Oil)
    IMPORTANT = 100           # Major subjects - large cap, major currencies, widely-followed indicators
    STANDARD = 300        # Standard subjects - upper mid-cap, common commodities, standard indicators [DEFAULT]
    EXTENDED = 1000       # Extended subjects - lower mid -cap, emerging markets, specialized indicators
    WIDE_RANGE = 5000    # Experimental - Smaller caps, low-volume assets
    FAR_REACH = 10000      # FarReach - niche subjects, alternative data
    LONG_TAIL = 30000     # Long Tail - Specialized subjects, Rare Collectibles


class ScopingField(AutoLower):
    """
    Standardized field names for scoping dimensions across AI components.
    
    **Dual Purpose**:
    1. **Applicability Scoping**: Defines filtering dimensions in applicability_constraints
       - Example: `{ScopingField.INDUSTRY: ["software", "semiconductors"]}`
       - Used for constraining which subjects/assets a component can handle
    
    2. **Instance Scoping Granularity**: Defines scoping level for assembly components
       - Example: `instance_scoping_granularity = ScopingField.SUBJECT_CATEGORY`
       - Indicates whether component is scoped per industry, region, subject ID, etc.
    
    **Usage Contexts**:
    - applicability_constraints (JSON dict in AnalystPersona, AIInputFormat, AIOutputFormat, AIAnalystAssemblyComponent)
    - instance_scoping_granularity (enum field in AIAnalystAssemblyComponent)
    - Subject metadata dictionaries for filtering
    - BigQuery WHERE clause generation (applicability_filters_to_sql.py)
    - Forward filtering on prefetched data (applicability_filter_on_prefetched_data.py)
    
    **Examples**:
        >>> # Applicability scoping
        >>> constraints = {ScopingField.INDUSTRY: ["software", "semiconductors"]}
        >>> field_mapping = {ScopingField.MARKET_CAP: "mkt_cap_usd"}
        
        >>> # Instance scoping granularity
        >>> component.instance_scoping_granularity = ScopingField.SUBJECT_ID  # One per subject
        >>> component.instance_scoping_granularity = ScopingField.SUBJECT_CATEGORY  # One per category
    """
    

    # Status filtering
    PULSE_STATUS = auto()  # type: ignore  # Pulse status (ACTIVE, INACTIVE, DRAFT, RETIRED)
    # Core identification fields (LEVEL 0-1, included for completeness)
    PULSE_SECTOR = auto()  # type: ignore  # LEVEL 0: Sector (fincore_sector: FINCORE, MACROECONOMY, ENVIRONMENT, SHARED)
    SECTOR_RECORDS_CATEGORY = auto()  # type: ignore  # LEVEL 0: Data type (market, fundamental, etc.)
    SUBJECT_CATEGORY = auto()  # type: ignore  # LEVEL 1: Asset class (equity, crypto, etc.)
    SUBJECT_CATEGORY_DETAILED = auto()  # type: ignore  # Detailed subcategory (e.g., "large_cap_equity", "etf_index")

    ASSET_TIER = auto()  # type: ignore  # Subject tier (e.g., "tier_1", "tier_2", "tier_3")


    # Fine-grained filtering fields (LEVEL 2)
    INDUSTRY = auto()  # type: ignore  # Industry classification (e.g., "software", "semiconductors", "biotechnology")
    REGION = auto()  # type: ignore  # Geographic region (e.g., "north_america", "europe", "asia_pacific")
    COUNTRY = auto()  # type: ignore  # Country code (e.g., "USA", "CHN", "GBR")
    
    # Numeric comparison fields
    MARKET_CAP = auto()  # type: ignore  # Market capitalization in USD
    PE_RATIO = auto()  # type: ignore  # Price-to-earnings ratio
    REVENUE_GROWTH = auto()  # type: ignore  # Revenue growth percentage
    
    # Manual override fields (LEVEL 3)
    SUBJECT_ID = auto()  # type: ignore  # Unique subject identifier for whitelist/blacklist
 