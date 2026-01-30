"""
Unit tests for applicability_filter_on_prefetched_data module.

Tests the 4-level hierarchical filtering logic for AI components based on subject metadata.
"""

import json
from ipulse_shared_ai_ftredge.utils.applicability_filter_on_prefetched_data import (
    filter_components_by_applicability,
    check_applicability_constraints,
    is_manually_excluded,
    is_manually_included,
    get_applicable_components_summary
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


class TestFilterComponentsByApplicability:
    """Tests for the main filter_components_by_applicability function."""
    
    def test_empty_components_list(self):
        """Test filtering with empty components list."""
        subject = {
            "sector_records_category": "market",
            "subject_category": "equity"
        }
        
        result = filter_components_by_applicability([], subject)
        assert result == []
    
    def test_level_0_filtering_sector_records_category(self):
        """Test LEVEL 0 filtering by sector_records_category."""
        component = create_test_persona(
            applicable_sector_records_categories="market,fundamental"
        )
        
        # Subject matching sector_records_category
        subject_match = {
            "sector_records_category": "market"
        }
        
        result = filter_components_by_applicability([component], subject_match)
        assert len(result) == 1
        assert result[0] == component
        
        # Subject not matching sector_records_category
        subject_no_match = {
            "sector_records_category": "event"
        }
        result = filter_components_by_applicability([component], subject_no_match)
        assert len(result) == 0
    
    def test_level_1_filtering_subject_category(self):
        """Test LEVEL 1 filtering by subject_category."""
        component = create_test_persona(
            applicable_sector_records_categories="market",
            applicable_subject_categories="equity,index"
        )
        
        # Subject matching both LEVEL 0 and LEVEL 1
        subject_match = {
            "sector_records_category": "market",
            "subject_category": "equity"
        }
        
        result = filter_components_by_applicability([component], subject_match)
        assert len(result) == 1
        
        # Subject matching LEVEL 0 but not LEVEL 1
        subject_no_match = {
            "sector_records_category": "market",
            "subject_category": "crypto"
        }
        
        result = filter_components_by_applicability([component], subject_no_match)
        assert len(result) == 0
    
    def test_level_2_filtering_simple_constraints(self):
        """Test LEVEL 2 filtering with simple constraints."""
        constraints = {
            "industry": ["software", "semiconductors"]
        }
        component = create_test_persona(
            applicable_sector_records_categories="market",
            applicable_subject_categories="equity",
            applicability_constraints=json.dumps(constraints)
        )
        
        # Subject matching all levels including constraints
        subject_match = {
            "sector_records_category": "market",
            "subject_category": "equity",
            "industry": "software"
        }
        
        result = filter_components_by_applicability([component], subject_match)
        assert len(result) == 1
        
        # Subject not matching constraints
        subject_no_match = {
            "sector_records_category": "market",
            "subject_category": "equity",
            "industry": "energy"
        }
        
        result = filter_components_by_applicability([component], subject_no_match)
        assert len(result) == 0
    
    def test_level_3_manual_overrides_whitelist(self):
        """Test LEVEL 3 manual whitelist (include_subjects)."""
        overrides = {
            "include_subjects": ["AAPL", "MSFT", "GOOGL"]
        }
        component = create_test_persona(
            applicable_sector_records_categories="market",
            applicable_subject_categories="equity",
            manual_subjects_overrides=json.dumps(overrides)
        )
        
        # Subject in whitelist (should pass even if other filters don't match)
        subject_whitelisted = {
            "sector_records_category": "fundamental",  # Doesn't match
            "subject_id": "AAPL"
        }
        
        result = filter_components_by_applicability([component], subject_whitelisted)
        assert len(result) == 1
        
        # Subject not in whitelist (should fail)
        subject_not_whitelisted = {
            "sector_records_category": "market",  # Matches
            "subject_category": "equity",  # Matches
            "subject_id": "TSLA"  # Not in whitelist
        }
        
        result = filter_components_by_applicability([component], subject_not_whitelisted)
        assert len(result) == 0
    
    def test_level_3_manual_overrides_blacklist(self):
        """Test LEVEL 3 manual blacklist (exclude_subjects)."""
        overrides = {
            "exclude_subjects": ["EXCLUDED_TICKER"]
        }
        component = create_test_persona(
            applicable_sector_records_categories="market",
            applicable_subject_categories="equity",
            manual_subjects_overrides=json.dumps(overrides)
        )
        
        # Subject in blacklist (should be excluded)
        subject_blacklisted = {
            "sector_records_category": "market",
            "subject_category": "equity",
            "subject_id": "EXCLUDED_TICKER"
        }
        
        result = filter_components_by_applicability([component], subject_blacklisted)
        assert len(result) == 0
        
        # Subject not in blacklist (should pass)
        subject_not_blacklisted = {
            "sector_records_category": "market",
            "subject_category": "equity",
            "subject_id": "AAPL"
        }
        
        result = filter_components_by_applicability([component], subject_not_blacklisted)
        assert len(result) == 1
    
    def test_string_keys_fallback(self):
        """Test that string keys still work (backward compatibility)."""
        component = create_test_persona(
            applicable_sector_records_categories="market",
            applicable_subject_categories="equity"
        )
        
        # Subject metadata with plain string keys (should still work)
        subject = {
            "sector_records_category": "market",
            "subject_category": "equity"
        }
        
        result = filter_components_by_applicability([component], subject)
        assert len(result) == 1


class TestCheckApplicabilityConstraints:
    """Tests for the check_applicability_constraints function."""
    
    def test_simple_in_constraint_match(self):
        """Test simple IN constraint (default operator) with match."""
        constraints = {"industry": ["software", "semiconductors"]}
        subject_meta = {"industry": "software"}
        
        assert check_applicability_constraints(constraints, subject_meta) is True
    
    def test_simple_in_constraint_no_match(self):
        """Test simple IN constraint with no match."""
        constraints = {"industry": ["software", "semiconductors"]}
        subject_meta = {"industry": "energy"}
        
        assert check_applicability_constraints(constraints, subject_meta) is False
    
    def test_not_in_operator(self):
        """Test NOT_IN operator."""
        constraints = {
            "industry": {
                "operator": "NOT_IN",
                "values": ["tobacco", "gambling"]
            }
        }
        
        # Subject not in excluded list (should pass)
        subject_valid = {"industry": "software"}
        assert check_applicability_constraints(constraints, subject_valid) is True
        
        # Subject in excluded list (should fail)
        subject_invalid = {"industry": "tobacco"}
        assert check_applicability_constraints(constraints, subject_invalid) is False
    
    def test_equals_operator(self):
        """Test EQUALS operator."""
        constraints = {
            "region": {
                "operator": "EQUALS",
                "value": "north_america"
            }
        }
        subject_match = {"region": "north_america"}
        subject_no_match = {"region": "europe"}
        
        assert check_applicability_constraints(constraints, subject_match) is True
        assert check_applicability_constraints(constraints, subject_no_match) is False
    
    def test_gt_operator(self):
        """Test GT (greater than) operator."""
        constraints = {
            "market_cap": {
                "operator": "GT",
                "value": 10000000000
            }
        }
        subject_pass = {"market_cap": 15000000000}
        subject_fail = {"market_cap": 5000000000}
        
        assert check_applicability_constraints(constraints, subject_pass) is True
        assert check_applicability_constraints(constraints, subject_fail) is False
    
    def test_gte_operator(self):
        """Test GTE (greater than or equal) operator."""
        constraints = {
            "market_cap": {
                "operator": "GTE",
                "value": 10000000000
            }
        }
        subject_greater = {"market_cap": 15000000000}
        subject_equal = {"market_cap": 10000000000}
        subject_less = {"market_cap": 5000000000}
        
        assert check_applicability_constraints(constraints, subject_greater) is True
        assert check_applicability_constraints(constraints, subject_equal) is True
        assert check_applicability_constraints(constraints, subject_less) is False
    
    def test_lt_operator(self):
        """Test LT (less than) operator."""
        constraints = {
            "pe_ratio": {
                "operator": "LT",
                "value": 20
            }
        }
        subject_pass = {"pe_ratio": 15}
        subject_fail = {"pe_ratio": 25}
        
        assert check_applicability_constraints(constraints, subject_pass) is True
        assert check_applicability_constraints(constraints, subject_fail) is False
    
    def test_lte_operator(self):
        """Test LTE (less than or equal) operator."""
        constraints = {
            "pe_ratio": {
                "operator": "LTE",
                "value": 20
            }
        }
        subject_less = {"pe_ratio": 15}
        subject_equal = {"pe_ratio": 20}
        subject_greater = {"pe_ratio": 25}
        
        assert check_applicability_constraints(constraints, subject_less) is True
        assert check_applicability_constraints(constraints, subject_equal) is True
        assert check_applicability_constraints(constraints, subject_greater) is False
    
    def test_between_operator(self):
        """Test BETWEEN operator."""
        constraints = {
            "pe_ratio": {
                "operator": "BETWEEN",
                "values": [10, 25]
            }
        }
        subject_in_range = {"pe_ratio": 15}
        subject_below = {"pe_ratio": 5}
        subject_above = {"pe_ratio": 30}
        
        assert check_applicability_constraints(constraints, subject_in_range) is True
        assert check_applicability_constraints(constraints, subject_below) is False
        assert check_applicability_constraints(constraints, subject_above) is False
    
    def test_or_logic(self):
        """Test OR logic with constraint_groups."""
        constraints = {
            "_logic": "OR",
            "constraint_groups": [
                {"industry": ["software"]},
                {"region": ["north_america"]}
            ]
        }
        
        subject_match_first = {"industry": "software", "region": "europe"}
        subject_match_second = {"industry": "energy", "region": "north_america"}
        subject_match_both = {"industry": "software", "region": "north_america"}
        subject_match_neither = {"industry": "energy", "region": "europe"}
        
        assert check_applicability_constraints(constraints, subject_match_first) is True
        assert check_applicability_constraints(constraints, subject_match_second) is True
        assert check_applicability_constraints(constraints, subject_match_both) is True
        assert check_applicability_constraints(constraints, subject_match_neither) is False
    
    def test_multiple_constraints_and_logic(self):
        """Test multiple constraints with AND logic (default)."""
        constraints = {
            "industry": ["software"],
            "market_cap": {
                "operator": "GT",
                "value": 10000000000
            }
        }
        
        subject_both_match = {"industry": "software", "market_cap": 15000000000}
        subject_only_industry = {"industry": "software", "market_cap": 5000000000}
        subject_only_market_cap = {"industry": "energy", "market_cap": 15000000000}
        
        assert check_applicability_constraints(constraints, subject_both_match) is True
        assert check_applicability_constraints(constraints, subject_only_industry) is False
        assert check_applicability_constraints(constraints, subject_only_market_cap) is False


class TestManualOverrides:
    """Tests for manual override functions."""
    
    def test_is_manually_excluded_with_blacklist(self):
        """Test is_manually_excluded with blacklist."""
        component = create_test_persona(
            manual_subjects_overrides=json.dumps({"exclude_subjects": ["TSLA", "GME"]})
        )
        
        assert is_manually_excluded(component, "TSLA") is True
        assert is_manually_excluded(component, "AAPL") is False
    
    def test_is_manually_excluded_no_overrides(self):
        """Test is_manually_excluded with no overrides."""
        component = create_test_persona()
        
        assert is_manually_excluded(component, "TSLA") is False
    
    def test_is_manually_included_with_whitelist(self):
        """Test is_manually_included with whitelist."""
        component = create_test_persona(
            manual_subjects_overrides=json.dumps({"include_subjects": ["AAPL", "MSFT"]})
        )
        
        assert is_manually_included(component, "AAPL") is True
        assert is_manually_included(component, "TSLA") is False
    
    def test_is_manually_included_no_whitelist(self):
        """Test is_manually_included with no whitelist."""
        component = create_test_persona()
        
        assert is_manually_included(component, "AAPL") is False


class TestGetApplicableComponentsSummary:
    """Tests for the get_applicable_components_summary function."""
    
    def test_summary_with_filtering(self):
        """Test summary generation with actual filtering."""
        components = [
            create_test_persona(
                applicable_sector_records_categories="market"
            ),
            create_test_persona(
                applicable_sector_records_categories="market",
                applicable_subject_categories="equity"
            ),
            create_test_persona(
                applicable_sector_records_categories="fundamental"
            )
        ]
        
        subject = {
            "sector_records_category": "market",
            "subject_category": "equity"
        }
        
        summary = get_applicable_components_summary(components, subject)
        
        assert summary["total_components"] == 3
        assert summary["passed_level_0"] == 2  # 2 components match market
        assert summary["passed_level_1"] == 2  # 2 components: one with None (all), one with equity
        assert summary["final_applicable"] == 2
        assert summary["reduction_pct"] > 0
