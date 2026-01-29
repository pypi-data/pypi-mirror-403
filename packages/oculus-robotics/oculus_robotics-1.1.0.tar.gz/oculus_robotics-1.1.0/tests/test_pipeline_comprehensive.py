"""
Comprehensive Test Suite for Oculus Anomaly Detection Pipeline

This test suite validates the entire anomaly detection pipeline including:
1. Robot Configuration (config.py)
2. Feature Buffer (feature_buffer.py)
3. Feature Extraction (features.py)
4. Dataset Builder (dataset.py)
5. Isolation Forest Model (model.py)
6. Training Orchestration (trainer.py)
7. Real-Time Inference (inference.py)
8. Model Registry (model_registry.py)
9. SHAP Explainability (explainability.py)

The suite includes robustness tests with:
- Missing data simulation
- Malformed inputs
- Edge cases and boundary conditions
- Real-world failure scenarios

Author: Oculus Testing Framework
Date: January 2026
"""

import pytest
import numpy as np
import tempfile
import shutil
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json

# Import test subjects
from oculus.core.state import UniversalState
from oculus.anomaly_detection.config import RobotConfig, RobotConfigLoader
from oculus.anomaly_detection.feature_buffer import FeatureBuffer
from oculus.anomaly_detection.features import (
    extract_step_features,
    extract_episode_features,
    compute_velocity_features,
    compute_acceleration_features,
    compute_torque_features,
    compute_contact_features,
    compute_smoothness_features,
    compute_stability_features,
    FEATURE_NAMES,
)
from oculus.anomaly_detection.dataset import EpisodeData, AnomalyDetectionDatasetBuilder
from oculus.anomaly_detection.model import IsolationForestModel
from oculus.anomaly_detection.trainer import train_model, quick_train, evaluate_on_labeled_data
from oculus.anomaly_detection.inference import (
    AnomalyDetectionInference,
    AnomalyResult,
    calibrate_threshold,
    batch_inference_on_episode,
)
from oculus.anomaly_detection.model_registry import (
    ModelRegistry,
    MIN_EPISODES_FOR_TRAINING,
    MIN_SAMPLES_FOR_TRAINING,
)
from oculus.anomaly_detection.utils import (
    safe_divide,
    safe_normalize,
    clip_features,
    replace_nan_inf,
    compute_rms,
)


# =============================================================================
# TEST FIXTURES AND HELPERS
# =============================================================================

@pytest.fixture
def sample_robot_config() -> RobotConfig:
    """Create a sample robot configuration for testing."""
    return RobotConfig(
        robot_id="test_robot",
        robot_type="quadruped",
        num_joints=12,
        max_linear_velocity=2.0,
        max_angular_velocity=3.14,
        max_linear_acceleration=5.0,
        max_angular_acceleration=10.0,
        max_joint_velocity=[3.0] * 12,
        max_joint_torque=[100.0] * 12,
        max_joint_acceleration=[10.0] * 12,
        expected_standing_height=0.5,
        robot_mass=50.0,
        max_contact_force=500.0,
        physics_dt=0.01,
    )


def create_valid_state(
    step: int = 0,
    timestamp: float = 0.0,
    num_joints: int = 12,
    include_contacts: bool = True,
    base_position: tuple = (0.0, 0.0, 0.5),
    base_velocity: tuple = (0.1, 0.0, 0.0),
    joint_velocities: Optional[List[float]] = None,
    joint_torques: Optional[List[float]] = None,
) -> UniversalState:
    """Create a valid UniversalState for testing."""
    return UniversalState(
        step=step,
        timestamp=timestamp,
        joint_positions=[0.0] * num_joints,
        joint_velocities=joint_velocities if joint_velocities else [0.1] * num_joints,
        joint_torques=joint_torques if joint_torques else [10.0] * num_joints,
        base_position=base_position,
        base_orientation=(0.0, 0.0, 0.0, 1.0),  # Identity quaternion
        base_linear_vel=base_velocity,
        base_angular_vel=(0.0, 0.0, 0.0),
        contact_forces=[(0.0, 0.0, 50.0), (0.0, 0.0, 50.0), (0.0, 0.0, 50.0), (0.0, 0.0, 50.0)] if include_contacts else None,
        contact_points=[(0.3, 0.2, 0.0), (-0.3, 0.2, 0.0), (0.3, -0.2, 0.0), (-0.3, -0.2, 0.0)] if include_contacts else None,
    )


def create_episode_states(
    num_steps: int = 100,
    num_joints: int = 12,
    include_contacts: bool = True,
    add_noise: bool = True,
) -> List[UniversalState]:
    """Create a sequence of states simulating an episode."""
    states = []
    for i in range(num_steps):
        # Simulate realistic motion with some noise
        noise = np.random.randn(3) * 0.01 if add_noise else np.zeros(3)
        base_pos = (0.0 + i * 0.01 + noise[0], 0.0 + noise[1], 0.5 + noise[2] * 0.01)
        base_vel = (0.1 + noise[0], noise[1] * 0.1, noise[2] * 0.01)
        
        joint_vels = [0.1 + np.random.randn() * 0.1 for _ in range(num_joints)] if add_noise else [0.1] * num_joints
        joint_torques = [10.0 + np.random.randn() * 2.0 for _ in range(num_joints)] if add_noise else [10.0] * num_joints
        
        states.append(create_valid_state(
            step=i,
            timestamp=i * 0.01,
            num_joints=num_joints,
            include_contacts=include_contacts,
            base_position=base_pos,
            base_velocity=base_vel,
            joint_velocities=joint_vels,
            joint_torques=joint_torques,
        ))
    return states


