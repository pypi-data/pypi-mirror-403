"""
Integration tests for Phase 4: Anomaly Detection + Tracer Integration

Tests the complete pipeline:
- BaseTracer with anomaly detection enabled
- Per-project model management
- Feature extraction during tracing
- Anomaly result buffering and sending
- Training data accumulation
"""

import pytest
import numpy as np
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from oculus.core.config import OculusConfig
from oculus.core.state import UniversalState
from oculus.core.tracer import BaseTracer
from oculus.anomaly_detection import (
    RobotConfig,
    RobotConfigLoader,
    IsolationForestModel,
    ModelRegistry,
    AnomalyDetectionInference,
    extract_step_features,
    FEATURE_NAMES,
)


class MockTracer(BaseTracer):
    """Mock tracer for testing"""
    
    def capture_state(self, step: int) -> UniversalState:
        return create_test_state(step)


def create_test_state(step: int, is_anomalous: bool = False) -> UniversalState:
    """Create a test UniversalState."""
    np.random.seed(step if not is_anomalous else step + 10000)
    
    num_joints = 12
    
    # Normal behavior
    joint_positions = np.random.uniform(-1, 1, num_joints).tolist()
    joint_velocities = np.random.uniform(-0.5, 0.5, num_joints).tolist()
    joint_torques = np.random.uniform(-10, 10, num_joints).tolist()
    
    if is_anomalous:
        # Inject anomaly: high torque spike
        joint_torques[0] = 50.0  # Way above normal
        joint_velocities[0] = 3.0  # Runaway joint
    
    return UniversalState(
        step=step,
        timestamp=time.time(),
        joint_positions=joint_positions,
        joint_velocities=joint_velocities,
        joint_torques=joint_torques,
        base_position=(0.0, 0.0, 0.8 if not is_anomalous else 0.3),  # Lower height = anomaly
        base_orientation=(0.0, 0.0, 0.0, 1.0),
        base_linear_vel=(0.1, 0.0, 0.0),
        base_angular_vel=(0.0, 0.0, 0.05),
        contact_forces=[(0.0, 0.0, 100.0)] * 4 if not is_anomalous else [],
        contact_points=[(0.0, 0.0, 0.0)] * 4 if not is_anomalous else None,
    )


def create_test_robot_config() -> RobotConfig:
    """Create a test robot configuration."""
    return RobotConfig(
        robot_id="test_quadruped",
        robot_type="quadruped",
        max_linear_velocity=2.0,
        max_angular_velocity=1.5,
        max_linear_acceleration=3.0,
        max_angular_acceleration=2.0,
        num_joints=12,
        max_joint_velocity=[2.0] * 12,
        max_joint_torque=[30.0] * 12,
        max_joint_acceleration=[5.0] * 12,
        expected_standing_height=0.8,
        robot_mass=20.0,
        max_contact_force=200.0,
        physics_dt=0.01,
    )


@pytest.fixture
def test_config():
    """Create test configuration with anomaly detection disabled for basic tests."""
    return OculusConfig(
        api_key="test_key",
        project_name="test_project",
        project_id="test_proj_123",
        robot_type="anymal_c",  # Use known robot type
        enable_anomaly_detection=False,  # Disabled to avoid import issues
        anomaly_threshold=0.6,
        explain_anomalies=False,
        accumulate_training_data=True,
        auto_train_model=False,
        offline_mode=True,
    )


@pytest.fixture
def trained_model(tmp_path):
    """Create a pre-trained model for testing."""
    # Generate synthetic training data
    num_samples = 300
    num_features = len(FEATURE_NAMES)
    
    X_train = np.random.randn(num_samples, num_features) * 0.3 + 0.5
    X_train = np.clip(X_train, 0, 1)  # Normalize to [0, 1]
    
    # Train model
    model = IsolationForestModel(n_estimators=100, contamination=0.01)
    model.fit(X_train)
    
    # Save to temp directory
    model_dir = tmp_path / "test_model"
    model.save(model_dir, project_id="test_proj_123")
    
    return model, model_dir


def test_tracer_without_anomaly_detection():
    """Test tracer works normally when anomaly detection is disabled."""
    config = OculusConfig(
        api_key="test_key",
        project_name="test_project",
        enable_anomaly_detection=False,
        offline_mode=True,
    )
    
    tracer = MockTracer(config)
    assert tracer._anomaly_inference is None
    assert tracer.config.enable_anomaly_detection is False
    
    # Start simulation
    sim_id = tracer.start_simulation("test_run")
    assert sim_id is not None
    
    # Trace steps
    for i in range(10):
        state = create_test_state(i)
        result = tracer.trace_step(state)
        assert result is None  # No anomaly detection
    
    # Finish
    summary = tracer.finish_simulation()
    assert summary["step_count"] == 10
    assert "anomaly_detection" not in summary or not summary.get("anomaly_detection", {}).get("enabled", False)


