"""Market-specific event class for equity, crypto, and fund predictions."""
from typing import ClassVar, Dict, Any, Optional
from datetime import datetime
from pydantic import Field, field_validator
from .time_series_prediction_event import TimeSeriesPredictionEventBase
from ..utils.market_key_drivers import (
    StockKeyDrivers,
    CryptoKeyDrivers,
    CommodityKeyDrivers,
    FundKeyDrivers
)
from ..utils.market_key_risks import (
    StockKeyRisks,
    CryptoKeyRisks,
    CommodityKeyRisks,
    FundKeyRisks
)


class FincorePredictionMarketEvent(TimeSeriesPredictionEventBase):
    """
    Market event (driver/risk/milestone) for equity, crypto, fund assets.
    
    Extends base event class with market-specific fields.
    Maps to BigQuery table: prediction_events
    
    Supports:
    - Period-level events (h5y_s6m schema): drivers/risks for specific 6-month periods
    - Horizon-level events (h3y_s3m schema): drivers/risks for entire 3-year horizon
    
    Event Categories validated against:
    - MarketKeyDrivers enums (9 categories for equity/crypto/fund)
    - MarketKeyRisks enums (10 categories for equity/crypto/fund)
    """
    SCHEMA_ID: ClassVar[str] = ""
    SCHEMA_NAME: ClassVar[str] = "dp_oracle_fincore_prediction_market__datasets.prediction_events"
    VERSION: ClassVar[int] = 1
    DOMAIN: ClassVar[str] = "oracle_fincore_prediction_market"
    OBJ_REF: ClassVar[str] = "mrktevent"
    
    # --- Market-Specific Context ---
    subject_category: str = Field(..., description="Asset category: equity, crypto, commodity, fund")
    subject_category_detailed: Optional[str] = Field(None, description="Detailed category: common_stock, etf, bitcoin, mutual_fund, gold, oil")
    
    @field_validator('event_category')
    @classmethod
    def validate_event_category(cls, v: str, info) -> str:
        """Validate event category against market-specific driver/risk enums."""
        if not info.data:
            return v
            
        subject_category = info.data.get('subject_category', '').lower()
        event_type = info.data.get('event_type', '').lower()
        
        # Map subject categories to their enum classes
        driver_enums = {
            'equity': StockKeyDrivers,
            'crypto': CryptoKeyDrivers,
            'commodity': CommodityKeyDrivers,
            'fund': FundKeyDrivers
        }
        
        risk_enums = {
            'equity': StockKeyRisks,
            'crypto': CryptoKeyRisks,
            'commodity': CommodityKeyRisks,
            'fund': FundKeyRisks
        }
        
        # Get the appropriate enum class based on event type
        if 'driver' in event_type or 'opportunity' in event_type:
            enum_class = driver_enums.get(subject_category)
        elif 'risk' in event_type:
            enum_class = risk_enums.get(subject_category)
        else:
            # For milestones and other events, skip validation
            return v
        
        # Validate if we have an enum class
        if enum_class:
            valid_categories = [field for field in dir(enum_class) 
                              if not field.startswith('_') and not callable(getattr(enum_class, field))]
            if v not in valid_categories:
                raise ValueError(
                    f"Invalid event_category '{v}' for {subject_category} {event_type}. "
                    f"Valid categories: {', '.join(valid_categories)}"
                )
        
        return v
    
    def to_bigquery_row(self) -> Dict[str, Any]:
        """Convert to BigQuery row format."""
        return self.model_dump(mode='json', exclude_none=False)
    
    @classmethod
    def from_bigquery_row(cls, row: Dict[str, Any]) -> "FincorePredictionMarketEvent":
        """Create instance from BigQuery row."""
        return cls(**row)
