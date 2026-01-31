"""
Analyst-related enums for AI prediction architecture.

This module defines all analyst identity, presentation, and execution enums
for the Analyst DNA v2 architecture.

AUTHOR: Russlan Ramdowar; russlan@ftredge.com
CREATED: 2025-12-28
"""

from enum import auto
from .enums_pulse import AutoLower
from .enums_units import TimeUnit, TimeFrame


# =============================================================================
# CORE COGNITIVE DIMENSIONS (Identity)
# =============================================================================

class CognitiveStyle(AutoLower):
    """Primary and secondary cognitive styles - the mental model and investment philosophy.
    
    These represent fundamental analytical lenses and thinking frameworks.
    Display names and ordering will be controlled via database display_name fields.
    
    Organized by domain for conceptual clarity:
    - Economist/Finance styles
    - Power-seeking styles  
    - Detective/Journalistic styles
    - Scientific/Analytical styles
    - Mystics
    """
    # Economist/Finance Styles
    VALUE_PURIST = auto()  # The Buffett - fundamentals, cash flow, intrinsic value
    ECONOMIST = auto()  # The Keynes - macro trends, cycles, behavioral finance
    MACRO_STRATEGIST = auto()  # The Ray Dalio - top-down, rates, geopolitics, cycles
    MACRO_INVESTOR = auto()  # The Bridgewater - integrated macro and fundamental analysis
    GROWTH_HUNTER = auto()  # The Cathie Wood, Peter Thiel - disruption, innovation, TAM
    TECHNICAL_QUANT = auto()  # The RoboTrader - data-driven, momentum, volatility
    CONTRARIAN = auto()  # The Michael Burry - skeptical of consensus
    
    # Power-Seeking Styles
    MACHIAVELLIAN = auto()  # The Realpolitik - power dynamics, monopoly, lobbying
    EARTH_INVADER = auto()  # The Outsider - alien perspective, non-human logic patterns
    
    # Detective/Journalistic Styles
    FORENSIC_DETECTIVE = auto()  # The Sherlock - accounting irregularities, hidden footnotes

     # Scientific/Analytical Styles
    SUPERINTELLIGENCE = auto()  # The Singularity - vast synthesis, non-obvious correlations
    PHYSICIST = auto()  # The Feynman - first principles, fundamental laws, deep modeling
    BIOLOGIST = auto()  # The Darwin - evolutionary patterns, adaptation, ecosystems
    CHEMIST = auto()  # The Curie - reaction dynamics, catalysts
    ENGINEER = auto()  # The Tesla, Elon Musk - systems thinking, optimization, efficiency

    # Mystics
    ASTROLOGIST = auto()  # The Mystic - cosmic patterns, planetary cycles, fate


# =============================================================================
# DATA SOURCING APPROACH
# =============================================================================

class DataSourcingApproach(AutoLower):
    """Defines how input data should be sourced and processed for the AI model."""
    QUERY_BASE_FIELDS_PLACEHOLDERS = auto()  # Basic fields (env_prefix, subject_id) replaced, source query works
    QUERY_NO_PLACEHOLDERS = auto()           # Run query as-is, no placeholders
    QUERY_CUSTOM = auto()                    # Custom pipeline definition required

class PersonaVariant(AutoLower):
    """Intensity/moderation level of persona expression.
    
    Defines how strongly the cognitive style is applied.
    """
    SIMPLE_DEFINITION = auto()  # Light, minimal expression of cognitive style
    STANDARD_DEFINITION = auto()  # Balanced, orthodox application of cognitive style
    EXTENDED_DEFINITION = auto()  # Enhanced, detailed expression of cognitive style
    EXTREME_PERSONALITY_DEFINITION = auto()  # Maximum intensity, often contrarian or unconventional