def create_anomalous_states(
    num_steps: int = 100,
    anomaly_start: int = 40,
    anomaly_end: int = 60,
    anomaly_type: str = "torque_spike",
    num_joints: int = 12,
) -> List[UniversalState]:
    """Create an episode with synthetic anomalies injected."""
    states = create_episode_states(num_steps, num_joints)
    
    for i in range(anomaly_start, min(anomaly_end, num_steps)):
        if anomaly_type == "torque_spike":
            # Inject extreme torque values
            states[i] = create_valid_state(
                step=i,
                timestamp=i * 0.01,
                num_joints=num_joints,
                joint_torques=[150.0] * num_joints,  # 1.5x max expected
            )
        elif anomaly_type == "velocity_jump":
            # Inject sudden velocity change
            states[i] = create_valid_state(
                step=i,
                timestamp=i * 0.01,
                num_joints=num_joints,
                base_velocity=(2.0, 1.0, 0.5),  # Sudden high velocity
            )
        elif anomaly_type == "contact_loss":
            # Simulate contact loss (robot falling)
            states[i] = create_valid_state(
                step=i,
                timestamp=i * 0.01,
                num_joints=num_joints,
                include_contacts=False,
                base_position=(0.0, 0.0, 0.3),  # Lower height
            )
        elif anomaly_type == "height_drop":
            # Simulate falling
            height = 0.5 - (i - anomaly_start) * 0.02  # Gradually drop
            states[i] = create_valid_state(
                step=i,
                timestamp=i * 0.01,
                num_joints=num_joints,
                base_position=(0.0, 0.0, max(0.1, height)),
            )
    
    return states


