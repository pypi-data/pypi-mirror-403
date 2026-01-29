"""Modern translator for converting Gemini SDK responses to separated prediction models."""
import uuid
from typing import Dict, Any, Optional, Union, Tuple, List
from datetime import datetime, timezone
from ipulse_shared_base_ftredge.enums import (
    ProgressStatus, ModelOutputPurpose, TimeFrame,
    FincoreCategoryDetailed, FincoreContractOrOwnershipType, SubjectCategory, SectorRecordsCategory
)
from .llm_prompt_json_response_schema_for_time_series_prediction import LLMPromptJSONResponseSchemaForMarketPrediction
from .time_series_prediction_base import TimeSeriesPredictionLog
from .time_series_prediction_fincore_market import (TimeSeriesPredictionValuesFincore,
                                             FincorePredictionAssetRating)
from ..utils.market_key_risks import (BaseMarketKeyRisks,
                                       StockKeyRisks,
                                       CryptoKeyRisks,
                                       CommodityKeyRisks,
                                       FunKeyRisks,
                                       MarketKeyRisks
)


class GeminiSDKResponseToTimeSeriesPredictionFincore:
    """
    Modern translator for converting Gemini SDK responses to separated prediction models.
    Produces three distinct outputs aligned with our new architecture:
    1. TimeSeriesPredictionLog - Execution metadata and context
    2. List[TimeSeriesPredictionValuesFincore] - Quantitative prediction values
    3. FincorePredictionInvestmentRating - Qualitative investment analysis
    """

    # Gemini API pricing (per 1M tokens) - update these as needed
    GEMINI_INPUT_COST_USD_PER_1M_TOKENS = 1.25
    GEMINI_OUTPUT_COST_USD_PER_1M_TOKENS = 10.00
    GEMINI_BATCHED_INPUT_COST_USD_PER_1M_TOKENS = 0.65
    GEMINI_BATCHED_OUTPUT_COST_USD_PER_1M_TOKENS = 6.00

    @classmethod
    def convert_gemini_response_to_prediction_models(
        cls,
        gemini_response,  # GenerateContentResponse object
        # Request Context - AI Model (required)
        model_specification_id: str,
        model_name: str,
        model_version_id: str,
        # Request Context - Target Asset (required)
        target_subject_id: str,
        target_subject_name: str,
        target_subject_symbol: str,
        asset_category_detailed: FincoreCategoryDetailed,
        asset_contract_type: FincoreContractOrOwnershipType,
        subject_category: Union[str, SubjectCategory],
        # Request Context - Prediction Parameters (required)
        prediction_step_timeframe: TimeFrame,
        # Request Context - Timing (required)
        prediction_requested_datetime_utc: datetime,
        prediction_received_datetime_utc: datetime,
        # Request Context - Optional Parameters
        model_version_name: Optional[str] = None,
        model_features_used: Optional[Dict[str, Any]] = None,
        predicted_records_type: Optional[str] = None,
        prediction_purpose: ModelOutputPurpose = ModelOutputPurpose.SERVING,
        input_data_start_datetime: Optional[Union[datetime, str]] = None,
        input_data_end_datetime: Optional[Union[datetime, str]] = None,
        batched: bool = False,
        tags: Optional[str] = None,
        created_by: str = "system",
    ) -> Tuple[TimeSeriesPredictionLog, List[TimeSeriesPredictionValuesFincore], FincorePredictionAssetRating]:
        """
        Convert a Gemini SDK GenerateContentResponse to separated prediction models.
        
        Returns:
            Tuple containing:
            - TimeSeriesPredictionLog: Execution metadata and context
            - List[TimeSeriesPredictionValuesFincore]: Individual prediction value points
            - FincorePredictionInvestmentRating: Investment analysis and rating
        """
        try:
            # Validate response structure
            if not cls._validate_gemini_response(gemini_response):
                raise ValueError("Invalid Gemini SDK response structure")

            # Extract the parsed schema directly from the response
            parsed_schema = gemini_response.parsed
            
            # Extract usage metadata
            usage_metadata = gemini_response.usage_metadata
            
            # Calculate cost
            cost_usd = cls._calculate_cost(usage_metadata, batched=batched)

            # Generate unique IDs for linked models
            prediction_log_id = gemini_response.response_id or f"gemini_{uuid.uuid4()}"
            investment_rating_id = f"rating_{uuid.uuid4()}"

            # Determine prediction period from data
            prediction_start_datetime = None
            prediction_end_datetime = None
            if parsed_schema.price_prediction:
                try:
                    dates = [
                        datetime.fromisoformat(str(point.prediction_date)) 
                        for point in parsed_schema.price_prediction
                    ]
                    prediction_start_datetime = min(dates)
                    prediction_end_datetime = max(dates)
                except (ValueError, AttributeError):
                    pass

            # 1. Create TimeSeriesPredictionLog (execution metadata)
            prediction_log = TimeSeriesPredictionLog(
                # Core Identity
                prediction_log_id=prediction_log_id,
                prediction_purpose=prediction_purpose,
                
                # Target Context
                target_subject_id=target_subject_id,
                target_subject_name=target_subject_name,
                predicted_records_type=predicted_records_type,
                target_subject_description={
                    'sector_records_category': SectorRecordsCategory.MARKET.value,
                    'subject_category': subject_category if isinstance(subject_category, str) else subject_category.value,
                    'contract_type': asset_contract_type.value,
                    'asset_category_detailed': asset_category_detailed.value
                },
                
                # AI Model Context
                model_specification_id=model_specification_id,
                model_name=model_name,
                model_version_id=model_version_id,
                model_version_name=model_version_name,
                model_features_used=model_features_used,
                model_serving_instance_id=None,
                model_serving_instance_name=None,
                
                # Input Structure
                input_structure=[
                    {
                        "input_type": "LLMPrompt",
                        "prompt_variant_id": "market_prediction_v1",
                        "temporal_range_start": str(input_data_start_datetime) if input_data_start_datetime else None,
                        "temporal_range_end": str(input_data_end_datetime) if input_data_end_datetime else None,
                    }
                ],
                
                # Output Structure  
                output_structure={
                    "output_type": "MarketPredictionMultiModel",
                    "prediction_values_count": len(parsed_schema.price_prediction),
                    "investment_rating_included": True,
                    "schema_version": "v1.0"
                },
                
                # Value Context Summary
                prediction_values_start_timestamp_utc=prediction_start_datetime,
                prediction_values_end_timestamp_utc=prediction_end_datetime,
                prediction_steps_count=len(parsed_schema.price_prediction),
                prediction_step_timeframe=prediction_step_timeframe,
                
                # Prediction Status
                prediction_status=ProgressStatus.DONE,
                retry_attempts=None,
                prediction_error=None,
                
                # Prediction Execution Context
                prediction_approach="single",
                prediction_requested_datetime_utc=prediction_requested_datetime_utc,
                prediction_received_datetime_utc=prediction_received_datetime_utc,
                prediction_cost_usd=cost_usd,
                
                # LLM-Specific Fields
                input_tokens_count=usage_metadata.prompt_token_count or 0,
                thinking_tokens_count=usage_metadata.thoughts_token_count,
                output_tokens_count=usage_metadata.candidates_token_count or 0,
                total_output_tokens_billed=usage_metadata.total_token_count or 0,
                finish_reason=(
                    gemini_response.candidates[0].finish_reason.name 
                    if gemini_response.candidates else None
                ),
                reasoning_trace=None,  # Not provided in current response format
                raw_response=cls._serialize_gemini_response(gemini_response),
                
                # Metadata
                tags=tags,
                metadata={
                    "gemini_response_id": gemini_response.response_id,
                    "model_version": model_version_id,
                    "asset_category": asset_category_detailed.value,
                    "batched": batched
                },
                
                # BaseNoSQLModel required fields
                created_by=created_by,
                created_at=datetime.now(timezone.utc),
                updated_by=created_by,
                updated_at=datetime.now(timezone.utc)
            )

            # 2. Create TimeSeriesPredictionValuesFincore (quantitative predictions)
            prediction_values = []
            for point in parsed_schema.price_prediction:
                prediction_values.append(TimeSeriesPredictionValuesFincore(
                    # Core Identity - No separate values_id needed, differentiated by timestamp
                    prediction_values_id=None,  # Optional field since timestamp + log_id is sufficient
                    prediction_log_id=prediction_log_id,
                    
                    # Value Point Structure
                    prediction_timestamp_utc=point.prediction_date,
                    prediction_value=point.prediction_value,
                    prediction_value_upper_bound=point.prediction_value_upper_bound,
                    prediction_value_lower_bound=point.prediction_value_lower_bound,
                    prediction_confidence_score=point.confidence_score,
                    
                    # Time Series Components (optional for LLM predictions)
                    trend_component=None,
                    seasonal_component=None,
                    residual_component=None,
                    
                    # Quality Indicators (optional)
                    is_anomaly=None,
                    uncertainty_score=None,
                    
                    # Market-Specific Analysis (if available in schema)
                    key_milestones_and_events=getattr(point, 'key_milestones_and_events', None),
                    most_influencing_technical_factors=getattr(point, 'technical_factors', None),
                    most_influencing_fundamental_factors=getattr(point, 'fundamental_factors', None),

                    # BaseNoSQLModel required fields
                    created_by=created_by,
                    created_at=datetime.now(timezone.utc),
                    updated_by=created_by,
                    updated_at=datetime.now(timezone.utc)
                ))

            # 3. Create FincorePredictionInvestmentRating (qualitative analysis)
            # Convert key assumptions list to string
            key_assumptions_str = None
            if parsed_schema.key_assumptions:
                key_assumptions_str = "; ".join(parsed_schema.key_assumptions)

            # Create asset-specific risk model
            key_risks = cls._create_asset_specific_risks(parsed_schema, asset_category_detailed)

            investment_rating = FincorePredictionAssetRating(
                # Core Identity
                investment_rating_id=investment_rating_id,
                prediction_log_id=prediction_log_id,  # Links to the prediction that generated this analysis
                target_subject_id=target_subject_id,
                target_subject_symbol=target_subject_symbol,
                analysis_timestamp_utc=prediction_received_datetime_utc,
                
                # Investment Analysis
                key_prediction_assumptions=key_assumptions_str,
                overall_rating=getattr(parsed_schema, 'overall_rating', None),
                investment_thesis=getattr(parsed_schema, 'investment_thesis', None),
                
                # Risk Analysis
                key_risks=key_risks,
                volatility_assessment=getattr(parsed_schema, 'volatility_assessment', None),
                
                # Supporting Analysis (if available in schema)
                macroeconomic_supportive_conditions_analysis=getattr(parsed_schema, 'macroeconomic_analysis', None),
                market_conditions_analysis=getattr(parsed_schema, 'market_conditions_analysis', None),
                sector_conditions_analysis=getattr(parsed_schema, 'sector_analysis', None),
                competitive_positioning_analysis=getattr(parsed_schema, 'competitive_analysis', None),
                
                # Recommendations (if available)
                time_horizon_days=getattr(parsed_schema, 'time_horizon_days', None),
                
                # Metadata
                confidence_in_analysis=getattr(parsed_schema, 'confidence_in_analysis', None),
                analysis_metadata={
                    "gemini_response_id": gemini_response.response_id,
                    "model_version": model_version_id,
                    "asset_category": asset_category_detailed.value,
                    "generated_from_prediction": prediction_log_id
                },
                
                # BaseNoSQLModel required fields
                created_by=created_by,
                created_at=datetime.now(timezone.utc),
                updated_by=created_by,
                updated_at=datetime.now(timezone.utc
            )

            return prediction_log, prediction_values, investment_rating

        except (ValueError, AttributeError, TypeError) as e:
            # Create minimal error models
            error_log_id = f"error_{uuid.uuid4()}"
            
            error_log = TimeSeriesPredictionLog(
                prediction_log_id=error_log_id,
                prediction_purpose=prediction_purpose,
                target_subject_id=target_subject_id,
                target_subject_name=target_subject_name,
                predicted_records_type=predicted_records_type,
                target_subject_description={},
                model_specification_id=model_specification_id,
                model_name=model_name,
                model_version_id=model_version_id,
                model_version_name=model_version_name,
                model_features_used=model_features_used,
                model_serving_instance_id=None,
                model_serving_instance_name=None,
                input_structure=[],
                output_structure={"error": str(e)},
                prediction_values_start_timestamp_utc=None,
                prediction_values_end_timestamp_utc=None,
                prediction_steps_count=0,
                prediction_step_timeframe=prediction_step_timeframe,
                prediction_status=ProgressStatus.FAILED,
                retry_attempts=None,
                prediction_error=str(e),
                prediction_approach="single",
                prediction_requested_datetime_utc=prediction_requested_datetime_utc,
                prediction_received_datetime_utc=prediction_received_datetime_utc,
                prediction_cost_usd=0.0,
                input_tokens_count=0,
                thinking_tokens_count=None,
                output_tokens_count=0,
                total_output_tokens_billed=0,
                finish_reason="ERROR",
                reasoning_trace=None,
                raw_response={"error": str(e)},
                tags=tags,
                metadata={"error": str(e)},
                created_by=created_by,
                updated_by=created_by,
            )
            
            return error_log, [], FincorePredictionInvestmentRating(
                investment_rating_id=f"error_rating_{uuid.uuid4()}",
                prediction_log_id=error_log_id,
                target_subject_id=target_subject_id,
                target_subject_symbol=target_subject_name,
                analysis_timestamp_utc=prediction_received_datetime_utc,
                key_prediction_assumptions=None,
                overall_rating=None,
                investment_thesis=None,
                key_risks=None,
                volatility_assessment=None,
                macroeconomic_supportive_conditions_analysis=None,
                market_conditions_analysis=None,
                sector_conditions_analysis=None,
                competitive_positioning_analysis=None,
                time_horizon_days=None,
                confidence_in_analysis=None,
                analysis_metadata={"error": str(e)},
                created_by=created_by,
                updated_by=created_by,
            )

    @classmethod
    def _validate_gemini_response(cls, gemini_response) -> bool:
        """Validate that the Gemini response has the expected structure."""
        try:
            return (
                hasattr(gemini_response, 'parsed') and
                hasattr(gemini_response, 'usage_metadata') and
                hasattr(gemini_response.parsed, 'price_prediction')
            )
        except (AttributeError, TypeError):
            return False

    @classmethod
    def _calculate_cost(cls, usage_metadata, batched: bool = False) -> float:
        """Calculate the cost in USD based on token usage."""
        try:
            input_tokens = usage_metadata.prompt_token_count or 0
            output_tokens = usage_metadata.candidates_token_count or 0
            
            if batched:
                input_cost = (input_tokens / 1_000_000) * cls.GEMINI_BATCHED_INPUT_COST_USD_PER_1M_TOKENS
                output_cost = (output_tokens / 1_000_000) * cls.GEMINI_BATCHED_OUTPUT_COST_USD_PER_1M_TOKENS
            else:
                input_cost = (input_tokens / 1_000_000) * cls.GEMINI_INPUT_COST_USD_PER_1M_TOKENS
                output_cost = (output_tokens / 1_000_000) * cls.GEMINI_OUTPUT_COST_USD_PER_1M_TOKENS
            
            return round(input_cost + output_cost, 6)
        except (AttributeError, TypeError, ValueError):
            return 0.0

    @classmethod
    def _create_asset_specific_risks(
        cls, 
        parsed_schema: LLMPromptJSONResponseSchemaForMarketPrediction, 
        subject_category_detailed: FincoreCategoryDetailed
    ) -> Optional[MarketKeyRisks]:
        """Create asset-specific risk model based on the category."""
        try:
            # Extract risk data from parsed schema
            risk_data = getattr(parsed_schema, 'key_risks', None)
            if not risk_data:
                return None

            # Create appropriate risk model based on subject category using correct enum values
            # Crypto assets
            if subject_category_detailed in [FincoreCategoryDetailed.CRYPTO_COIN, FincoreCategoryDetailed.CRYPTO_TOKEN, 
                                           FincoreCategoryDetailed.STABLECOIN, FincoreCategoryDetailed.DEFI_GOV_TOKEN]:
                return CryptoKeyRisks(
                    regulatory_risks=getattr(risk_data, 'regulatory_risks', ""),
                    macroeconomic_risks=getattr(risk_data, 'macroeconomic_risks', ""),
                    political_and_geopolitical_risks=getattr(risk_data, 'political_and_geopolitical_risks', ""),
                    climate_and_environmental_risks=getattr(risk_data, 'climate_and_environmental_risks', ""),
                    adoption_risks=getattr(risk_data, 'adoption_risks', ""),
                    security_risks=getattr(risk_data, 'security_risks', ""),
                    volatility_risks=getattr(risk_data, 'volatility_risks', ""),
                    liquidity_risks=getattr(risk_data, 'liquidity_risks', "")
                )
            # Commodity assets
            elif subject_category_detailed in [FincoreCategoryDetailed.PRECIOUS_METAL, FincoreCategoryDetailed.INDUSTRIAL_METAL, 
                                             FincoreCategoryDetailed.ENERGY, FincoreCategoryDetailed.AGRICULTURE]:
                return CommodityKeyRisks(
                    regulatory_risks=getattr(risk_data, 'regulatory_risks', ""),
                    macroeconomic_risks=getattr(risk_data, 'macroeconomic_risks', ""),
                    political_and_geopolitical_risks=getattr(risk_data, 'political_and_geopolitical_risks', ""),
                    climate_and_environmental_risks=getattr(risk_data, 'climate_and_environmental_risks', ""),
                    supply_demand_imbalance_risks=getattr(risk_data, 'supply_demand_imbalance_risks', ""),
                    producer_risks=getattr(risk_data, 'producer_risks', ""),
                    substitute_risks=getattr(risk_data, 'substitute_risks', ""),
                    inventory_risks=getattr(risk_data, 'inventory_risks', "")
                )
            # ETF assets
            elif subject_category_detailed in [FincoreCategoryDetailed.EQUITY_FUND, FincoreCategoryDetailed.BOND_FUND,
                                             FincoreCategoryDetailed.COMMODITY_FUND, FincoreCategoryDetailed.INDEX_FUND]:
                return ETFKeyRisks(
                    regulatory_risks=getattr(risk_data, 'regulatory_risks', ""),
                    macroeconomic_risks=getattr(risk_data, 'macroeconomic_risks', ""),
                    political_and_geopolitical_risks=getattr(risk_data, 'political_and_geopolitical_risks', ""),
                    climate_and_environmental_risks=getattr(risk_data, 'climate_and_environmental_risks', ""),
                    counterparty_risks=getattr(risk_data, 'counterparty_risks', ""),
                    management_risks=getattr(risk_data, 'management_risks', ""),
                    expense_and_fees_risks=getattr(risk_data, 'expense_and_fees_risks', ""),
                    closure_risks=getattr(risk_data, 'closure_risks', None)
                )
            # Stock assets (be specific about what gets stock risks)
            elif subject_category_detailed in [FincoreCategoryDetailed.COMMON_STOCK, FincoreCategoryDetailed.PREFERRED_STOCK]:
                return StockKeyRisks(
                    regulatory_risks=getattr(risk_data, 'regulatory_risks', ""),
                    macroeconomic_risks=getattr(risk_data, 'macroeconomic_risks', ""),
                    political_and_geopolitical_risks=getattr(risk_data, 'political_and_geopolitical_risks', ""),
                    climate_and_environmental_risks=getattr(risk_data, 'climate_and_environmental_risks', ""),
                    competitive_risks=getattr(risk_data, 'competitive_risks', ""),
                    operational_execution_risks=getattr(risk_data, 'operational_execution_risks', ""),
                    management_risks=getattr(risk_data, 'management_risks', ""),
                    financial_risks=getattr(risk_data, 'financial_risks', ""),
                    sector_specific_risks=getattr(risk_data, 'sector_specific_risks', ""),
                    contract_and_ownership_type_risks=getattr(risk_data, 'contract_and_ownership_type_risks', None)
                )
            # Default to base risks for everything else
            else:
                return BaseFincoreKeyRisks(
                    regulatory_risks=getattr(risk_data, 'regulatory_risks', ""),
                    macroeconomic_risks=getattr(risk_data, 'macroeconomic_risks', ""),
                    political_and_geopolitical_risks=getattr(risk_data, 'political_and_geopolitical_risks', ""),
                    climate_and_environmental_risks=getattr(risk_data, 'climate_and_environmental_risks', "")
                )
                
        except (AttributeError, TypeError, ValueError):
            return None

    @classmethod
    def _serialize_gemini_response(cls, gemini_response) -> Dict[str, Any]:
        """Serialize Gemini response for storage."""
        try:
            return {
                "response_id": gemini_response.response_id,
                "candidates_count": len(gemini_response.candidates) if gemini_response.candidates else 0,
                "finish_reason": (
                    gemini_response.candidates[0].finish_reason.name 
                    if gemini_response.candidates else None
                ),
                "usage_metadata": {
                    "prompt_token_count": gemini_response.usage_metadata.prompt_token_count,
                    "candidates_token_count": gemini_response.usage_metadata.candidates_token_count,
                    "total_token_count": gemini_response.usage_metadata.total_token_count,
                    "thoughts_token_count": getattr(gemini_response.usage_metadata, 'thoughts_token_count', None)
                }
            }
        except (AttributeError, TypeError):
            return {"error": "Failed to serialize response"}


# Legacy compatibility alias (deprecated - use FincoreGeminiSDKResponseTranslator)
TimeSeriesMarketLLMPredictionGeminiSDKResponseTranslator = GeminiSDKResponseToTimeSeriesPredictionFincore