class Mood(AutoLower):
    """Emotional/psychological flavor - can have multiple moods.
    
    Personas can combine moods (e.g., [AGGRESSIVE, GREEDY] or [FEARFUL, SAD]).
    """
    BALANCED = auto()  # Even-keeled, objective, measured temperament
    COLD = auto()  # Detached, clinical, highly rational
    AGGRESSIVE = auto()  # Bold, high-conviction, assertive expression
    FEARFUL = auto()  # Risk-averse, emphasizes caution and downside protection
    GREEDY = auto()  # Maximum upside seeking, opportunity capture focus
    SAD = auto()  # Pessimistic outlook, melancholic framing, defensive positioning


# =============================================================================
# PRESENTATION DIMENSIONS (How They Communicate)
# =============================================================================

class CommunicationTone(AutoLower):
    """HOW the analyst communicates - the emotional/rhetorical stance.
    
    Defines delivery style and attitude in analysis presentation.
    """
    BALANCED = auto()  # Objective, measured, even-handed
    EXPRESSIVE = auto()  # Emotional, passionate, emphatic language
    SOCRATIC = auto()  # Question-driven, dialogic, challenges assumptions
    PROPHETIC = auto()  # Grand vision, sweeping historical analogies
    GONZO = auto()  # First-person, immersive, visceral, unfiltered
    INVESTIGATIVE = auto()  # Detective-like, evidence-building, methodical
    ROAST = auto()  # Abrasive, brutally honest, mocking, sarcastic
    TELEGRAPHIC = auto()  # Terse, no-nonsense, BLUF attitude


class LexicalRegister(AutoLower):
    """Target audience sophistication level - vocabulary complexity.
    
    Controls how technical and specialized the language should be.
    """
    NOVICE_FRIENDLY = auto()  # Explains jargon, analogies, educational tone
    INTERMEDIATE = auto()  # Moderate terminology, balanced accessibility
    SME = auto()  # Dense terminology, assumes domain expertise
    SLANG = auto()  # Internet culture, meme references, Gen Z speak


# =============================================================================
# TASK SCOPE DIMENSIONS (What Timeframe)
# =============================================================================

class ThinkingHorizon(AutoLower):
    """Investment timeframe perspective - temporal scope of analysis.
    
    Defines the time horizon for investment analysis and predictions.
    
    Micro-Structure Horizons (High Frequency & Intraday):
    - HIGHFREQ_TRADE: Seconds/Minutes - Market microstructure, order flow, tick data
    - SCALP_TRADE: Minutes/Hours - Quick momentum bursts, breakout trading
    - INTRADAY_TRADE: Hours/Day - Session-based trading, closing before market close
    
    Swing & Trend Horizons (Days to Months):
    - SWING_TRADE: Days/Weeks - Capturing multi-day moves, technical patterns
    - POSITION_TRADE: Weeks/Months - Riding major trends, intermediate term
    
    Investment Horizons (Months to Decades):
    - TACTICAL_INVESTMENT: Months/Years - Medium-term allocation, business cycle investing
    - STRATEGIC_INVESTMENT: Years - Long-term capital appreciation, strategy execution
    - DYNASTY_BUILDING: Decades/Generations - Forever holding, compounding machines
    """
    HIGHFREQ_TRADE = auto()  # Seconds/Minutes: Market microstructure, order flow, tick data
    SCALP_TRADE = auto()  # Minutes/Hours: Quick momentum bursts, breakout trading
    INTRADAY_TRADE = auto()  # Hours/Day: Session-based trading, closing before market close
    SWING_TRADE = auto()  # Days/Weeks: Capturing multi-day moves, technical patterns
    POSITION_TRADE = auto()  # Weeks/Months: Riding major trends, intermediate term
    TACTICAL_INVESTMENT = auto()  # Months/Years: Medium-term allocation, business cycle investing (6m-3y)
    STRATEGIC_INVESTMENT = auto()  # Years: Long-term capital appreciation, strategy execution (3y-7y)
    DYNASTY_BUILDING = auto()  # Decades/Generations: Forever holding, compounding machines (7y-50y+)