@pytest.fixture
def temp_directory():
    """Create a temporary directory for test file I/O."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)


# =============================================================================
# SECTION 1: ROBOT CONFIGURATION TESTS
# =============================================================================

class TestRobotConfig:
    """Tests for RobotConfig and RobotConfigLoader."""
    
    def test_valid_config_creation(self):
        """Test creating a valid RobotConfig."""
        config = RobotConfig(
            robot_id="test_robot",
            robot_type="quadruped",
            num_joints=12,
            max_linear_velocity=2.0,
            max_angular_velocity=3.14,
            max_linear_acceleration=5.0,
            max_angular_acceleration=10.0,
            max_joint_velocity=[3.0] * 12,
            max_joint_torque=[100.0] * 12,
            max_joint_acceleration=[10.0] * 12,
            expected_standing_height=0.5,
            robot_mass=50.0,
            max_contact_force=500.0,
        )
        assert config.robot_id == "test_robot"
        assert config.num_joints == 12
        assert len(config.max_joint_velocity) == 12
    
    def test_config_validation_joint_mismatch(self):
        """Test that validation fails with mismatched joint arrays."""
        with pytest.raises(ValueError, match="max_joint_velocity length"):
            RobotConfig(
                robot_id="test",
                robot_type="arm",
                num_joints=6,
                max_linear_velocity=1.0,
                max_angular_velocity=1.0,
                max_linear_acceleration=1.0,
                max_angular_acceleration=1.0,
                max_joint_velocity=[1.0] * 8,  # Wrong length
                max_joint_torque=[1.0] * 6,
                max_joint_acceleration=[1.0] * 6,
                expected_standing_height=0.3,
                robot_mass=10.0,
                max_contact_force=100.0,
            )
    
    def test_config_validation_negative_velocity(self):
        """Test that validation fails with negative velocity."""
        with pytest.raises(ValueError, match="max_linear_velocity must be positive"):
            RobotConfig(
                robot_id="test",
                robot_type="arm",
                num_joints=6,
                max_linear_velocity=-1.0,  # Invalid
                max_angular_velocity=1.0,
                max_linear_acceleration=1.0,
                max_angular_acceleration=1.0,
                max_joint_velocity=[1.0] * 6,
                max_joint_torque=[1.0] * 6,
                max_joint_acceleration=[1.0] * 6,
                expected_standing_height=0.3,
                robot_mass=10.0,
                max_contact_force=100.0,
            )
    
    def test_config_save_and_load(self, temp_directory):
        """Test saving and loading RobotConfig."""
        config = RobotConfig(
            robot_id="test_save",
            robot_type="quadruped",
            num_joints=12,
            max_linear_velocity=2.0,
            max_angular_velocity=3.14,
            max_linear_acceleration=5.0,
            max_angular_acceleration=10.0,
            max_joint_velocity=[3.0] * 12,
            max_joint_torque=[100.0] * 12,
            max_joint_acceleration=[10.0] * 12,
            expected_standing_height=0.5,
            robot_mass=50.0,
            max_contact_force=500.0,
        )
        
        save_path = os.path.join(temp_directory, "config.json")
        config.save(save_path)
        
        loaded = RobotConfig.load(save_path)
        assert loaded.robot_id == config.robot_id
        assert loaded.num_joints == config.num_joints
        assert loaded.max_linear_velocity == config.max_linear_velocity
    
    def test_load_default_configs(self):
        """Test loading default robot configurations."""
        available = RobotConfigLoader.list_defaults()
        assert isinstance(available, list)
        
        # Try loading first available config
        if len(available) > 0:
            config = RobotConfigLoader.load_default(available[0])
            assert config is not None
            assert config.num_joints > 0
    
    def test_create_generic_config(self):
        """Test creating generic config for unknown robot."""
        config = RobotConfigLoader.create_generic_config(
            robot_id="unknown_robot",
            robot_type="custom",
            num_joints=8,
        )
        assert config.robot_id == "unknown_robot"
        assert config.num_joints == 8
        assert len(config.max_joint_velocity) == 8


# =============================================================================
# SECTION 2: FEATURE BUFFER TESTS
# =============================================================================

class TestFeatureBuffer:
    """Tests for FeatureBuffer temporal state management."""
    
    def test_buffer_initialization(self):
        """Test buffer initializes correctly."""
        buffer = FeatureBuffer(buffer_size=20)
        assert buffer.buffer_size == 20
        assert buffer.is_empty
        assert not buffer.is_full
        assert len(buffer) == 0
    
    def test_add_and_retrieve_states(self, sample_robot_config):
        """Test adding and retrieving states."""
        buffer = FeatureBuffer(buffer_size=5)
        
        states = [create_valid_state(step=i) for i in range(3)]
        for state in states:
            buffer.add_state(state)
        
        assert len(buffer) == 3
        assert buffer.get_current_state().step == 2
        assert buffer.get_previous_state(1).step == 1
        assert buffer.get_previous_state(2).step == 0
    
    def test_buffer_overflow(self):
        """Test buffer correctly evicts oldest states."""
        buffer = FeatureBuffer(buffer_size=3)
        
        for i in range(5):
            buffer.add_state(create_valid_state(step=i))
        
        assert len(buffer) == 3
        assert buffer.is_full
        # Oldest should be step 2 (0, 1 evicted)
        assert buffer.get_history_window(3)[0].step == 2
    
    def test_get_previous_state_boundary(self):
        """Test getting state beyond buffer capacity returns None."""
        buffer = FeatureBuffer(buffer_size=5)
        buffer.add_state(create_valid_state(step=0))
        buffer.add_state(create_valid_state(step=1))
        
        assert buffer.get_previous_state(1) is not None
        assert buffer.get_previous_state(5) is None
    
    def test_get_previous_state_invalid_offset(self):
        """Test that offset < 1 raises an error."""
        buffer = FeatureBuffer(buffer_size=5)
        buffer.add_state(create_valid_state())
        
        with pytest.raises(ValueError, match="Offset must be >= 1"):
            buffer.get_previous_state(0)
    
    def test_buffer_reset(self):
        """Test buffer reset clears all data."""
        buffer = FeatureBuffer(buffer_size=10)
        for i in range(5):
            buffer.add_state(create_valid_state(step=i))
        
        buffer.reset()
        assert buffer.is_empty
        assert buffer.step_count == 0
    
    def test_get_history_window(self):
        """Test retrieving history window."""
        buffer = FeatureBuffer(buffer_size=10)
        for i in range(8):
            buffer.add_state(create_valid_state(step=i))
        
        window = buffer.get_history_window(5)
        assert len(window) == 5
        # Window should be the last 5 states (steps 3-7)
        assert window[0].step == 3
        assert window[-1].step == 7
    
    def test_has_history_check(self):
        """Test has_history correctly reports availability."""
        buffer = FeatureBuffer(buffer_size=10)
        
        assert not buffer.has_history(1)
        buffer.add_state(create_valid_state())
        assert buffer.has_history(1)
        assert not buffer.has_history(2)


# =============================================================================
# SECTION 3: FEATURE EXTRACTION TESTS
# =============================================================================

class TestFeatureExtraction:
    """Tests for feature extraction functions."""
    
    def test_extract_step_features_shape(self, sample_robot_config):
        """Test that feature extraction produces correct shape."""
        buffer = FeatureBuffer(buffer_size=20)
        state = create_valid_state()
        buffer.add_state(state)
        
        features = extract_step_features(state, buffer, sample_robot_config)
        
        assert features.shape == (40,)
        assert len(FEATURE_NAMES) == 40
    
    def test_extract_step_features_no_nan(self, sample_robot_config):
        """Test that features don't contain NaN or Inf."""
        buffer = FeatureBuffer(buffer_size=20)
        states = create_episode_states(num_steps=10)
        
        for state in states:
            buffer.add_state(state)
            features = extract_step_features(state, buffer, sample_robot_config)
            
            assert not np.any(np.isnan(features)), "Features contain NaN"
            assert not np.any(np.isinf(features)), "Features contain Inf"
    
    def test_extract_step_features_bounded(self, sample_robot_config):
        """Test that features are clipped to expected bounds."""
        buffer = FeatureBuffer(buffer_size=20)
        state = create_valid_state()
        buffer.add_state(state)
        
        features = extract_step_features(state, buffer, sample_robot_config)
        
        assert np.all(features >= -10.0), f"Features below -10: {features[features < -10]}"
        assert np.all(features <= 10.0), f"Features above 10: {features[features > 10]}"
    
    def test_extract_episode_features_shape(self, sample_robot_config):
        """Test episode feature extraction produces correct shape."""
        states = create_episode_states(num_steps=50)
        features = extract_episode_features(states, sample_robot_config)
        
        assert features.shape == (50, 40)
    
    def test_velocity_features_category(self, sample_robot_config):
        """Test velocity feature computation."""
        state = create_valid_state(base_velocity=(1.0, 0.0, 0.0))
        prev_state = create_valid_state(base_velocity=(0.5, 0.0, 0.0))
        
        features = compute_velocity_features(state, prev_state, sample_robot_config)
        
        assert features.shape == (6,)
        # Base velocity magnitude should be non-zero
        assert features[0] > 0
    
    def test_acceleration_features_requires_history(self, sample_robot_config):
        """Test that acceleration features handle missing history."""
        state = create_valid_state()
        
        # No previous state
        features = compute_acceleration_features(state, None, None, sample_robot_config)
        assert np.all(features == 0), "Should be zeros without history"
    
    def test_contact_features_handles_missing_data(self, sample_robot_config):
        """Test contact features handle missing contact data."""
        state = create_valid_state(include_contacts=False)
        
        features = compute_contact_features(state, sample_robot_config)
        
        assert features.shape == (8,)
        assert np.all(features == 0), "Should be zeros without contact data"
    
    def test_torque_features_empty_joints(self, sample_robot_config):
        """Test torque features handle empty joint data."""
        state = UniversalState(
            step=0,
            timestamp=0.0,
            joint_positions=[],
            joint_velocities=[],
            joint_torques=[],  # Empty
            base_position=(0.0, 0.0, 0.5),
            base_orientation=(0.0, 0.0, 0.0, 1.0),
            base_linear_vel=(0.0, 0.0, 0.0),
            base_angular_vel=(0.0, 0.0, 0.0),
        )
        
        features = compute_torque_features(state, None, sample_robot_config)
        assert features.shape == (8,)
        assert np.all(features == 0)


