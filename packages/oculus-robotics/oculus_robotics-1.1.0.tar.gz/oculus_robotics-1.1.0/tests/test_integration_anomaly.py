"""
Integration tests for Phase 4: Anomaly Detection Pipeline Integration

Tests the integration between BaseTracer and anomaly detection components.
"""

import pytest
import numpy as np
import tempfile
import shutil
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import core components
from oculus.core.state import UniversalState
from oculus.core.config import OculusConfig
from oculus.core.tracer import BaseTracer

# Import anomaly detection components
from oculus.anomaly_detection import (
    RobotConfig,
    RobotConfigLoader,
    IsolationForestModel,
    AnomalyDetectionInference,
    AnomalyDetectionDatasetBuilder,
    FeatureBuffer,
    extract_step_features,
    FEATURE_NAMES,
    train_model,
)
from oculus.anomaly_detection.explanations import (
    FEATURE_EXPLANATIONS,
    get_human_explanation,
    format_anomaly_explanation,
    get_feature_description,
)
from oculus.anomaly_detection.model_registry import (
    ModelRegistry,
    get_global_registry,
    MIN_EPISODES_FOR_TRAINING,
    MIN_SAMPLES_FOR_TRAINING,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def sample_state():
    """Create a sample UniversalState for testing."""
    return UniversalState(
        step=1,
        timestamp=time.time(),
        joint_positions=[0.1, 0.2, 0.3, -0.1, -0.2, -0.3, 0.0, 0.1, 0.2, -0.1, -0.2, -0.3],
        joint_velocities=[0.01, 0.02, 0.03, -0.01, -0.02, -0.03, 0.0, 0.01, 0.02, -0.01, -0.02, -0.03],
        joint_torques=[1.0, 2.0, 3.0, -1.0, -2.0, -3.0, 0.5, 1.5, 2.5, -0.5, -1.5, -2.5],
        base_position=(0.0, 0.0, 0.5),
        base_orientation=(0.0, 0.0, 0.0, 1.0),
        base_linear_vel=(0.1, 0.0, 0.0),
        base_angular_vel=(0.0, 0.0, 0.01),
        contact_forces=[(0.0, 0.0, 50.0), (0.0, 0.0, 50.0)],
        contact_points=[(0.1, 0.1, 0.0), (-0.1, -0.1, 0.0)],
    )


@pytest.fixture
def robot_config():
    """Create a sample robot configuration."""
    return RobotConfig(
        robot_id="test_robot",
        robot_type="quadruped",
        max_linear_velocity=2.0,
        max_angular_velocity=3.0,
        max_linear_acceleration=5.0,
        max_angular_acceleration=10.0,
        num_joints=12,
        max_joint_velocity=[5.0] * 12,
        max_joint_torque=[50.0] * 12,
        max_joint_acceleration=[100.0] * 12,
        expected_standing_height=0.5,
        robot_mass=30.0,
        max_contact_force=500.0,
        physics_dt=0.01,
    )


@pytest.fixture
def temp_model_dir():
    """Create a temporary directory for model storage."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def synthetic_features(robot_config):
    """Generate synthetic feature data for training."""
    np.random.seed(42)
    n_samples = 200
    n_features = len(FEATURE_NAMES)
    
    # Generate mostly normal data with some variance
    features = np.random.randn(n_samples, n_features) * 0.2 + 0.5
    features = np.clip(features, 0, 1)
    
    return features


@pytest.fixture
def trained_model(synthetic_features, temp_model_dir):
    """Create a trained model for testing."""
    model = IsolationForestModel(
        n_estimators=50,  # Fewer trees for faster tests
        contamination=0.01,
        random_state=42
    )
    model.fit(synthetic_features)
    model.save(temp_model_dir)
    return model


# =============================================================================
# Test: Feature Explanation Mapping
# =============================================================================

class TestFeatureExplanations:
    """Tests for human-readable feature explanations."""
    
    def test_all_features_have_explanations(self):
        """Verify all 40 features have human-readable explanations."""
        for feature_name in FEATURE_NAMES:
            assert feature_name in FEATURE_EXPLANATIONS, \
                f"Feature '{feature_name}' missing from FEATURE_EXPLANATIONS"
    
    def test_explanation_structure(self):
        """Verify explanation dict has required keys."""
        required_keys = {"short", "anomaly_high", "anomaly_low"}
        
        for feature_name, explanation in FEATURE_EXPLANATIONS.items():
            for key in required_keys:
                assert key in explanation, \
                    f"Feature '{feature_name}' missing key '{key}'"
    
    def test_get_human_explanation_high_anomaly(self):
        """Test explanation for high anomaly contribution."""
        explanation = get_human_explanation(
            feature_name="joint_torque_spike",
            shap_value=0.25,  # Positive = pushes toward anomaly
            feature_value=0.9   # High value
        )
        
        assert isinstance(explanation, str)
        assert len(explanation) > 0
        assert "spike" in explanation.lower() or "torque" in explanation.lower()
    
    def test_get_human_explanation_low_anomaly(self):
        """Test explanation for low value causing anomaly."""
        explanation = get_human_explanation(
            feature_name="total_contact_force_magnitude",
            shap_value=0.2,   # Positive = anomaly
            feature_value=0.1  # Low value
        )
        
        assert isinstance(explanation, str)
        assert "contact" in explanation.lower() or "loss" in explanation.lower()
    
    def test_get_human_explanation_normal(self):
        """Test explanation for normal contribution."""
        explanation = get_human_explanation(
            feature_name="base_linear_velocity_magnitude",
            shap_value=-0.1,  # Negative = argues for normalcy
            feature_value=0.5
        )
        
        assert isinstance(explanation, str)
        assert "normal" in explanation.lower() or "range" in explanation.lower()
    
    def test_format_anomaly_explanation(self):
        """Test full anomaly explanation formatting."""
        top_features = [
            {"feature_name": "joint_torque_spike", "feature_value": 0.9, "shap_value": 0.25, "rank": 1},
            {"feature_name": "contact_stability", "feature_value": 0.2, "shap_value": 0.15, "rank": 2},
            {"feature_name": "base_height_normalized", "feature_value": 0.3, "shap_value": 0.10, "rank": 3},
        ]
        
        result = format_anomaly_explanation(
            top_features=top_features,
            anomaly_score=0.75,
            threshold=0.6
        )
        
        assert result["is_anomaly"] is True
        assert result["severity"] == "warning"
        assert result["primary_cause"] is not None
        assert result["primary_feature"] == "joint_torque_spike"
        assert result["summary"] is not None
        assert len(result["summary"]) > 0
    
    def test_format_explanation_normal_behavior(self):
        """Test explanation for normal behavior."""
        top_features = [
            {"feature_name": "joint_velocity_rms", "feature_value": 0.5, "shap_value": 0.05, "rank": 1},
        ]
        
        result = format_anomaly_explanation(
            top_features=top_features,
            anomaly_score=0.3,
            threshold=0.6
        )
        
        assert result["is_anomaly"] is False
        assert result["severity"] == "normal"


# =============================================================================
# Test: Model Registry
# =============================================================================

class TestModelRegistry:
    """Tests for per-project model management."""
    
    def test_registry_initialization(self, temp_model_dir):
        """Test registry initializes correctly."""
        registry = ModelRegistry(base_dir=temp_model_dir)
        
        assert registry.base_dir.exists()
        assert len(registry.list_projects()) == 0
    
    def test_model_save_and_load(self, temp_model_dir, trained_model):
        """Test saving and loading models."""
        registry = ModelRegistry(base_dir=temp_model_dir)
        project_id = "test_project_123"
        
        # Save model
        save_path = registry.save_model(project_id, trained_model)
        
        assert save_path.exists()
        assert registry.model_exists(project_id)
        
        # Load model
        loaded_model = registry.load_model(project_id)
        
        assert loaded_model is not None
        assert loaded_model.is_fitted
        assert loaded_model.n_features_in_ == trained_model.n_features_in_
    
    def test_model_caching(self, temp_model_dir, trained_model):
        """Test that loaded models are cached."""
        registry = ModelRegistry(base_dir=temp_model_dir)
        project_id = "cached_project"
        
        registry.save_model(project_id, trained_model)
        
        # First load
        model1 = registry.load_model(project_id)
        # Second load should return cached
        model2 = registry.load_model(project_id)
        
        assert model1 is model2  # Same object
    
    def test_episode_data_accumulation(self, temp_model_dir, synthetic_features):
        """Test episode data accumulation for training."""
        registry = ModelRegistry(base_dir=temp_model_dir)
        project_id = "accumulation_test"
        
        # Add episodes
        for i in range(5):
            episode_features = synthetic_features[i*20:(i+1)*20]
            status = registry.add_episode_data(
                project_id=project_id,
                features=episode_features,
                episode_id=f"episode_{i}",
                outcome="success"
            )
        
        assert status["episodes_collected"] == 5
        assert status["total_samples"] == 100
        assert not status["ready_for_training"]  # Need more data
    
    def test_training_trigger_threshold(self, temp_model_dir, synthetic_features):
        """Test auto-training triggers at threshold."""
        registry = ModelRegistry(base_dir=temp_model_dir)
        project_id = "trigger_test"
        
        # Add enough data to trigger training
        n_episodes = MIN_EPISODES_FOR_TRAINING + 2
        samples_per_episode = (MIN_SAMPLES_FOR_TRAINING // n_episodes) + 10
        
        for i in range(n_episodes):
            start_idx = (i * samples_per_episode) % len(synthetic_features)
            episode_features = synthetic_features[start_idx:start_idx + samples_per_episode]
            if len(episode_features) < samples_per_episode:
                # Wrap around
                episode_features = np.vstack([
                    episode_features,
                    synthetic_features[:samples_per_episode - len(episode_features)]
                ])
            
            status = registry.add_episode_data(
                project_id=project_id,
                features=episode_features,
                episode_id=f"episode_{i}",
                outcome="success"
            )
        
        assert status["ready_for_training"]
    
    def test_model_deletion(self, temp_model_dir, trained_model):
        """Test model deletion."""
        registry = ModelRegistry(base_dir=temp_model_dir)
        project_id = "delete_test"
        
        registry.save_model(project_id, trained_model)
        assert registry.model_exists(project_id)
        
        deleted = registry.delete_model(project_id)
        assert deleted
        assert not registry.model_exists(project_id)
    
    def test_list_projects(self, temp_model_dir, trained_model):
        """Test listing projects with models."""
        registry = ModelRegistry(base_dir=temp_model_dir)
        
        registry.save_model("project_a", trained_model)
        registry.save_model("project_b", trained_model)
        
        projects = registry.list_projects()
        
        assert len(projects) == 2
        assert "project_a" in projects
        assert "project_b" in projects


# =============================================================================
# Test: Anomaly Detection Inference Integration
# =============================================================================

class TestAnomalyDetectionInference:
    """Tests for inference engine with tracer integration."""
    
    def test_inference_initialization(self, trained_model, robot_config):
        """Test inference engine initializes correctly."""
        inference = AnomalyDetectionInference(
            model=trained_model,
            robot_config=robot_config,
            anomaly_threshold=0.6
        )
        
        assert inference.model is trained_model
        assert inference.anomaly_threshold == 0.6
        assert inference.steps_processed == 0
    
    def test_process_step(self, trained_model, robot_config, sample_state):
        """Test processing a single step."""
        inference = AnomalyDetectionInference(
            model=trained_model,
            robot_config=robot_config,
            anomaly_threshold=0.6
        )
        
        result = inference.process_step(sample_state)
        
        assert hasattr(result, 'anomaly_score')
        assert 0.0 <= result.anomaly_score <= 1.0
        assert isinstance(result.is_anomaly, bool)
        assert inference.steps_processed == 1
    
    def test_episode_reset(self, trained_model, robot_config, sample_state):
        """Test episode boundary reset."""
        inference = AnomalyDetectionInference(
            model=trained_model,
            robot_config=robot_config,
            anomaly_threshold=0.6
        )
        
        # Process some steps
        for _ in range(5):
            inference.process_step(sample_state)
        
        assert inference.steps_processed == 5
        
        # Reset
        inference.reset_episode()
        
        assert inference.steps_processed == 0
        assert inference.anomalies_detected == 0
    
    def test_statistics(self, trained_model, robot_config, sample_state):
        """Test inference statistics."""
        inference = AnomalyDetectionInference(
            model=trained_model,
            robot_config=robot_config,
            anomaly_threshold=0.6
        )
        
        for _ in range(10):
            inference.process_step(sample_state)
        
        stats = inference.get_statistics()
        
        assert "steps_processed" in stats
        assert "anomalies_detected" in stats
        assert "anomaly_rate" in stats
        assert stats["steps_processed"] == 10


# =============================================================================
# Test: OculusConfig Anomaly Detection Fields
# =============================================================================

class TestOculusConfigAnomalyDetection:
    """Tests for anomaly detection configuration."""
    
    def test_default_config_anomaly_disabled(self):
        """Test default config has anomaly detection disabled."""
        config = OculusConfig(api_key="test_key")
        
        assert config.enable_anomaly_detection is False
    
    def test_config_with_anomaly_detection(self):
        """Test config with anomaly detection enabled."""
        config = OculusConfig(
            api_key="test_key",
            enable_anomaly_detection=True,
            anomaly_threshold=0.7,
            explain_anomalies=True,
            accumulate_training_data=True,
            auto_train_model=True
        )
        
        assert config.enable_anomaly_detection is True
        assert config.anomaly_threshold == 0.7
        assert config.explain_anomalies is True
        assert config.accumulate_training_data is True
        assert config.auto_train_model is True
    
    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        config_dict = {
            "api_key": "test_key",
            "enable_anomaly_detection": True,
            "anomaly_threshold": 0.65,
            "project_id": "my_project"
        }
        
        config = OculusConfig.from_dict(config_dict)
        
        assert config.enable_anomaly_detection is True
        assert config.anomaly_threshold == 0.65
        assert config.project_id == "my_project"


# =============================================================================
# Test: BaseTracer Integration (Mocked)
# =============================================================================

class MockTracer(BaseTracer):
    """Mock tracer for testing BaseTracer functionality."""
    
    def capture_state(self, step: int) -> UniversalState:
        """Generate mock state."""
        return UniversalState(
            step=step,
            timestamp=time.time(),
            joint_positions=[0.1] * 12,
            joint_velocities=[0.01] * 12,
            joint_torques=[1.0] * 12,
            base_position=(0.0, 0.0, 0.5),
            base_orientation=(0.0, 0.0, 0.0, 1.0),
            base_linear_vel=(0.1, 0.0, 0.0),
            base_angular_vel=(0.0, 0.0, 0.01),
        )


class TestBaseTracerIntegration:
    """Tests for BaseTracer with anomaly detection integration."""
    
    def test_tracer_without_anomaly_detection(self):
        """Test tracer works without anomaly detection."""
        config = OculusConfig(
            api_key="test_key",
            offline_mode=True,
            enable_anomaly_detection=False
        )
        
        tracer = MockTracer(config)
        
        assert tracer._anomaly_inference is None
    
    @patch('oculus.core.tracer.BaseTracer._init_anomaly_detection')
    def test_tracer_initializes_anomaly_detection(self, mock_init):
        """Test tracer initializes anomaly detection when enabled."""
        config = OculusConfig(
            api_key="test_key",
            offline_mode=True,
            enable_anomaly_detection=True
        )
        
        tracer = MockTracer(config)
        
        mock_init.assert_called_once()
    
    def test_get_anomaly_status_disabled(self):
        """Test anomaly status when disabled."""
        config = OculusConfig(
            api_key="test_key",
            offline_mode=True,
            enable_anomaly_detection=False
        )
        
        tracer = MockTracer(config)
        status = tracer.get_anomaly_status()
        
        assert status["enabled"] is False
    
    def test_trace_step_returns_anomaly_result(self, trained_model, robot_config, temp_model_dir):
        """Test trace_step returns anomaly result when inference available."""
        config = OculusConfig(
            api_key="test_key",
            offline_mode=True,
            enable_anomaly_detection=True,
            anomaly_threshold=0.6
        )
        
        tracer = MockTracer(config)
        
        # Manually set up inference (bypassing model registry)
        tracer._robot_config = robot_config
        tracer._anomaly_inference = AnomalyDetectionInference(
            model=trained_model,
            robot_config=robot_config,
            anomaly_threshold=0.6
        )
        
        # Start simulation
        tracer.start_simulation("test_sim")
        
        # Trace a step
        state = tracer.capture_state(1)
        result = tracer.trace_step(state)
        
        # Should return anomaly result
        assert result is not None
        assert "anomaly_score" in result
        assert "is_anomaly" in result
    
    def test_finish_simulation_summary(self, trained_model, robot_config):
        """Test simulation summary includes anomaly detection info."""
        config = OculusConfig(
            api_key="test_key",
            offline_mode=True,
            enable_anomaly_detection=True,
            accumulate_training_data=False  # Disable to simplify test
        )
        
        tracer = MockTracer(config)
        tracer._robot_config = robot_config
        tracer._anomaly_inference = AnomalyDetectionInference(
            model=trained_model,
            robot_config=robot_config,
            anomaly_threshold=0.6
        )
        
        tracer.start_simulation("test_sim")
        
        # Trace some steps
        for i in range(5):
            state = tracer.capture_state(i)
            tracer.trace_step(state)
        
        # Finish and get summary
        summary = tracer.finish_simulation(outcome="success")
        
        assert "anomaly_detection" in summary
        assert summary["anomaly_detection"]["enabled"] is True
        assert "steps_processed" in summary["anomaly_detection"]
    
    def test_get_project_id(self):
        """Test project ID generation."""
        config = OculusConfig(
            api_key="test_key",
            offline_mode=True,
            project_name="My Test Project",
            robot_type="quadruped"
        )
        
        tracer = MockTracer(config)
        project_id = tracer._get_project_id()
        
        assert "my_test_project" in project_id.lower()
        assert "quadruped" in project_id.lower()
    
    def test_get_project_id_explicit(self):
        """Test explicit project ID takes precedence."""
        config = OculusConfig(
            api_key="test_key",
            offline_mode=True,
            project_name="My Project",
            project_id="custom_project_id"
        )
        
        tracer = MockTracer(config)
        project_id = tracer._get_project_id()
        
        assert project_id == "custom_project_id"


# =============================================================================
# Test: End-to-End Integration
# =============================================================================

class TestEndToEndIntegration:
    """End-to-end integration tests."""
    
    def test_full_pipeline_offline(self, temp_model_dir, synthetic_features, robot_config):
        """Test full pipeline in offline mode."""
        # Setup registry with pre-trained model
        registry = ModelRegistry(base_dir=temp_model_dir)
        project_id = "e2e_test_project"
        
        # Train and save model
        model = IsolationForestModel(n_estimators=50, random_state=42)
        model.fit(synthetic_features)
        registry.save_model(project_id, model)
        
        # Create tracer config pointing to temp registry
        config = OculusConfig(
            api_key="test_key",
            offline_mode=True,
            project_id=project_id,
            robot_type="quadruped",
            enable_anomaly_detection=True,
            anomaly_threshold=0.6,
            accumulate_training_data=False
        )
        
        tracer = MockTracer(config)
        
        # Manually wire up the model (simulating what _init_anomaly_detection does)
        tracer._robot_config = robot_config
        loaded_model = registry.load_model(project_id)
        tracer._anomaly_inference = AnomalyDetectionInference(
            model=loaded_model,
            robot_config=robot_config,
            anomaly_threshold=0.6
        )
        
        # Run simulation
        tracer.start_simulation("E2E Test Simulation")
        
        anomaly_results = []
        for i in range(20):
            state = tracer.capture_state(i)
            result = tracer.trace_step(state)
            if result:
                anomaly_results.append(result)
        
        summary = tracer.finish_simulation(outcome="success")
        
        # Verify results
        assert len(anomaly_results) == 20
        assert all("anomaly_score" in r for r in anomaly_results)
        assert "anomaly_detection" in summary
        assert summary["anomaly_detection"]["steps_processed"] == 20
    
    def test_data_accumulation_workflow(self, temp_model_dir, robot_config):
        """Test workflow when no model exists (data accumulation)."""
        registry = ModelRegistry(base_dir=temp_model_dir)
        project_id = "new_project_no_model"
        
        # Verify no model exists
        assert not registry.model_exists(project_id)
        
        # Simulate multiple episodes
        np.random.seed(42)
        
        for episode in range(3):
            # Generate episode features
            n_steps = 50
            episode_features = np.random.randn(n_steps, len(FEATURE_NAMES)) * 0.2 + 0.5
            episode_features = np.clip(episode_features, 0, 1)
            
            status = registry.add_episode_data(
                project_id=project_id,
                features=episode_features,
                episode_id=f"episode_{episode}",
                outcome="success"
            )
        
        # Check accumulation status
        accum_status = registry.get_accumulation_status(project_id)
        
        assert accum_status["episodes_collected"] == 3
        assert accum_status["total_samples"] == 150
        assert not accum_status["ready_for_training"]  # Need more data


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
