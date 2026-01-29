"""
Unit tests for AI Model Serialization/Deserialization

Tests the complete round-trip serialization and deserialization of AI models,
particularly focusing on string array handling for enum fields when interfacing with BigQuery.

Key test scenarios:
1. Normal Pydantic model creation and serialization
2. BigQuery string array format deserialization  
3. Round-trip data integrity verification
4. Error handling for malformed data
5. Edge cases with empty/null values
"""

import pytest
import json
from datetime import datetime, timezone
from typing import List, Optional

from ipulse_shared_ai_ftredge import AIModelSpecification
from ipulse_shared_base_ftredge import (
    AIProblemType, 
    AIAlgorithm, 
    AIArchitectureStructure,
    ObjectOverallStatus,
    make_json_serializable
)


class TestAIModelSpecificationSerialization:
    """Test suite for AIModelSpecification serialization/deserialization."""
    
    def create_sample_model_data(self) -> dict:
        """Create sample model data for testing."""
        return {
            'model_spec_id': 'test_model_123',
            'model_spec_name': 'Test AI Model',
            'model_spec_display_name': 'Test AI Model Display',
            'pulse_status': ObjectOverallStatus.ACTIVE,
            'model_generalization_level': 'generalized',
            'model_source': 'external_service',
            'model_author': 'Test Author',
            'model_provider_organization': 'OpenAI',
            'learning_paradigm': 'unsupervised',
            'supported_ai_problem_types': [AIProblemType.GENERATION, AIProblemType.QA],
            'ai_algorithms': [AIAlgorithm.TRANSFORMER],
            'ai_architecture_structure': AIArchitectureStructure.SINGLE,
            'created_by': 'test_user',
            'updated_by': 'test_user'
        }
    
    def test_normal_model_creation(self):
        """Test normal Pydantic model creation with enum lists."""
        data = self.create_sample_model_data()
        model = AIModelSpecification(**data)
        
        assert model.model_spec_id == 'test_model_123'
        assert len(model.supported_ai_problem_types) == 2
        assert model.supported_ai_problem_types[0] == AIProblemType.GENERATION
        assert model.supported_ai_problem_types[1] == AIProblemType.QA
        assert model.ai_algorithms is not None
        assert len(model.ai_algorithms) == 1
        assert model.ai_algorithms[0] == AIAlgorithm.TRANSFORMER
        assert model.ai_architecture_structure == AIArchitectureStructure.SINGLE
    
    def test_model_serialization_to_dict(self):
        """Test serialization to dictionary format."""
        data = self.create_sample_model_data()
        model = AIModelSpecification(**data)
        
        # Test normal serialization
        serialized = model.model_dump()
        assert isinstance(serialized['supported_ai_problem_types'], list)
        assert isinstance(serialized['ai_algorithms'], list)
        
        # Test BigQuery-ready serialization
        bq_ready = make_json_serializable(serialized)
        assert isinstance(bq_ready['supported_ai_problem_types'], list)
        assert all(isinstance(item, str) for item in bq_ready['supported_ai_problem_types'])
    
    def test_string_array_deserialization(self):
        """Test deserialization from BigQuery string array format."""
        # Simulate BigQuery data with string arrays
        bq_data = {
            'model_spec_id': 'test_bq_123',
            'model_spec_name': 'BigQuery Test Model',
            'model_spec_display_name': 'BigQuery Test Model Display',
            'pulse_status': ObjectOverallStatus.ACTIVE,
            'model_generalization_level': 'specialized',
            'model_source': 'internal',
            'model_author': 'BQ Test Author',
            'model_provider_organization': 'Internal Team',
            'learning_paradigm': 'supervised',
            'supported_ai_problem_types': '["regression", "classification"]',  # String format
            'ai_algorithms': '["random_forest", "xgboost"]',  # String format
            'ai_architecture_structure': 'ensemble',
            'created_by': 'bq_test_user',
            'updated_by': 'bq_test_user'
        }
        
        # Should work with custom validators
        model = AIModelSpecification(**bq_data)
        
        assert len(model.supported_ai_problem_types) == 2
        assert model.supported_ai_problem_types[0] == AIProblemType.REGRESSION
        assert model.supported_ai_problem_types[1] == AIProblemType.CLASSIFICATION
        assert model.ai_algorithms is not None
        assert len(model.ai_algorithms) == 2
        assert model.ai_algorithms[0] == AIAlgorithm.RANDOM_FOREST
        assert model.ai_algorithms[1] == AIAlgorithm.XGBOOST
    
    def test_complete_round_trip(self):
        """Test complete serialization → BigQuery → deserialization round trip."""
        # 1. Create original model
        original_data = self.create_sample_model_data()
        original_model = AIModelSpecification(**original_data)
        
        # 2. Serialize to dict
        serialized_dict = original_model.model_dump()
        bq_ready_dict = make_json_serializable(serialized_dict)
        
        # 3. Convert to BigQuery string format
        bq_data = bq_ready_dict.copy()
        bq_data['supported_ai_problem_types'] = json.dumps(bq_ready_dict['supported_ai_problem_types'])
        bq_data['ai_algorithms'] = json.dumps(bq_ready_dict['ai_algorithms'])
        
        # 4. Deserialize back from BigQuery format
        reconstructed_model = AIModelSpecification(**bq_data)
        
        # 5. Verify data integrity
        assert original_model.model_spec_id == reconstructed_model.model_spec_id
        assert original_model.supported_ai_problem_types == reconstructed_model.supported_ai_problem_types
        assert original_model.ai_algorithms == reconstructed_model.ai_algorithms
        assert original_model.ai_architecture_structure == reconstructed_model.ai_architecture_structure
    
    def test_empty_algorithms_list(self):
        """Test handling of empty algorithms list."""
        data = self.create_sample_model_data()
        data['ai_algorithms'] = []  # Empty list
        
        model = AIModelSpecification(**data)
        assert model.ai_algorithms == []
        
        # Test BigQuery round trip with empty list
        serialized = make_json_serializable(model.model_dump())
        bq_data = serialized.copy()
        bq_data['ai_algorithms'] = json.dumps([])
        
        reconstructed = AIModelSpecification(**bq_data)
        assert reconstructed.ai_algorithms == []
    
    def test_null_algorithms_field(self):
        """Test handling of null algorithms field."""
        data = self.create_sample_model_data()
        data['ai_algorithms'] = None  # Null value
        
        model = AIModelSpecification(**data)
        assert model.ai_algorithms is None
        
        # Test BigQuery handling - None should remain None
        serialized = make_json_serializable(model.model_dump())
        reconstructed = AIModelSpecification(**serialized)
        assert reconstructed.ai_algorithms is None
    
    def test_invalid_json_string_error_handling(self):
        """Test error handling for malformed JSON strings."""
        data = self.create_sample_model_data()
        data['supported_ai_problem_types'] = '["invalid_json"'  # Malformed JSON
        
        with pytest.raises(ValueError, match="Invalid supported_ai_problem_types format"):
            AIModelSpecification(**data)
    
    def test_invalid_enum_values_error_handling(self):
        """Test error handling for invalid enum values."""
        data = self.create_sample_model_data()
        data['supported_ai_problem_types'] = '["invalid_enum_value"]'  # Invalid enum
        
        with pytest.raises(ValueError):
            AIModelSpecification(**data)
    
    def test_mixed_enum_and_string_input(self):
        """Test handling mixed enum and string inputs."""
        data = self.create_sample_model_data()
        # Mix of enum objects and strings
        data['supported_ai_problem_types'] = [AIProblemType.GENERATION, 'qa']
        data['ai_algorithms'] = ['transformer']  # String input
        
        model = AIModelSpecification(**data)
        assert len(model.supported_ai_problem_types) == 2
        assert model.supported_ai_problem_types[0] == AIProblemType.GENERATION
        assert model.supported_ai_problem_types[1] == AIProblemType.QA
        assert model.ai_algorithms is not None
        assert len(model.ai_algorithms) == 1
        assert model.ai_algorithms[0] == AIAlgorithm.TRANSFORMER