# =============================================================================
# SECTION 4: ROBUSTNESS TESTS - DATA QUALITY ISSUES
# =============================================================================

class TestRobustnessDataQuality:
    """Tests for handling data quality issues and malformed inputs."""
    
    def test_feature_extraction_with_nan_input(self, sample_robot_config):
        """Test feature extraction handles NaN values in state."""
        buffer = FeatureBuffer(buffer_size=5)
        
        # Create state with NaN values
        state = UniversalState(
            step=0,
            timestamp=0.0,
            joint_positions=[float('nan')] * 12,
            joint_velocities=[float('nan')] * 12,
            joint_torques=[float('nan')] * 12,
            base_position=(float('nan'), 0.0, 0.5),
            base_orientation=(0.0, 0.0, 0.0, 1.0),
            base_linear_vel=(0.0, float('nan'), 0.0),
            base_angular_vel=(0.0, 0.0, 0.0),
        )
        
        buffer.add_state(state)
        features = extract_step_features(state, buffer, sample_robot_config)
        
        # Should not crash and should replace NaN with 0
        assert not np.any(np.isnan(features))
        assert not np.any(np.isinf(features))
    
    def test_feature_extraction_with_inf_input(self, sample_robot_config):
        """Test feature extraction handles Inf values in state."""
        buffer = FeatureBuffer(buffer_size=5)
        
        state = UniversalState(
            step=0,
            timestamp=0.0,
            joint_positions=[0.0] * 12,
            joint_velocities=[float('inf')] * 12,  # Inf velocities
            joint_torques=[10.0] * 12,
            base_position=(0.0, 0.0, 0.5),
            base_orientation=(0.0, 0.0, 0.0, 1.0),
            base_linear_vel=(0.0, 0.0, 0.0),
            base_angular_vel=(0.0, 0.0, 0.0),
        )
        
        buffer.add_state(state)
        features = extract_step_features(state, buffer, sample_robot_config)
        
        assert not np.any(np.isinf(features))
    
    def test_feature_extraction_extreme_values(self, sample_robot_config):
        """Test feature extraction handles extreme but valid values."""
        buffer = FeatureBuffer(buffer_size=5)
        
        # Create state with extreme values
        state = UniversalState(
            step=0,
            timestamp=0.0,
            joint_positions=[0.0] * 12,
            joint_velocities=[100.0] * 12,  # Way above max
            joint_torques=[1000.0] * 12,  # Way above max
            base_position=(1000.0, 1000.0, 100.0),
            base_orientation=(0.0, 0.0, 0.0, 1.0),
            base_linear_vel=(50.0, 50.0, 50.0),
            base_angular_vel=(100.0, 100.0, 100.0),
        )
        
        buffer.add_state(state)
        features = extract_step_features(state, buffer, sample_robot_config)
        
        # Features should be clipped
        assert np.all(features >= -10.0) and np.all(features <= 10.0)
    
    def test_randomly_dropped_features(self, sample_robot_config):
        """Test robustness when features randomly become unavailable."""
        buffer = FeatureBuffer(buffer_size=20)
        
        for i in range(50):
            # Randomly drop contact data
            include_contacts = np.random.random() > 0.3
            
            # Randomly zero out some joint data
            num_joints = 12
            joint_vels = [0.1] * num_joints
            if np.random.random() > 0.7:
                # Zero out random joints
                zero_indices = np.random.choice(num_joints, size=np.random.randint(1, 4), replace=False)
                for idx in zero_indices:
                    joint_vels[idx] = 0.0
            
            state = create_valid_state(
                step=i,
                timestamp=i * 0.01,
                include_contacts=include_contacts,
                joint_velocities=joint_vels,
            )
            
            buffer.add_state(state)
            features = extract_step_features(state, buffer, sample_robot_config)
            
            # Should never crash or produce invalid values
            assert not np.any(np.isnan(features))
            assert not np.any(np.isinf(features))
    
    def test_zero_physics_dt(self, sample_robot_config):
        """Test handling when physics_dt approaches zero."""
        # Create config with very small dt
        config = RobotConfigLoader.create_generic_config(
            robot_id="tiny_dt",
            robot_type="test",
            num_joints=12,
            physics_dt=1e-10,
        )
        
        buffer = FeatureBuffer(buffer_size=5)
        state = create_valid_state()
        buffer.add_state(state)
        
        # Should not crash with very small dt
        features = extract_step_features(state, buffer, config)
        assert not np.any(np.isnan(features))


# =============================================================================
# SECTION 5: DATASET BUILDER TESTS
# =============================================================================