class PredictionTaskType(AutoLower):
    """DEPRECATED: Use AIAssemblyComponentType.TASK_* variants instead.
    
    Type of prediction task being performed.
    
    Defines the analytical goal of the prediction pipeline.
    
    MIGRATION NOTE: These values have been moved to AIAssemblyComponentType with TASK_ prefix.
    This enum is kept temporarily for backward compatibility during migration.
    Use AIAssemblyComponentType.TASK_* in new code.
    """
    FORECAST_CLOSE_PRICE = auto()
    FORECAST_TS_CLOSE_PRICE_PCT_CHANGE = auto()
    GENERATE_INVESTMENT_THESIS = auto()  # Qualitative buy/sell/hold reasoning
    GENERATE_INVESTMENT_THESIS_AND_TIMESERIES_EOD_CLOSE_PRICE = auto()  # Combined qualitative and quantitative
    GENERATE_INVESTMENT_THESIS_AND_TIMESERIES_EOD_CLOSE_PRICE_PCT_CHANGE = auto()  # Combined qualitative and quantitative
    GENERATE_RISK_ASSESSMENT = auto()  # Risk analysis and scoring



class PredictionTarget(AutoLower):
    """Type of prediction task being performed.
    
    Defines the analytical goal of the prediction pipeline.
    """
    EOD_CLOSE_PRICE = auto()
    EOD_CLOSE_PRICE_PCT_CHANGE = auto()


# =============================================================================
# EXECUTION CONFIGURATION DIMENSIONS (How They Work)
# =============================================================================

class AnalystModeCategory(AutoLower):
    """Execution capability mode category.
    
    Represents the high-level category of execution capability.
    Combinations of category + variant determine the specific mode.
    """
    # Pure Thinking Modes - no external data
    THINKER = auto()  # Standard thinker

    RESEARCHER = auto()  # Web-enabled
    SCHOLAR = auto()  # RAG-enabled
    
    # Specialized Analytical Modes - Non-LLM
    STATISTICIAN = auto()  # Classical statistical modeling (ARIMA, regression)
    QUANT = auto()  # Deep learning models (neural networks, LSTM)


class AssignmentReason(AutoLower):
    """Reason for assigning an analyst to a subject.
    
    Context for why this specific analyst is covering this subject.
    """
    MANUAL_CURATION = auto()  # Explicitly assigned by human
    EXPERIMENTAL = auto()  # Testing new configurations
    AUTO_RECOMMEND = auto()  # System recommended based on fit
    PILOT_TEST = auto()  # Testing new analyst performance
    PERFORMANCE_UPGRADE = auto()  # Upgrading from lower performing analyst


class ThinkingLevel(AutoLower):
    """Reasoning depth control - technical configuration.
    
    Controls the depth and thoroughness of the AI model's reasoning process.
    """
    FAST = auto()  # Quick, efficient reasoning
    NORMAL = auto()  # Standard reasoning
    HIGH = auto()  # High, thorough reasoning (default)
    DEEP = auto()  # Deep reasoning depth (when available)


class CreativityLevel(AutoLower):
    """Model temperature/creativity control - technical configuration.
    
    Controls output variability and creative exploration.
    """
    CONVENTIONAL = auto()  # Low temperature, highly consistent
    STANDARD = auto()  # Moderate creativity (default)
    CREATIVE = auto()  # High temperature, exploratory

class WebSearchMode(AutoLower):
    """Web search intensity - technical configuration.
    
    Defines web search depth when web_search is enabled.
    """
    STANDARD = auto()  # Single query, top results (default)
    DEEP = auto()  # Multi-step iterative research (premium cost)


class RagRetrievalMode(AutoLower):
    """RAG retrieval strategy - technical configuration.
    
    Defines retrieval precision when rag_search is enabled.
    """
    STANDARD = auto()  # Balanced retrieval (default)
    PRECISE = auto()  # High-precision retrieval, fewer but more relevant results


