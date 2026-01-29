"""
Usage example for the new FincoreGeminiSDKResponseTranslator.

This demonstrates how to use the modern translator that produces three separate models
aligned with the new prediction architecture.
"""

from datetime import datetime, timezone
from .gemini_sdk_response_to_time_series_prediction_fincore import GeminiSDKResponseToTimeSeriesPredictionFincore
from ipulse_shared_base_ftredge.enums import (
    ModelOutputPurpose, TimeFrame, FincoreCategoryDetailed, 
    FincoreContractOrOwnershipType
)

def example_usage():
    """Example of how to use the new translator."""
    
    # Mock Gemini response (replace with actual response from SDK)
    gemini_response = None  # Your actual GenerateContentResponse object
    
    # Call the translator with required parameters
    prediction_log, prediction_values, investment_rating = GeminiSDKResponseToTimeSeriesPredictionFincore.convert_gemini_response_to_prediction_models(
        gemini_response=gemini_response,
        
        # AI Model Context
        model_specification_id="gemini-1.5-pro-market-v1",
        model_name="Gemini Pro",
        model_version_id="gemini-1.5-pro-002",
        
        # Target Asset
        target_subject_id="AAPL",
        target_subject_name="Apple Inc.",
        target_subject_symbol="AAPL",
        asset_category_detailed=FincoreCategoryDetailed.COMMON_STOCK,
        asset_contract_type=FincoreContractOrOwnershipType.SPOT,
        subject_category="EQUITY",  # Use string or correct enum value
        
        # Prediction Parameters
        prediction_step_timeframe=TimeFrame.ONE_DAY,
        
        # Timing
        prediction_requested_datetime_utc=datetime.utcnow(),
        prediction_received_datetime_utc=datetime.utcnow(),
        
        # Optional parameters
        model_version_name="Summer 2024 Production",
        predicted_records_type="eod_adjc",
        prediction_purpose=ModelOutputPurpose.SERVING,
        created_by="market_prediction_service",
        tags="apple,tech,daily",
    )
    
    # Now you have three separate models:
    
    # 1. TimeSeriesPredictionLog - execution metadata and context
    print(f"Prediction Log ID: {prediction_log.prediction_log_id}")
    print(f"Model used: {prediction_log.model_name}")
    print(f"Cost: ${prediction_log.prediction_cost_usd}")
    print(f"Token usage: {prediction_log.input_tokens_count} input, {prediction_log.output_tokens_count} output")
    
    # 2. List[TimeSeriesPredictionValuesFincore] - quantitative prediction values
    # Note: No separate prediction_values_id needed - identified by prediction_log_id + timestamp
    print(f"Generated {len(prediction_values)} prediction values:")
    for value in prediction_values:
        print(f"  Date: {value.prediction_timestamp_utc}, Value: {value.prediction_value}")
        if value.key_milestones_and_events:
            print(f"    Key events: {value.key_milestones_and_events}")
    
    # 3. FincorePredictionInvestmentRating - qualitative investment analysis
    print(f"Investment Analysis ID: {investment_rating.investment_rating_id}")
    print(f"Overall Rating: {investment_rating.overall_rating}")
    print(f"Investment Thesis: {investment_rating.investment_thesis}")
    if investment_rating.key_risks:
        print(f"Key Risks Type: {type(investment_rating.key_risks).__name__}")
        print("  - Can be: StockKeyRisks, CryptoKeyRisks, CommodityKeyRisks, ETFKeyRisks, or BaseFincoreKeyRisks")
    
    # Store each model separately in your database
    # save_prediction_log(prediction_log)
    # save_prediction_values(prediction_values) 
    # save_investment_rating(investment_rating)
    
    return prediction_log, prediction_values, investment_rating

# Migration guide from old translators:
# 
# OLD WAY (deprecated):
#     result = TimeSeriesMarketLLMPredictionGeminiSDKResponseTranslator.convert_gemini_response_to_market_prediction(...)
#     # Returns single monolithic TimeSeriesLLMPredictionMarketAsset object
# 
# NEW WAY:
#     log, values, rating = FincoreGeminiSDKResponseTranslator.convert_gemini_response_to_prediction_models(...)
#     # Returns three separate specialized models:
#     # - log: TimeSeriesPredictionLog (execution metadata)
#     # - values: List[TimeSeriesPredictionValuesFincore] (quantitative predictions)  
#     # - rating: FincorePredictionInvestmentRating (qualitative analysis)
# 
# BENEFITS:
# - Clear separation of concerns
# - Better data normalization
# - Easier to query and analyze each aspect independently
# - Aligns with new prediction architecture
# - Supports proper relational modeling