class TestDatasetBuilder:
    """Tests for AnomalyDetectionDatasetBuilder."""
    
    def test_add_single_episode(self):
        """Test adding a single episode."""
        builder = AnomalyDetectionDatasetBuilder()
        
        episode = EpisodeData(
            episode_id="ep_001",
            simulation_id="sim_001",
            robot_id="test_robot",
            outcome="success",
            features=np.random.randn(100, 40),
        )
        
        builder.add_episode(episode)
        assert len(builder) == 1
    
    def test_build_training_matrix(self):
        """Test building training matrix from multiple episodes."""
        builder = AnomalyDetectionDatasetBuilder()
        
        for i in range(5):
            episode = EpisodeData(
                episode_id=f"ep_{i:03d}",
                simulation_id=f"sim_{i:03d}",
                robot_id="test_robot",
                outcome="success",
                features=np.random.randn(100, 40),
            )
            builder.add_episode(episode)
        
        X = builder.build_training_matrix()
        assert X.shape == (500, 40)
    
    def test_filter_by_outcome(self):
        """Test filtering episodes by outcome."""
        builder = AnomalyDetectionDatasetBuilder()
        
        # Add success and failure episodes
        for i in range(3):
            builder.add_episode(EpisodeData(
                episode_id=f"success_{i}",
                simulation_id=f"sim_{i}",
                robot_id="test",
                outcome="success",
                features=np.random.randn(50, 40),
            ))
        
        for i in range(2):
            builder.add_episode(EpisodeData(
                episode_id=f"failure_{i}",
                simulation_id=f"sim_{i}",
                robot_id="test",
                outcome="failure",
                features=np.random.randn(50, 40),
            ))
        
        # Build only from successes
        X_success = builder.build_training_matrix(outcomes=["success"])
        assert X_success.shape == (150, 40)
        
        # Filter directly
        success_eps = builder.filter_by_outcome(["success"])
        assert len(success_eps) == 3
    
    def test_feature_dimension_mismatch(self):
        """Test that adding episode with wrong feature count raises error."""
        builder = AnomalyDetectionDatasetBuilder()
        
        builder.add_episode(EpisodeData(
            episode_id="ep_1",
            simulation_id="sim_1",
            robot_id="test",
            outcome="success",
            features=np.random.randn(50, 40),
        ))
        
        with pytest.raises(ValueError, match="Feature dimension mismatch"):
            builder.add_episode(EpisodeData(
                episode_id="ep_2",
                simulation_id="sim_2",
                robot_id="test",
                outcome="success",
                features=np.random.randn(50, 35),  # Wrong dimension
            ))
    
    def test_save_and_load_dataset(self, temp_directory):
        """Test saving and loading dataset."""
        builder = AnomalyDetectionDatasetBuilder()
        
        for i in range(3):
            builder.add_episode(EpisodeData(
                episode_id=f"ep_{i}",
                simulation_id=f"sim_{i}",
                robot_id="test",
                outcome="success",
                features=np.random.randn(50, 40),
            ))
        
        save_path = os.path.join(temp_directory, "dataset")
        builder.save_to_disk(save_path)
        
        loaded = AnomalyDetectionDatasetBuilder.load_from_disk(save_path)
        assert len(loaded) == 3
        
        X_original = builder.build_training_matrix()
        X_loaded = loaded.build_training_matrix()
        np.testing.assert_array_almost_equal(X_original, X_loaded)
    
    def test_invalid_outcome_raises_error(self):
        """Test that invalid outcome raises error."""
        with pytest.raises(ValueError, match="Invalid outcome"):
            EpisodeData(
                episode_id="ep_1",
                simulation_id="sim_1",
                robot_id="test",
                outcome="invalid_outcome",
                features=np.random.randn(50, 40),
            )
    
    def test_get_statistics(self):
        """Test getting dataset statistics."""
        builder = AnomalyDetectionDatasetBuilder()
        
        for i in range(5):
            builder.add_episode(EpisodeData(
                episode_id=f"ep_{i}",
                simulation_id=f"sim_{i}",
                robot_id="test",
                outcome="success",
                features=np.random.randn(100, 40),
            ))
        
        stats = builder.get_statistics()
        
        assert stats["num_episodes"] == 5
        assert stats["num_timesteps"] == 500
        assert stats["num_features"] == 40
        assert "feature_stats" in stats


# =============================================================================
# SECTION 6: ISOLATION FOREST MODEL TESTS
# =============================================================================

class TestIsolationForestModel:
    """Tests for IsolationForestModel."""
    
    def test_model_initialization(self):
        """Test model initializes correctly."""
        model = IsolationForestModel(
            n_estimators=100,
            contamination=0.05,
            random_state=42,
        )
        
        assert not model.is_fitted
        assert model.n_estimators == 100
        assert model.contamination == 0.05
    
    def test_model_fit(self):
        """Test model fitting."""
        model = IsolationForestModel(n_estimators=50)
        X = np.random.randn(500, 40)
        
        model.fit(X)
        
        assert model.is_fitted
        assert model.n_features_in_ == 40
        assert model.training_samples_ == 500
    
    def test_model_predict_score(self):
        """Test model prediction scores."""
        model = IsolationForestModel(n_estimators=50)
        X_train = np.random.randn(500, 40)
        model.fit(X_train)
        
        X_test = np.random.randn(100, 40)
        scores = model.predict_score(X_test)
        
        assert scores.shape == (100,)
        assert np.all(scores >= 0) and np.all(scores <= 1)
    
    def test_model_predict_single_sample(self):
        """Test prediction on single sample."""
        model = IsolationForestModel(n_estimators=50)
        X_train = np.random.randn(500, 40)
        model.fit(X_train)
        
        single_sample = np.random.randn(40)
        score = model.predict_score(single_sample)
        
        assert isinstance(score, (float, np.floating))
        assert 0 <= score <= 1
    
    def test_model_predict_binary_labels(self):
        """Test binary label prediction."""
        model = IsolationForestModel(n_estimators=50, contamination=0.1)
        X_train = np.random.randn(500, 40)
        model.fit(X_train)
        
        labels = model.predict(X_train)
        
        assert set(labels).issubset({-1, 1})
    
    def test_model_predict_before_fit_raises_error(self):
        """Test that predicting before fitting raises error."""
        model = IsolationForestModel()
        
        with pytest.raises(ValueError, match="Model must be fitted"):
            model.predict_score(np.random.randn(10, 40))
    
    def test_model_save_and_load(self, temp_directory):
        """Test model persistence."""
        model = IsolationForestModel(n_estimators=50, random_state=42)
        X_train = np.random.randn(500, 40)
        model.fit(X_train)
        
        original_score = model.predict_score(X_train[:10])
        
        save_path = os.path.join(temp_directory, "model")
        model.save(save_path)
        
        loaded = IsolationForestModel.load(save_path)
        loaded_score = loaded.predict_score(X_train[:10])
        
        np.testing.assert_array_almost_equal(original_score, loaded_score)
    
    def test_model_fit_invalid_input(self):
        """Test that fitting with invalid input raises error."""
        model = IsolationForestModel()
        
        # 1D array
        with pytest.raises(ValueError, match="X must be 2D"):
            model.fit(np.random.randn(100))
        
        # Contains NaN
        X_nan = np.random.randn(100, 40)
        X_nan[0, 0] = float('nan')
        with pytest.raises(ValueError, match="contains NaN"):
            model.fit(X_nan)