class DataStructureMode(AutoLower):
    """Data presentation format for AI consumption/production.
    
    Defines the structural paradigm of the data.
    """
    TABULAR = auto()  # Rigid arrays, positional encoding (for XGBoost/ARIMA)
    NARRATIVE_TEXT = auto()  # Human-readable text with templates (for LLMs)
    JSON = auto()  # Structured object data (for Hybrid/LLMs)


class AssemblyStyle(AutoLower):
    """Prompt assembly style for different model capabilities.
    
    Defines how the prompt components are stitched together.
    """
    BALANCED = auto()  # Equal weight to system and user content
    INSTRUCTION_DRIVEN = auto()  # Enforced JSON schema output
    CONTENT_DRIVEN = auto()  # Flexible narrative output


class AssemblyComponentComplexity(AutoLower):
    """Prompt assembly complexity levels.
    
    Defines the granularity and detail level of the assembled prompt components.
    """
    MINIMAL = auto()  # Basic context, minimal detail
    STANDARD = auto()  # Standard detail level
    EXTENSIVE = auto()  # Maximum detail and context


# =============================================================================
# PROMPT ASSEMBLY COMPONENT TYPES (DNA v2)
# =============================================================================

class AIAssemblyComponentType(AutoLower):
    """Component types for AI prompt assembly architecture.
    
    Used in PromptAssemblyComponent to define the type of each building block.
    Each type maps to a specific source table for runtime resolution:
    - analyst_persona -> ai_analyst_personas
    - input_data -> ai_input_formats  
    - output_instructions -> ai_output_formats (includes task-specific instructions)
    - others -> ai_assembly_components
    
    ARCHITECTURE DECISION: Task instructions are merged into OUTPUT_INSTRUCTIONS.
    This is because task goals ("generate investment thesis") are tightly coupled
    with output structure. The output format definition implicitly defines the task.
    """
    # Core component types for prompt assembly
    ANALYST_PERSONA_DEFINITION = auto()
    TASK_GUIDELINES = auto()  # Task-specific analytical guidelines (formerly GENERAL_GUIDELINES)
    SUBJECT_CONTEXT = auto()
    INPUT_DATA = auto()
    OUTPUT_INSTRUCTIONS = auto()  # Includes task instructions + output formatting
    COMMUNICATION_STYLE = auto()
    LEXICAL_REGISTER = auto()

    # Specific task instruction types (replaces old PredictionTaskType enum)
    # These define what analytical goal the task performs
    # TASK_FORECAST_CLOSE_PRICE = auto()
    # TASK_FORECAST_TS_CLOSE_PRICE_PCT_CHANGE = auto()
    # TASK_GENERATE_INVESTMENT_THESIS = auto()
    # TASK_GENERATE_INVESTMENT_THESIS_AND_TIMESERIES_CLOSE_PRICE_CHANGE = auto()
    # TASK_GENERATE_INVESTMENT_THESIS_AND_TIMESERIES_CLOSE_PRICE_PCT_CHANGE = auto()
    # TASK_GENERATE_RISK_ASSESSMENT = auto()



# =============================================================================
# COMPONENT TYPES (Scoping and Assembly)
# =============================================================================

class ScopingComponentType(AutoLower):
    """Types of reusable scoping context components.
    
    Defines the categories of instruction/context components used in prompt assembly.
    Uses lowercase as per architecture specification.
    Numbered codes: 10s series.
    """
    GENERAL_GUIDELINES = auto()  # 10: Universal instructions
    COMMUNICATION_TONE_INSTRUCTIONS = auto()  # 20: Tone/attitude directives
    LEXICAL_REGISTER_INSTRUCTIONS = auto()  # 30: Audience-specific language
    OUTPUT_INSTRUCTIONS = auto()  # 60: Output format and schema
    ANALYST_MODE_INSTRUCTIONS = auto()  # 70: Execution mode guidelines
    SUBJECT_CONTEXT = auto()  # 40: Subject-specific context
    TASK_INSTRUCTIONS = auto()  # 50: Task-specific instructions


