"""Specialized risk models for different market asset types."""
from typing import Optional, Union
from pydantic import BaseModel, Field


class BaseMarketKeyRisks(BaseModel):
    """Base class for all market-specific risk models."""
    macroeconomic_risks: str = Field(..., description="Macroeconomic risks, such as interest rate changes, inflation/deflation, recession risks, GDP growth slowdown, unemployment trends, or consumer spending patterns")
    global_financial_risks: str = Field(..., description="Global financial risks, such as currency fluctuations, global debt cycles, sovereign debt crises, banking system instability, credit market disruptions, liquidity crises, systemic financial contagion, global risk sentiment shifts, global equity valuations and P/E ratios, or yield curve inversions")
    political_and_geopolitical_risks: str = Field(..., description="Political and geopolitical risks, such as tariffs, trade wars, sanctions, elections, regime changes, regional conflicts, or diplomatic tensions")
    regulatory_risks: str = Field(..., description="Regulatory risks affecting the asset, such as legal changes, compliance requirements, antitrust actions, or policy shifts")
    asset_ownership_type_risks: Optional[str] = Field(None, description="Risks specific to contract or ownership of underlying asset type (e.g., FUTURE, OPTION, SPOT, ADR, GDR, TOKEN, COIN, NFT)")

class StockKeyRisks(BaseMarketKeyRisks):
    """Risk model specifically for stock/equity investments."""
    competitive_risks: str = Field(..., description="Competitive risks in the sector/industry, such as new entrants, innovation disruptions, pricing pressure, or loss of market share")
    operational_and_financial_risks: str = Field(..., description="Operational execution failures (supply chain disruptions, production issues) and financial health concerns (excessive leverage, liquidity constraints, margin compression, credit rating downgrades)")
    management_risks: str = Field(..., description="Risks related to leadership effectiveness, including key person dependency, poor capital allocation, governance failures, strategic missteps, or misalignment of interests")
    sector_specific_risks: str = Field(..., description="Industry/sector-specific risks, such as regulatory changes, commodity price exposure, cyclical downturns, or technological obsolescence")
    climate_and_environmental_risks: str = Field(..., description="Climate and environmental risks, such as natural disasters, resource scarcity")


class CryptoKeyRisks(BaseMarketKeyRisks):
    """Risk model specifically for cryptocurrency investments."""
    adoption_risks: str = Field(..., description="Risks related to slower-than-expected adoption, network stagnation, failure to achieve critical mass, or displacement by competing protocols")
    smart_contract_and_technical_risks: str = Field(..., description="Risks of protocol exploits, smart contract vulnerabilities, bridge hacks, wallet security breaches, or consensus mechanism failures")
    governance_and_centralization_risks: str = Field(..., description="Risks related to centralization of control, 51% attacks, malicious governance proposals, or developer team centralization")
    volatility_risks: str = Field(..., description="Risks of extreme price fluctuations, flash crashes, market manipulation (wash trading, spoofing), and correlation with broader risk assets")
    liquidity_risks: str = Field(..., description="Risks of thin order books, high slippage, exchange insolvencies, delistings, or inability to exit positions during market stress")


class CommodityKeyRisks(BaseMarketKeyRisks):
    """Risk model specifically for commodity investments."""
    supply_demand_imbalance_risks: str = Field(..., description="Supply and demand imbalance risks, including geopolitical tensions and trade policies")
    producer_risks: str = Field(..., description="Major producer and supplier concentration risks, including OPEC dynamics and mining regulations")
    substitute_risks: str = Field(..., description="Substitute products and alternatives risks, including renewable energy sources and synthetic materials")
    inventory_risks: str = Field(..., description="Global inventory levels and stockpile risks, including strategic reserves and seasonal fluctuations")
    climate_and_environmental_risks: str = Field(..., description="Climate and environmental risks, such as natural disasters, resource scarcity")

class FundKeyRisks(BaseMarketKeyRisks):
    """Risk model specifically for ETF (Exchange-Traded Fund) investments."""
    counterparty_risks: str = Field(..., description="Counterparty and issuer risks, including fund sponsor stability, credit risks, and synthetic replication risks")
    manager_risk_and_strategy_drift: str = Field(..., description="Risks related to fund manager performance, strategy drift, tracking error relative to benchmark, or operational failures in trade execution")
    liquidity_and_redemption_risks: str = Field(..., description="Risks related to the ability to redeem shares at fair value, bid-ask spread widening, or underlying asset illiquidity")
    expense_and_fees_risks: str = Field(..., description="Fee structure and expense impact risks, including high expense ratios, hidden costs, and tax inefficiencies eroding returns")
    closure_risks: Optional[str] = Field(None, description="ETF closure or merger risks, including liquidity events and forced redemption issues")


# Union type for all market-specific risk models
MarketKeyRisks = Union[StockKeyRisks, CryptoKeyRisks, CommodityKeyRisks, FundKeyRisks, BaseMarketKeyRisks]