# =============================================================================
# SECTION 7: INFERENCE ENGINE TESTS
# =============================================================================

class TestInferenceEngine:
    """Tests for AnomalyDetectionInference."""
    
    @pytest.fixture
    def trained_model(self):
        """Create a trained model for inference tests."""
        model = IsolationForestModel(n_estimators=50, random_state=42)
        X = np.random.randn(500, 40)
        model.fit(X)
        return model
    
    def test_inference_initialization(self, trained_model, sample_robot_config):
        """Test inference engine initialization."""
        inference = AnomalyDetectionInference(
            model=trained_model,
            robot_config=sample_robot_config,
            anomaly_threshold=0.6,
        )
        
        assert inference.model == trained_model
        assert inference.anomaly_threshold == 0.6
        assert inference.steps_processed == 0
    
    def test_inference_init_requires_fitted_model(self, sample_robot_config):
        """Test that unfitted model raises error."""
        unfitted_model = IsolationForestModel()
        
        with pytest.raises(ValueError, match="Model must be fitted"):
            AnomalyDetectionInference(
                model=unfitted_model,
                robot_config=sample_robot_config,
            )
    
    def test_process_step(self, trained_model, sample_robot_config):
        """Test processing a single step."""
        inference = AnomalyDetectionInference(
            model=trained_model,
            robot_config=sample_robot_config,
        )
        
        state = create_valid_state()
        result = inference.process_step(state, timestamp=0.0)
        
        assert isinstance(result, AnomalyResult)
        assert 0 <= result.anomaly_score <= 1
        # is_anomaly can be Python bool or numpy.bool_ from comparison
        assert result.is_anomaly in (True, False) or isinstance(result.is_anomaly, (bool, np.bool_))
        assert result.features.shape == (40,)
    
    def test_process_episode(self, trained_model, sample_robot_config):
        """Test processing full episode."""
        inference = AnomalyDetectionInference(
            model=trained_model,
            robot_config=sample_robot_config,
            anomaly_threshold=0.6,
        )
        
        states = create_episode_states(num_steps=100)
        
        for state in states:
            result = inference.process_step(state)
        
        assert inference.steps_processed == 100
        stats = inference.get_statistics()
        assert stats["steps_processed"] == 100
    
    def test_reset_episode(self, trained_model, sample_robot_config):
        """Test episode reset clears state."""
        inference = AnomalyDetectionInference(
            model=trained_model,
            robot_config=sample_robot_config,
        )
        
        for state in create_episode_states(num_steps=50):
            inference.process_step(state)
        
        assert inference.steps_processed == 50
        
        inference.reset_episode()
        
        assert inference.steps_processed == 0
        assert inference.anomalies_detected == 0
    
    def test_set_threshold(self, trained_model, sample_robot_config):
        """Test threshold setting."""
        inference = AnomalyDetectionInference(
            model=trained_model,
            robot_config=sample_robot_config,
            anomaly_threshold=0.5,
        )
        
        inference.set_threshold(0.7)
        assert inference.anomaly_threshold == 0.7
        
        with pytest.raises(ValueError, match="must be in"):
            inference.set_threshold(1.5)


class TestThresholdCalibration:
    """Tests for threshold calibration."""
    
    def test_calibrate_threshold(self):
        """Test threshold calibration on normal data."""
        model = IsolationForestModel(n_estimators=50)
        X = np.random.randn(500, 40)
        model.fit(X)
        
        threshold = calibrate_threshold(model, X, percentile=95)
        
        assert 0 < threshold < 1
        
        # 95% of samples should have score below threshold
        scores = model.predict_score(X)
        below = np.mean(scores < threshold)
        assert below >= 0.90  # Allow some tolerance


class TestBatchInference:
    """Tests for batch inference on episodes."""
    
    def test_batch_inference_on_episode(self, sample_robot_config):
        """Test batch inference on complete episode."""
        model = IsolationForestModel(n_estimators=50)
        X_train = np.random.randn(500, 40)
        model.fit(X_train)
        
        states = create_episode_states(num_steps=100)
        
        results = batch_inference_on_episode(
            model=model,
            states=states,
            robot_config=sample_robot_config,
            threshold=0.6,
        )
        
        assert "scores" in results
        assert "labels" in results
        assert "anomaly_rate" in results
        assert len(results["scores"]) == 100


# =============================================================================
# SECTION 8: MODEL REGISTRY TESTS
# =============================================================================

