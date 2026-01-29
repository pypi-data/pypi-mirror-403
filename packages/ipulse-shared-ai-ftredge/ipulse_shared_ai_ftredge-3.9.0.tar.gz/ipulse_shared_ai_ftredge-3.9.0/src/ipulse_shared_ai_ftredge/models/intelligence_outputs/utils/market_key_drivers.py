"""Specialized driver/opportunity models for different market asset types."""
from typing import Optional, Union
from pydantic import BaseModel, Field


class BaseMarketKeyDrivers(BaseModel):
    """
    Base class for all market-specific driver/opportunity models.
    These are POSITIVE factors that could drive upside performance.
    """
    macroeconomic_drivers: Optional[str] = Field(
        None, 
        description="Favorable macroeconomic conditions, such as economic growth, low interest rates, supportive monetary policy"
    )
    political_and_geopolitical_drivers: Optional[str] = Field(
        None, 
        description="Positive political and geopolitical factors, such as favorable trade agreements, political stability, reduced tensions"
    )
    regulatory_drivers: Optional[str] = Field(
        None, 
        description="Supportive regulatory environment, such as deregulation, favorable policy changes, subsidies, tax incentives"
    )

class StockKeyDrivers(BaseMarketKeyDrivers):
    """Driver/opportunity model specifically for stock/equity investments."""
    
     # Market-Level Drivers
    market_sentiment_and_trends: Optional[str] = Field(
        None,
        description="Current market sentiment and trends, such as bullish or bearish trends, market volatility, and investor behavior patterns"
    )
    competitive_positioning_drivers: Optional[str] = Field(
        None, 
        description="Strengthening competitive position, such as market share gains, pricing power, brand strength, customer loyalty, network effects, moat widening"
    )
    sector_and_industry_tailwinds: Optional[str] = Field(
        None, 
        description="Favorable industry dynamics, such as sector growth, favorable trends, consolidation opportunities, emerging demand, technological shifts benefiting the sector"
    )
    expansion_opportunities: Optional[str] = Field(
        None, 
        description="Growth through market expansion, such as geographic expansion, new customer segments, addressable market growth, emerging markets penetration"
    )
    operational_drivers: Optional[str] = Field(
        None, 
        description="Operational improvements, such as supply chain optimization, production efficiency, quality enhancements, cost reductions, capacity expansion"
    )
    management_drivers: Optional[str] = Field(
        None, 
        description="Strong management and leadership, characterized by visionary executive teams, effective capital allocation, robust corporate governance, and aligned insider ownership"
    )
    innovation_and_product_drivers: Optional[str] = Field(
        None, 
        description="Innovation and new product launches, such as R&D breakthroughs, successful product launches, patent protections, technology advantages"
    )


class CryptoKeyDrivers(BaseMarketKeyDrivers):
    """Driver/opportunity model specifically for cryptocurrency investments."""
    
    adoption_and_network_growth: Optional[str] = Field(
        None, 
        description="Increasing adoption and network effects, characterized by growth in active addresses, transaction volume, developer activity, total value locked (TVL), and real-world utility"
    )
    technological_advancement: Optional[str] = Field(
        None, 
        description="Protocol improvements and technological innovations, such as scalability upgrades (Layer 2s), interoperability solutions, privacy enhancements, and energy efficiency improvements"
    )
    institutional_and_regulatory_support: Optional[str] = Field(
        None, 
        description="Growing institutional support and regulatory clarity, such as ETF approvals, custody solutions, regulatory frameworks, central bank digital currencies (CBDCs)"
    )
    defi_and_ecosystem_expansion: Optional[str] = Field(
        None, 
        description="DeFi ecosystem growth and use case expansion, such as new protocols, yield opportunities, real-world asset (RWA) tokenization, and NFT integration"
    )
    scarcity_and_tokenomics: Optional[str] = Field(
        None, 
        description="Favorable tokenomics and supply dynamics, such as halving events, token burns, staking rewards, deflationary mechanisms, supply shocks"
    )


class CommodityKeyDrivers(BaseMarketKeyDrivers):
    """Driver/opportunity model specifically for commodity investments."""
    
    supply_constraints: Optional[str] = Field(
        None,
        description="Tightening supply conditions, such as production cuts, mine closures, underinvestment, geopolitical supply disruptions, OPEC+ agreements"
    )
    demand_growth: Optional[str] = Field(
        None, 
        description="Increasing demand, such as economic growth in emerging markets, industrial demand, green energy transition (copper, lithium), inventory restocking"
    )
    technology_advancement_opportunities: Optional[str] = Field(
        None, 
        description="Opportunities from technology advancements, such as EV adoption driving lithium/cobalt demand, renewable energy infrastructure requiring copper/silver, hydrogen economy"
    )

class FundKeyDrivers(BaseMarketKeyDrivers):
    """Driver/opportunity model specifically for Fund investments."""

    underlying_assets_and_sector_performance: Optional[str] = Field(
        None,
        description="Strong performance of underlying assets, such as sector outperformance, index gains, favorable asset class trends, thematic opportunities"
    )
    investment_flows_and_liquidity: Optional[str] = Field(
        None, 
        description="Positive investment flows and liquidity, such as increasing AUM, strong investor demand, improved liquidity, tightening bid-ask spreads"
    )
    fund_performance_and_expense_drivers: Optional[str] = Field(
        None, 
        description="Competitive cost structure and performance metrics, such as low expense ratios, tax efficiency, efficient tracking, and alpha generation"
    )
    fund_manager_track_record_drivers: Optional[str] = Field(
        None,
        description="Proven track record of the fund manager or management team, including historical outperformance, experience in the asset class, and stability"
    )
    strategy_execution_drivers: Optional[str] = Field(
        None,
        description="Effective execution of the fund's stated strategy, including disciplined rebalancing, adherence to mandate, and risk management effectiveness"
    )
    market_exposure_opportunities: Optional[str] = Field(
        None,
        description="Unique or efficient access to specific markets, sectors, or asset classes that are otherwise difficult for individual investors to access"
    )


# Union type for all market-specific driver models
MarketKeyDrivers = Union[StockKeyDrivers, CryptoKeyDrivers, CommodityKeyDrivers, FundKeyDrivers, BaseMarketKeyDrivers]