class TestAllAIProblemTypes:
    """Test all AIProblemType enum values for serialization."""
    
    @pytest.mark.parametrize("problem_type", [
        AIProblemType.REGRESSION,
        AIProblemType.CLASSIFICATION, 
        AIProblemType.PREDICTION,
        AIProblemType.RANKING,
        AIProblemType.CLUSTERING,
        AIProblemType.ANOMALY_DETECTION,
        AIProblemType.DIMENSIONALITY_REDUCTION,
        AIProblemType.GENERATION,
        AIProblemType.OBJECT_DETECTION,
        AIProblemType.TRANSLATION,
        AIProblemType.SUMMARIZATION,
        AIProblemType.QA,
        AIProblemType.RL_CONTROL
    ])
    def test_individual_problem_type_serialization(self, problem_type):
        """Test each AIProblemType enum value individually."""
        data = {
            'model_spec_id': f'test_{problem_type.value}',
            'model_spec_name': f'Test {problem_type.value} Model',
            'model_spec_display_name': f'Test {problem_type.value} Model Display',
            'pulse_status': ObjectOverallStatus.ACTIVE,
            'model_generalization_level': 'specialized',
            'model_source': 'internal',
            'model_author': 'Test Author',
            'model_provider_organization': 'Test Org',
            'learning_paradigm': 'supervised',
            'supported_ai_problem_types': [problem_type],
            'ai_algorithms': [AIAlgorithm.LINEAR_REGRESSION],
            'ai_architecture_structure': AIArchitectureStructure.SINGLE,
            'created_by': 'test_user',
            'updated_by': 'test_user'
        }
        
        # Test normal creation
        model = AIModelSpecification(**data)
        assert model.supported_ai_problem_types[0] == problem_type
        
        # Test BigQuery round trip
        serialized = make_json_serializable(model.model_dump())
        bq_data = serialized.copy()
        bq_data['supported_ai_problem_types'] = json.dumps(serialized['supported_ai_problem_types'])
        if serialized.get('ai_algorithms') is not None:
            bq_data['ai_algorithms'] = json.dumps(serialized['ai_algorithms'])
        
        reconstructed = AIModelSpecification(**bq_data)
        assert reconstructed.supported_ai_problem_types[0] == problem_type


