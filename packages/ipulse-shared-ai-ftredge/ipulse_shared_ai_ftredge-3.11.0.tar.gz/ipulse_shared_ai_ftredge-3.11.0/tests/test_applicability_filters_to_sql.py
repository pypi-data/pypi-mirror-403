"""
Unit tests for applicability_filters_to_sql module.

Tests SQL WHERE clause generation from AI component applicability rules.
"""

import json
from ipulse_shared_base_ftredge.enums.enums_pulse import ScopingField
from ipulse_shared_base_ftredge.enums.enums_status import ObjectOverallStatus
from ipulse_shared_ai_ftredge.utils.applicability_filters_to_sql import (
    generate_bigquery_where_clause,
    _parse_constraints_to_sql
)
from ipulse_shared_ai_ftredge.models.intelligence_designs.analyst_persona import AnalystPersona


def create_test_persona(**kwargs):
    """Helper to create AnalystPersona with minimal required fields."""
    defaults = {
        "persona_id": "test_persona_id",
        "persona_name": "test__persona",
        "persona_character": "test_character",
        "persona_character_display_name": "Test Character",
        "persona_archetype": "test_archetype",
        "persona_archetype_display_name": "Test Archetype",
        "persona_identity_display_brief": "Test persona for unit testing",
        "primary_cognitive_style": "value_purist",
        "primary_cognitive_style_display_name": "Value Purist",
        "persona_variant": "standard",
        "persona_variant_display_name": "Standard",
        "moods": "balanced",
        "moods_display_names": "Balanced",
        "compatible_thinking_horizons": "tactical_investment",
        "compatible_modes": "thinker",
        "analyst_persona_definition": "Test persona definition"
    }
    defaults.update(kwargs)
    return AnalystPersona(**defaults)