class TestModelRegistry:
    """Tests for ModelRegistry per-project model management."""
    
    @pytest.fixture
    def registry(self, temp_directory):
        """Create a test registry."""
        return ModelRegistry(base_dir=temp_directory)
    
    def test_registry_initialization(self, registry):
        """Test registry initializes correctly."""
        assert registry.base_dir.exists()
    
    def test_model_exists_when_empty(self, registry):
        """Test model_exists returns False for unknown project."""
        assert not registry.model_exists("unknown_project")
    
    def test_save_and_load_model(self, registry):
        """Test saving and loading model via registry."""
        model = IsolationForestModel(n_estimators=50)
        model.fit(np.random.randn(500, 40))
        
        registry.save_model("test_project", model)
        
        assert registry.model_exists("test_project")
        
        loaded = registry.load_model("test_project")
        assert loaded is not None
        assert loaded.is_fitted
    
    def test_add_episode_data(self, registry):
        """Test adding episode data for training."""
        features = np.random.randn(100, 40)
        
        status = registry.add_episode_data(
            project_id="test_project",
            features=features,
            episode_id="ep_001",
            outcome="success",
        )
        
        assert status["episodes_collected"] == 1
        assert not status["ready_for_training"]
    
    def test_should_train_threshold(self, registry):
        """Test auto-training threshold detection."""
        project_id = "test_training"
        
        # Add just under threshold
        for i in range(MIN_EPISODES_FOR_TRAINING - 1):
            registry.add_episode_data(
                project_id=project_id,
                features=np.random.randn(60, 40),
                episode_id=f"ep_{i:03d}",
                outcome="success",
            )
        
        assert not registry.should_train(project_id)
        
        # Add one more to hit threshold
        registry.add_episode_data(
            project_id=project_id,
            features=np.random.randn(60, 40),
            episode_id=f"ep_{MIN_EPISODES_FOR_TRAINING:03d}",
            outcome="success",
        )
        
        assert registry.should_train(project_id)
    
    def test_train_model_via_registry(self, registry):
        """Test training model through registry."""
        project_id = "train_test"
        
        # Add sufficient episodes
        for i in range(MIN_EPISODES_FOR_TRAINING):
            registry.add_episode_data(
                project_id=project_id,
                features=np.random.randn(100, 40),
                episode_id=f"ep_{i:03d}",
                outcome="success",
            )
        
        model, metrics = registry.train_model(project_id, verbose=False)
        
        assert model.is_fitted
        assert "n_train_samples" in metrics
    
    def test_list_projects(self, registry):
        """Test listing projects with models."""
        model = IsolationForestModel(n_estimators=50)
        model.fit(np.random.randn(100, 40))
        
        registry.save_model("project_a", model)
        registry.save_model("project_b", model)
        
        projects = registry.list_projects()
        assert "project_a" in projects
        assert "project_b" in projects
    
    def test_delete_model(self, registry):
        """Test deleting a model."""
        model = IsolationForestModel(n_estimators=50)
        model.fit(np.random.randn(100, 40))
        
        registry.save_model("to_delete", model)
        assert registry.model_exists("to_delete")
        
        result = registry.delete_model("to_delete")
        assert result
        assert not registry.model_exists("to_delete")
    
    def test_project_id_sanitization(self, registry):
        """Test that unsafe project IDs are sanitized."""
        model = IsolationForestModel(n_estimators=50)
        model.fit(np.random.randn(100, 40))
        
        # Project ID with special characters
        unsafe_id = "project/test/../hack"
        registry.save_model(unsafe_id, model)
        
        # Should not create unsafe paths
        project_dir = registry.get_project_dir(unsafe_id)
        assert ".." not in str(project_dir)


# =============================================================================
# SECTION 9: END-TO-END PIPELINE TESTS
# =============================================================================

class TestEndToEndPipeline:
    """End-to-end integration tests for the complete pipeline."""
    
    def test_full_pipeline_normal_data(self, sample_robot_config, temp_directory):
        """Test complete pipeline with normal data."""
        # Step 1: Generate training data
        states = create_episode_states(num_steps=200)
        features = extract_episode_features(states, sample_robot_config)
        
        # Step 2: Build dataset
        builder = AnomalyDetectionDatasetBuilder()
        builder.add_episode(EpisodeData(
            episode_id="train_ep",
            simulation_id="sim_1",
            robot_id="test",
            outcome="success",
            features=features,
        ))
        
        # Step 3: Train model
        model = IsolationForestModel(n_estimators=100)
        X_train = builder.build_training_matrix()
        model.fit(X_train)
        
        # Step 4: Create inference engine
        inference = AnomalyDetectionInference(
            model=model,
            robot_config=sample_robot_config,
            anomaly_threshold=0.7,
        )
        
        # Step 5: Run inference on new normal data
        test_states = create_episode_states(num_steps=100)
        anomaly_count = 0
        for state in test_states:
            result = inference.process_step(state)
            if result.is_anomaly:
                anomaly_count += 1
        
        # Normal data should have low anomaly rate
        anomaly_rate = anomaly_count / 100
        assert anomaly_rate < 0.3, f"Anomaly rate too high for normal data: {anomaly_rate}"
    
    def test_full_pipeline_anomaly_detection(self, sample_robot_config):
        """Test pipeline detects synthetic anomalies."""
        # Train on normal data
        normal_states = create_episode_states(num_steps=500, add_noise=False)
        normal_features = extract_episode_features(normal_states, sample_robot_config)
        
        model = IsolationForestModel(n_estimators=100, contamination=0.01)
        model.fit(normal_features)
        
        # Test on data with anomalies
        anomalous_states = create_anomalous_states(
            num_steps=100,
            anomaly_start=40,
            anomaly_end=60,
            anomaly_type="torque_spike",
        )
        
        inference = AnomalyDetectionInference(
            model=model,
            robot_config=sample_robot_config,
            anomaly_threshold=0.5,
        )
        
        anomaly_detected_in_window = False
        for i, state in enumerate(anomalous_states):
            result = inference.process_step(state)
            if 40 <= i < 60 and result.is_anomaly:
                anomaly_detected_in_window = True
        
        # Should detect at least some anomalies in the anomaly window
        assert anomaly_detected_in_window, "Failed to detect synthetic anomaly"
    
    def test_pipeline_with_multiple_anomaly_types(self, sample_robot_config):
        """Test detection of different anomaly types."""
        # Train on clean normal data
        normal_states = create_episode_states(num_steps=500, add_noise=False)
        normal_features = extract_episode_features(normal_states, sample_robot_config)
        
        model = IsolationForestModel(n_estimators=100, contamination=0.01)
        model.fit(normal_features)
        
        anomaly_types = ["torque_spike", "velocity_jump", "contact_loss", "height_drop"]
        detected = {}
        
        for atype in anomaly_types:
            anomalous_states = create_anomalous_states(
                num_steps=100,
                anomaly_start=40,
                anomaly_end=60,
                anomaly_type=atype,
            )
            
            inference = AnomalyDetectionInference(
                model=model,
                robot_config=sample_robot_config,
                anomaly_threshold=0.5,
            )
            
            anomalies_in_window = 0
            for i, state in enumerate(anomalous_states):
                result = inference.process_step(state)
                if 40 <= i < 60 and result.is_anomaly:
                    anomalies_in_window += 1
            
            detected[atype] = anomalies_in_window > 0
            inference.reset_episode()
        
        # At least some anomaly types should be detected
        detected_count = sum(detected.values())
        assert detected_count >= 2, f"Only detected {detected_count}/{len(anomaly_types)} anomaly types: {detected}"