class TestAllAIAlgorithms:
    """Test key AIAlgorithm enum values for serialization."""
    
    @pytest.mark.parametrize("algorithm", [
        AIAlgorithm.LINEAR_REGRESSION,
        AIAlgorithm.LOGISTIC_REGRESSION,
        AIAlgorithm.RANDOM_FOREST,
        AIAlgorithm.XGBOOST,
        AIAlgorithm.TRANSFORMER,
        AIAlgorithm.CNN,
        AIAlgorithm.LSTM,
        AIAlgorithm.KMEANS,
        AIAlgorithm.PCA,
        AIAlgorithm.ARIMA
    ])
    def test_individual_algorithm_serialization(self, algorithm):
        """Test key AIAlgorithm enum values individually."""
        data = {
            'model_spec_id': f'test_{algorithm.value}',
            'model_spec_name': f'Test {algorithm.value} Model',
            'model_spec_display_name': f'Test {algorithm.value} Model Display',
            'pulse_status': ObjectOverallStatus.ACTIVE,
            'model_generalization_level': 'specialized',
            'model_source': 'internal',
            'model_author': 'Test Author',
            'model_provider_organization': 'Test Org',
            'learning_paradigm': 'supervised',
            'supported_ai_problem_types': [AIProblemType.CLASSIFICATION],
            'ai_algorithms': [algorithm],
            'ai_architecture_structure': AIArchitectureStructure.SINGLE,
            'created_by': 'test_user',
            'updated_by': 'test_user'
        }
        
        # Test normal creation
        model = AIModelSpecification(**data)
        assert model.ai_algorithms is not None
        assert model.ai_algorithms[0] == algorithm
        
        # Test BigQuery round trip
        serialized = make_json_serializable(model.model_dump())
        bq_data = serialized.copy()
        bq_data['supported_ai_problem_types'] = json.dumps(serialized['supported_ai_problem_types'])
        bq_data['ai_algorithms'] = json.dumps(serialized['ai_algorithms'])
        
        reconstructed = AIModelSpecification(**bq_data)
        assert reconstructed.ai_algorithms is not None
        assert reconstructed.ai_algorithms[0] == algorithm


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