class PersonaInjectionMethod(AutoLower):
    """Method for injecting persona instructions into model API calls.
    
    Only applicable to configurable models (LLMs). Null for traditional ML models.
    """
    SYSTEM_INSTRUCTION = auto()  # Via system instruction field
    USER_CONTENT = auto()  # Via user content/prompt
    HYBRID = auto()  # Split across both fields


# =============================================================================
# ENUM HELPER FUNCTIONS
# =============================================================================

def get_horizon_constraints(thinking_horizon: ThinkingHorizon) -> dict:
    """Dynamically derive min/max horizon values from thinking_horizon enum.
    
    This function provides time constraint lookups for thinking horizons.
    Used throughout the analyst DNA architecture for:
    - Validating horizon values in xref table configurations
    - Filtering compatible analyst personas by thinking horizon
    - Enforcing time range constraints in prediction pipelines
    - Dynamic constraint resolution vs. hardcoded values in schemas
    
    Args:
        thinking_horizon: The thinking horizon enum value
        
    Returns:
        dict: Dictionary with min_val, min_timeunit, max_val, max_timeunit.
              Format:
              {
                  'min_val': int,
                  'min_timeunit': TimeUnit,
                  'max_val': int,
                  'max_timeunit': TimeUnit
              }
    
    Note:
        Each type's max val is always inclusive. min val is non inclusive.
        
        Current implementation supports all 8 horizons from micro-structure trading to multi-generational investing.
    """
    
    horizon_map = {
        ThinkingHorizon.HIGHFREQ_TRADE: {
            "min_val": 0, "min_timeunit": TimeUnit.SECOND,
            "max_val": 10, "max_timeunit": TimeUnit.SECOND
        },  # nanoseconds to 10 seconds (market microstructure)
        ThinkingHorizon.SCALP_TRADE: {
            "min_val": 10, "min_timeunit": TimeUnit.SECOND,
            "max_val": 5, "max_timeunit": TimeUnit.MINUTE
        },  # Minutes to 4 hours (intraday momentum)
        ThinkingHorizon.INTRADAY_TRADE: {
            "min_val": 5, "min_timeunit": TimeUnit.MINUTE,
            "max_val": 24, "max_timeunit": TimeUnit.HOUR
        },  # Hours to 1 day (session-based)
        ThinkingHorizon.SWING_TRADE: {
            "min_val": 1, "min_timeunit": TimeUnit.DAY,
            "max_val": 15, "max_timeunit": TimeUnit.DAY
        },  # Days to 3 weeks (multi-day moves)
        ThinkingHorizon.POSITION_TRADE: {
            "min_val": 15, "min_timeunit": TimeUnit.DAY,
            "max_val": 6, "max_timeunit": TimeUnit.MONTH
        },  # Weeks to 3 months (trend following)
        ThinkingHorizon.TACTICAL_INVESTMENT: {
            "min_val": 6, "min_timeunit": TimeUnit.MONTH,
            "max_val": 3, "max_timeunit": TimeUnit.YEAR
        },  # 6 months to 3 years (business cycle)
        ThinkingHorizon.STRATEGIC_INVESTMENT: {
            "min_val": 3, "min_timeunit": TimeUnit.YEAR,
            "max_val": 7, "max_timeunit": TimeUnit.YEAR
        },  # 3 years to 7 years (long-term capital appreciation)
        ThinkingHorizon.DYNASTY_BUILDING: {
            "min_val": 7, "min_timeunit": TimeUnit.YEAR,
            "max_val": 100, "max_timeunit": TimeUnit.YEAR
        },  # 7 years to 50+ years (generational wealth)
    }
    
    return horizon_map.get(thinking_horizon, {
        "min_val": 6, "min_timeunit": TimeUnit.MONTH,
        "max_val": 3, "max_timeunit": TimeUnit.YEAR
    })  # Default to TACTICAL