# =============================================================================
# SECTION 10: UTILITY FUNCTION TESTS
# =============================================================================

class TestUtilityFunctions:
    """Tests for utility functions."""
    
    def test_safe_divide_normal(self):
        """Test safe_divide with normal values."""
        result = safe_divide(10.0, 2.0)
        assert result == pytest.approx(5.0, rel=1e-5)
    
    def test_safe_divide_by_zero(self):
        """Test safe_divide handles zero denominator."""
        result = safe_divide(10.0, 0.0, default=0.0)
        assert result == 0.0
    
    def test_safe_divide_array(self):
        """Test safe_divide with arrays."""
        num = np.array([10.0, 20.0, 30.0])
        den = np.array([2.0, 0.0, 5.0])
        
        result = safe_divide(num, den, default=0.0)
        
        assert result[0] == pytest.approx(5.0, rel=1e-5)
        assert result[1] == 0.0  # Division by zero case
        assert result[2] == pytest.approx(6.0, rel=1e-5)
    
    def test_safe_normalize(self):
        """Test safe_normalize."""
        result = safe_normalize(5.0, 10.0)
        assert result == pytest.approx(0.5, rel=1e-5)
    
    def test_safe_normalize_zero_max(self):
        """Test safe_normalize with zero max value."""
        result = safe_normalize(5.0, 0.0, default=0.5)
        assert result == 0.5
    
    def test_clip_features(self):
        """Test feature clipping."""
        features = np.array([-20.0, -5.0, 0.0, 5.0, 20.0])
        clipped = clip_features(features, min_val=-10.0, max_val=10.0)
        
        assert np.all(clipped >= -10.0)
        assert np.all(clipped <= 10.0)
        np.testing.assert_array_equal(clipped, [-10.0, -5.0, 0.0, 5.0, 10.0])
    
    def test_replace_nan_inf(self):
        """Test NaN/Inf replacement."""
        arr = np.array([1.0, float('nan'), 3.0, float('inf'), float('-inf')])
        cleaned = replace_nan_inf(arr, nan_value=0.0, inf_value=0.0)
        
        assert not np.any(np.isnan(cleaned))
        assert not np.any(np.isinf(cleaned))
        np.testing.assert_array_equal(cleaned, [1.0, 0.0, 3.0, 0.0, 0.0])
    
    def test_compute_rms(self):
        """Test RMS computation."""
        values = np.array([3.0, 4.0])  # RMS should be sqrt((9+16)/2) = sqrt(12.5)
        result = compute_rms(values)
        expected = np.sqrt(12.5)
        assert result == pytest.approx(expected, rel=1e-5)
    
    def test_compute_rms_empty(self):
        """Test RMS with empty array."""
        result = compute_rms(np.array([]))
        assert result == 0.0


# =============================================================================
# SECTION 11: STRESS TESTS
# =============================================================================

class TestStressConditions:
    """Stress tests for robustness under extreme conditions."""
    
    def test_large_episode(self, sample_robot_config):
        """Test handling very large episodes."""
        states = create_episode_states(num_steps=10000)
        features = extract_episode_features(states, sample_robot_config)
        
        assert features.shape == (10000, 40)
        assert not np.any(np.isnan(features))
    
    def test_many_short_episodes(self, sample_robot_config, temp_directory):
        """Test handling many short episodes."""
        builder = AnomalyDetectionDatasetBuilder()
        
        for i in range(100):
            states = create_episode_states(num_steps=10)
            features = extract_episode_features(states, sample_robot_config)
            builder.add_episode(EpisodeData(
                episode_id=f"ep_{i:03d}",
                simulation_id=f"sim_{i:03d}",
                robot_id="test",
                outcome="success",
                features=features,
            ))
        
        X = builder.build_training_matrix()
        assert X.shape == (1000, 40)
        
        # Should still train successfully
        model = IsolationForestModel(n_estimators=50)
        model.fit(X)
        assert model.is_fitted
    
    def test_high_frequency_inference(self, sample_robot_config):
        """Test high-frequency inference calls."""
        model = IsolationForestModel(n_estimators=50)
        model.fit(np.random.randn(500, 40))
        
        inference = AnomalyDetectionInference(
            model=model,
            robot_config=sample_robot_config,
        )
        
        import time
        start = time.time()
        
        for i in range(1000):
            state = create_valid_state(step=i)
            inference.process_step(state)
        
        elapsed = time.time() - start
        avg_ms = (elapsed / 1000) * 1000
        
        # Should be under 10ms per step on average
        assert avg_ms < 10, f"Inference too slow: {avg_ms:.2f}ms per step"


# =============================================================================
# RUN CONFIGURATION
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