class TestGenerateBigQueryWhereClause:
    """Tests for generate_bigquery_where_clause function."""
    
    def test_basic_level_0_filtering(self):
        """Test basic LEVEL 0 sector_records_category filtering."""
        component = create_test_persona(
            applicable_sector_records_categories="market,fundamental"
        )
        
        where_clause = generate_bigquery_where_clause(component, "assets")
        
        assert "assets.sector_records_category IN ('market', 'fundamental')" in where_clause
    
    def test_basic_level_1_filtering(self):
        """Test basic LEVEL 1 subject_category filtering."""
        component = create_test_persona(
            applicable_sector_records_categories="market",
            applicable_subject_categories="equity,index"
        )
        
        where_clause = generate_bigquery_where_clause(component, "assets")
        
        assert "assets.sector_records_category IN ('market')" in where_clause
        assert "assets.subject_category IN ('equity', 'index')" in where_clause
        assert " AND " in where_clause
    
    def test_level_2_simple_in_constraint(self):
        """Test LEVEL 2 with simple IN constraint."""
        constraints = {
            "industry": ["software", "semiconductors"]
        }
        component = create_test_persona(
            applicable_sector_records_categories="market",
            applicable_subject_categories="equity",
            applicability_constraints=json.dumps(constraints)
        )
        
        where_clause = generate_bigquery_where_clause(component, "s")
        
        assert "s.industry IN ('software', 'semiconductors')" in where_clause
    
    def test_level_2_gt_operator(self):
        """Test LEVEL 2 with GT operator."""
        constraints = {
            "market_cap": {
                "operator": "GT",
                "value": 10000000000
            }
        }
        component = create_test_persona(
            applicable_sector_records_categories="market",
            applicability_constraints=json.dumps(constraints)
        )
        
        where_clause = generate_bigquery_where_clause(component, "assets")
        
        assert "assets.market_cap > 10000000000" in where_clause
    
    def test_level_2_between_operator(self):
        """Test LEVEL 2 with BETWEEN operator."""
        constraints = {
            "pe_ratio": {
                "operator": "BETWEEN",
                "values": [10, 25]
            }
        }
        component = create_test_persona(
            applicable_sector_records_categories="market",
            applicability_constraints=json.dumps(constraints)
        )
        
        where_clause = generate_bigquery_where_clause(component, "assets")
        
        assert "assets.pe_ratio BETWEEN 10 AND 25" in where_clause
    
    def test_level_3_whitelist(self):
        """Test LEVEL 3 manual whitelist (include_subjects)."""
        overrides = {
            "include_subjects": ["AAPL", "MSFT", "GOOGL"]
        }
        component = create_test_persona(
            applicable_sector_records_categories="market",
            manual_subjects_overrides=json.dumps(overrides)
        )
        
        where_clause = generate_bigquery_where_clause(component, "assets")
        
        assert "assets.subject_id IN ('AAPL', 'MSFT', 'GOOGL')" in where_clause
    
    def test_level_3_blacklist(self):
        """Test LEVEL 3 manual blacklist (exclude_subjects)."""
        overrides = {
            "exclude_subjects": ["EXCLUDED_TICKER"]
        }
        component = create_test_persona(
            applicable_sector_records_categories="market",
            manual_subjects_overrides=json.dumps(overrides)
        )
        
        where_clause = generate_bigquery_where_clause(component, "assets")
        
        assert "assets.subject_id NOT IN ('EXCLUDED_TICKER')" in where_clause
    
    def test_pulse_statuses_to_have(self):
        """Test pulse_statuses_to_have parameter."""
        component = create_test_persona(
            applicable_sector_records_categories="market"
        )
        
        where_clause = generate_bigquery_where_clause(
            component,
            "assets",
            pulse_statuses_to_have=[ObjectOverallStatus.ACTIVE]
        )
        
        assert "assets.pulse_status IN ('ACTIVE')" in where_clause
    
    def test_pulse_statuses_to_avoid(self):
        """Test pulse_statuses_to_avoid parameter."""
        component = create_test_persona(
            applicable_sector_records_categories="market"
        )
        
        where_clause = generate_bigquery_where_clause(
            component,
            "assets",
            pulse_statuses_to_avoid=[ObjectOverallStatus.ARCHIVED, ObjectOverallStatus.DELETED]
        )
        
        assert "assets.pulse_status NOT IN ('ARCHIVED', 'DELETED')" in where_clause
    
    def test_exclude_fields(self):
        """Test exclude_fields parameter."""
        component = create_test_persona(
            applicable_sector_records_categories="market",
            applicable_subject_categories="equity"
        )
        
        # Exclude LEVEL 0 field
        where_clause = generate_bigquery_where_clause(
            component,
            "assets",
            exclude_fields=[ScopingField.SECTOR_RECORDS_CATEGORY]
        )
        
        assert "sector_records_category" not in where_clause
        assert "assets.subject_category IN ('equity')" in where_clause
    
    def test_field_mapping(self):
        """Test field_mapping parameter."""
        component = create_test_persona(
            applicable_sector_records_categories="market",
            applicable_subject_categories="equity"
        )
        
        field_mapping = {
            ScopingField.SECTOR_RECORDS_CATEGORY: "data_category",
            ScopingField.SUBJECT_CATEGORY: "asset_type"
        }
        
        where_clause = generate_bigquery_where_clause(
            component,
            "assets",
            field_mapping=field_mapping
        )
        
        assert "assets.data_category IN ('market')" in where_clause
        assert "assets.asset_type IN ('equity')" in where_clause
    
    def test_custom_table_alias(self):
        """Test custom table alias."""
        component = create_test_persona(
            applicable_sector_records_categories="market"
        )
        
        where_clause = generate_bigquery_where_clause(component, "my_table")
        
        assert "my_table.sector_records_category IN ('market')" in where_clause
    
    def test_empty_component_filters(self):
        """Test component with no filters (should return TRUE)."""
        component = create_test_persona()
        
        where_clause = generate_bigquery_where_clause(component, "assets")
        
        assert where_clause == "TRUE"
    
    def test_combined_all_levels(self):
        """Test SQL generation with all 4 levels."""
        constraints = {
            "industry": ["software"],
            "market_cap": {
                "operator": "GT",
                "value": 10000000000
            }
        }
        overrides = {
            "exclude_subjects": ["EXCLUDED"]
        }
        component = create_test_persona(
            applicable_sector_records_categories="market",
            applicable_subject_categories="equity",
            applicability_constraints=json.dumps(constraints),
            manual_subjects_overrides=json.dumps(overrides)
        )
        
        where_clause = generate_bigquery_where_clause(
            component,
            "a",
            pulse_statuses_to_have=[ObjectOverallStatus.ACTIVE]
        )
        
        # Check all 4 levels + pulse_status
        assert "a.sector_records_category IN ('market')" in where_clause
        assert "a.subject_category IN ('equity')" in where_clause
        assert "a.industry IN ('software')" in where_clause
        assert "a.market_cap > 10000000000" in where_clause
        assert "a.subject_id NOT IN ('EXCLUDED')" in where_clause
        assert "a.pulse_status IN ('ACTIVE')" in where_clause
        assert where_clause.count(" AND ") >= 5  # At least 5 AND operators