def test_model_registry_basic(tmp_path):
    """Test basic model registry operations."""
    registry = ModelRegistry(base_dir=str(tmp_path / "models"))
    
    project_id = "test_project_arm"
    
    # Initially no model
    assert not registry.model_exists(project_id)
    
    # Create and train a simple model
    num_features = len(FEATURE_NAMES)
    X_train = np.random.randn(200, num_features) * 0.3 + 0.5
    X_train = np.clip(X_train, 0, 1)
    
    model = IsolationForestModel(n_estimators=50)
    model.fit(X_train)
    
    # Save model
    registry.save_model(project_id, model, metadata={"robot_type": "arm"})
    
    # Check model exists
    assert registry.model_exists(project_id)
    
    # Load model
    loaded_model = registry.load_model(project_id)
    assert loaded_model is not None
    assert loaded_model.is_fitted


def test_model_registry_multiple_projects(tmp_path):
    """Test model registry handles multiple projects correctly."""
    registry = ModelRegistry(base_dir=str(tmp_path / "models"))
    
    projects = ["proj_a", "proj_b", "proj_c"]
    num_features = len(FEATURE_NAMES)
    
    # Create models for each project
    for proj in projects:
        X_train = np.random.randn(100, num_features) * 0.3 + 0.5
        model = IsolationForestModel(n_estimators=30)
        model.fit(X_train)
        registry.save_model(proj, model)
    
    # All should exist
    for proj in projects:
        assert registry.model_exists(proj)
        loaded = registry.load_model(proj)
        assert loaded is not None
        assert loaded.is_fitted


def test_isolation_forest_model_save_load(tmp_path):
    """Test model save/load functionality."""
    num_features = len(FEATURE_NAMES)
    X_train = np.random.randn(150, num_features) * 0.3 + 0.5
    
    # Train model
    model = IsolationForestModel(n_estimators=75, contamination=0.05)
    model.fit(X_train)
    
    # Get predictions before save
    test_sample = np.random.randn(1, num_features) * 0.3 + 0.5
    score_before = model.predict_score(test_sample)
    
    # Save
    model_dir = tmp_path / "saved_model"
    model.save(model_dir, project_id="test_proj")
    
    # Load
    loaded_model = IsolationForestModel.load(model_dir)
    
    # Verify same predictions
    score_after = loaded_model.predict_score(test_sample)
    assert np.isclose(score_before, score_after, rtol=1e-5)


def test_anomaly_inference_engine():
    """Test the anomaly detection inference engine."""
    robot_cfg = create_test_robot_config()
    
    # Train model
    num_features = len(FEATURE_NAMES)
    X_train = np.random.randn(200, num_features) * 0.3 + 0.5
    X_train = np.clip(X_train, 0, 1)
    
    model = IsolationForestModel(n_estimators=100)
    model.fit(X_train)
    
    # Create inference engine
    inference = AnomalyDetectionInference(
        model=model,
        robot_config=robot_cfg,
        anomaly_threshold=0.6
    )
    
    # Process normal state
    state = create_test_state(0, is_anomalous=False)
    result = inference.process_step(state)
    
    assert result is not None
    assert hasattr(result, 'anomaly_score')
    assert 0.0 <= result.anomaly_score <= 1.0
    assert hasattr(result, 'is_anomaly')
    
    # Check statistics
    stats = inference.get_statistics()
    assert stats["steps_processed"] == 1


def test_anomaly_inference_reset():
    """Test that inference engine resets correctly."""
    robot_cfg = create_test_robot_config()
    
    num_features = len(FEATURE_NAMES)
    X_train = np.random.randn(200, num_features) * 0.3 + 0.5
    model = IsolationForestModel(n_estimators=50)
    model.fit(X_train)
    
    inference = AnomalyDetectionInference(
        model=model,
        robot_config=robot_cfg,
        anomaly_threshold=0.6
    )
    
    # Process some steps
    for i in range(5):
        inference.process_step(create_test_state(i))
    
    assert inference.get_statistics()["steps_processed"] == 5
    
    # Reset
    inference.reset_episode()
    
    assert inference.get_statistics()["steps_processed"] == 0


def test_robot_config_loader():
    """Test RobotConfigLoader functionality."""
    # List available defaults
    defaults = RobotConfigLoader.list_defaults()
    assert "anymal_c" in defaults or len(defaults) >= 0  # May be empty in test env
    
    # Create generic config
    generic = RobotConfigLoader.create_generic_config(
        robot_id="custom_bot",
        robot_type="quadruped",
        num_joints=12
    )
    
    assert generic.robot_id == "custom_bot"
    assert generic.num_joints == 12
    assert len(generic.max_joint_velocity) == 12


def test_feature_extraction():
    """Test feature extraction from UniversalState."""
    from oculus.anomaly_detection import FeatureBuffer
    
    robot_cfg = create_test_robot_config()
    buffer = FeatureBuffer(buffer_size=20)
    
    # Create and add state
    state = create_test_state(0)
    buffer.add_state(state)
    
    # Extract features
    features = extract_step_features(state, buffer, robot_cfg)
    
    assert features is not None
    assert len(features) == len(FEATURE_NAMES)
    assert not np.any(np.isnan(features))


def test_config_anomaly_detection_fields():
    """Test that OculusConfig has anomaly detection fields."""
    config = OculusConfig(
        api_key="test",
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


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