class TestParseConstraintsToSql:
    """Tests for _parse_constraints_to_sql helper function."""
    
    def test_simple_in_constraint(self):
        """Test simple IN constraint (default)."""
        constraints = {"industry": ["software", "semiconductors"]}
        sql = _parse_constraints_to_sql(constraints, "t")
        
        assert "t.industry IN ('software', 'semiconductors')" == sql
    
    def test_not_in_operator(self):
        """Test NOT_IN operator."""
        constraints = {
            "industry": {
                "operator": "NOT_IN",
                "values": ["tobacco", "gambling"]
            }
        }
        sql = _parse_constraints_to_sql(constraints, "t")
        
        assert "t.industry NOT IN ('tobacco', 'gambling')" == sql
    
    def test_equals_operator(self):
        """Test EQUALS operator."""
        constraints = {
            "region": {
                "operator": "EQUALS",
                "value": "north_america"
            }
        }
        sql = _parse_constraints_to_sql(constraints, "t")
        
        assert "t.region = 'north_america'" == sql
    
    def test_comparison_operators(self):
        """Test GT, GTE, LT, LTE operators."""
        # GT
        constraints_gt = {"market_cap": {"operator": "GT", "value": 1000000}}
        assert "t.market_cap > 1000000" == _parse_constraints_to_sql(constraints_gt, "t")
        
        # GTE
        constraints_gte = {"market_cap": {"operator": "GTE", "value": 1000000}}
        assert "t.market_cap >= 1000000" == _parse_constraints_to_sql(constraints_gte, "t")
        
        # LT
        constraints_lt = {"pe_ratio": {"operator": "LT", "value": 20}}
        assert "t.pe_ratio < 20" == _parse_constraints_to_sql(constraints_lt, "t")
        
        # LTE
        constraints_lte = {"pe_ratio": {"operator": "LTE", "value": 20}}
        assert "t.pe_ratio <= 20" == _parse_constraints_to_sql(constraints_lte, "t")
    
    def test_between_operator(self):
        """Test BETWEEN operator."""
        constraints = {
            "pe_ratio": {
                "operator": "BETWEEN",
                "values": [10, 25]
            }
        }
        sql = _parse_constraints_to_sql(constraints, "t")
        
        assert "t.pe_ratio BETWEEN 10 AND 25" == sql
    
    def test_or_logic(self):
        """Test OR logic with constraint_groups."""
        constraints = {
            "_logic": "OR",
            "constraint_groups": [
                {"industry": ["software"]},
                {"industry": ["semiconductors"]}
            ]
        }
        sql = _parse_constraints_to_sql(constraints, "t")
        
        assert " OR " in sql
        assert "t.industry IN ('software')" in sql
        assert "t.industry IN ('semiconductors')" in sql
    
    def test_multiple_constraints_and_logic(self):
        """Test multiple constraints with AND logic (default)."""
        constraints = {
            "industry": ["software"],
            "market_cap": {
                "operator": "GT",
                "value": 10000000000
            }
        }
        sql = _parse_constraints_to_sql(constraints, "t")
        
        assert " AND " in sql
        assert "t.industry IN ('software')" in sql
        assert "t.market_cap > 10000000000" in sql
    
    def test_exclude_fields_in_parsing(self):
        """Test exclude_set parameter."""
        constraints = {
            "industry": ["software"],
            "market_cap": {"operator": "GT", "value": 1000000}
        }
        exclude_set = {"industry"}
        
        sql = _parse_constraints_to_sql(constraints, "t", exclude_set)
        
        assert "industry" not in sql
        assert "t.market_cap > 1000000" == sql
    
    def test_field_mapping_in_parsing(self):
        """Test field_mapping parameter."""
        constraints = {
            "market_cap": {"operator": "GT", "value": 1000000}
        }
        field_mapping = {ScopingField.MARKET_CAP: "mkt_cap_usd"}
        
        sql = _parse_constraints_to_sql(constraints, "t", None, field_mapping)
        
        assert "t.mkt_cap_usd > 1000000" == sql
    
    def test_numeric_values_not_quoted(self):
        """Test that numeric values are not quoted in SQL."""
        constraints = {
            "market_cap": {"operator": "GT", "value": 10000000000}
        }
        sql = _parse_constraints_to_sql(constraints, "t")
        
        # Numeric value should not be quoted
        assert "t.market_cap > 10000000000" == sql
        assert "t.market_cap > '10000000000'" not in sql
    
    def test_string_values_quoted(self):
        """Test that string values are properly quoted in SQL."""
        constraints = {
            "region": {
                "operator": "EQUALS",
                "value": "north_america"
            }
        }
        sql = _parse_constraints_to_sql(constraints, "t")
        
        # String value should be quoted
        assert "t.region = 'north_america'" == sql
