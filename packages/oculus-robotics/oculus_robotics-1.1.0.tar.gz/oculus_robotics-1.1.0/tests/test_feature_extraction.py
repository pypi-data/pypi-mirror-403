"""
Test feature extraction pipeline to ensure Phase 1 works correctly.
"""

import pytest
import numpy as np
from oculus.core.state import UniversalState
from oculus.anomaly_detection import (
    RobotConfig,
    FeatureBuffer,
    extract_step_features,
    extract_episode_features,
    FEATURE_NAMES
)


def create_test_state(step=0, timestamp=0.0):
    """Create a valid test state."""
    return UniversalState(
        step=step,
        timestamp=timestamp,
        joint_positions=[0.1, -0.2, 0.3, 0.0, 0.1, -0.1] * 2,  # 12 joints
        joint_velocities=[0.5, -0.3, 0.2, 0.1, -0.4, 0.3] * 2,
        joint_torques=[10.0, -15.0, 20.0, 5.0, -10.0, 12.0] * 2,
        base_position=(1.0, 0.5, 0.6),
        base_orientation=(0.0, 0.0, 0.0, 1.0),
        base_linear_vel=(0.2, 0.1, 0.05),
        base_angular_vel=(0.01, 0.02, -0.01),
        contact_forces=[(0.0, 0.0, 50.0), (0.0, 0.0, 48.0), (0.0, 0.0, 52.0), (0.0, 0.0, 49.0)],
        contact_points=[(0.3, 0.2, 0.0), (0.3, -0.2, 0.0), (-0.3, 0.2, 0.0), (-0.3, -0.2, 0.0)]
    )


def create_test_robot_config():
    """Create a valid robot configuration."""
    return RobotConfig(
        robot_id="test_robot",
        robot_type="quadruped",
        num_joints=12,
        max_linear_velocity=2.0,
        max_angular_velocity=3.0,
        max_linear_acceleration=10.0,
        max_angular_acceleration=15.0,
        max_joint_velocity=np.ones(12) * 3.0,
        max_joint_torque=np.ones(12) * 100.0,
        max_joint_acceleration=np.ones(12) * 20.0,
        expected_standing_height=0.5,
        max_contact_force=200.0,
        robot_mass=50.0
    )


class TestFeatureExtraction:
    """Test feature extraction functions."""
    
    def test_feature_count(self):
        """Test that we extract exactly 40 features."""
        assert len(FEATURE_NAMES) == 40, f"Expected 40 features, got {len(FEATURE_NAMES)}"
    
    def test_extract_single_step(self):
        """Test single step feature extraction."""
        state = create_test_state()
        robot_cfg = create_test_robot_config()
        buffer = FeatureBuffer()
        buffer.add_state(state)
        
        features = extract_step_features(state, buffer, robot_cfg)
        
        # Check shape
        assert features.shape == (40,), f"Expected (40,) features, got {features.shape}"
        
        # Check no NaN/Inf
        assert not np.any(np.isnan(features)), "Features contain NaN"
        assert not np.any(np.isinf(features)), "Features contain Inf"
        
        # Check reasonable range (should be roughly normalized)
        print(f"\nFeature range: [{features.min():.3f}, {features.max():.3f}]")
        print(f"Mean: {features.mean():.3f}, Std: {features.std():.3f}")
        
        # Features should be mostly in reasonable range after normalization
        assert features.min() >= -20, f"Features too negative: {features.min()}"
        assert features.max() <= 20, f"Features too large: {features.max()}"
    
    def test_extract_with_history(self):
        """Test feature extraction with temporal history."""
        robot_cfg = create_test_robot_config()
        buffer = FeatureBuffer(buffer_size=20)
        
        # Add multiple states
        states = []
        for i in range(10):
            state = create_test_state(step=i, timestamp=i * 0.01)
            buffer.add_state(state)
            states.append(state)
        
        # Extract features for last state
        features = extract_step_features(states[-1], buffer, robot_cfg)
        
        assert features.shape == (40,)
        assert not np.any(np.isnan(features))
        
        print(f"\nWith history - Feature range: [{features.min():.3f}, {features.max():.3f}]")
    
    def test_extract_episode_features(self):
        """Test extracting features for entire episode."""
        robot_cfg = create_test_robot_config()
        
        # Create episode
        states = []
        for i in range(50):
            state = create_test_state(step=i, timestamp=i * 0.01)
            states.append(state)
        
        # Extract episode features
        episode_features = extract_episode_features(states, robot_cfg)
        
        # Check shape
        assert episode_features.shape == (50, 40), f"Expected (50, 40), got {episode_features.shape}"
        
        # Check no NaN/Inf
        assert not np.any(np.isnan(episode_features)), "Episode features contain NaN"
        assert not np.any(np.isinf(episode_features)), "Episode features contain Inf"
        
        print(f"\nEpisode features:")
        print(f"  Shape: {episode_features.shape}")
        print(f"  Range: [{episode_features.min():.3f}, {episode_features.max():.3f}]")
        print(f"  Mean: {episode_features.mean():.3f}")
    
    def test_feature_changes_with_state(self):
        """Test that features actually change with different states."""
        robot_cfg = create_test_robot_config()
        buffer = FeatureBuffer()
        
        # State 1: Normal
        state1 = create_test_state()
        buffer.add_state(state1)
        features1 = extract_step_features(state1, buffer, robot_cfg)
        
        # State 2: High velocity
        state2 = UniversalState(
            step=1,
            timestamp=0.01,
            joint_positions=[0.1] * 12,
            joint_velocities=[2.0] * 12,  # Much higher
            joint_torques=[10.0] * 12,
            base_position=(1.0, 0.5, 0.6),
            base_orientation=(0.0, 0.0, 0.0, 1.0),
            base_linear_vel=(1.5, 0.0, 0.0),  # Much higher
            base_angular_vel=(0.01, 0.02, -0.01),
            contact_forces=[(0.0, 0.0, 50.0)] * 4,
            contact_points=[(0.3, 0.2, 0.0), (0.3, -0.2, 0.0), (-0.3, 0.2, 0.0), (-0.3, -0.2, 0.0)]
        )
        buffer.add_state(state2)
        features2 = extract_step_features(state2, buffer, robot_cfg)
        
        # Features should be different
        diff = np.abs(features1 - features2).sum()
        print(f"\nFeature difference: {diff:.3f}")
        assert diff > 0.1, "Features don't change enough between different states"
    
    def test_anomalous_state_detection(self):
        """Test that anomalous states produce different features."""
        robot_cfg = create_test_robot_config()
        buffer = FeatureBuffer()
        
        # Normal state
        normal_state = create_test_state()
        buffer.add_state(normal_state)
        normal_features = extract_step_features(normal_state, buffer, robot_cfg)
        
        # Anomalous state: extreme torque spike
        anomalous_state = UniversalState(
            step=1,
            timestamp=0.01,
            joint_positions=[0.1] * 12,
            joint_velocities=[0.5] * 12,
            joint_torques=[90.0] * 12,  # Near maximum torque
            base_position=(1.0, 0.5, 0.6),
            base_orientation=(0.0, 0.0, 0.0, 1.0),
            base_linear_vel=(0.2, 0.1, 0.05),
            base_angular_vel=(0.01, 0.02, -0.01),
            contact_forces=[(0.0, 0.0, 50.0)] * 4,
            contact_points=[(0.3, 0.2, 0.0), (0.3, -0.2, 0.0), (-0.3, 0.2, 0.0), (-0.3, -0.2, 0.0)]
        )
        buffer.add_state(anomalous_state)
        anomalous_features = extract_step_features(anomalous_state, buffer, robot_cfg)
        
        # Calculate difference
        diff = np.abs(normal_features - anomalous_features)
        print(f"\nNormal vs Anomalous:")
        print(f"  Total difference: {diff.sum():.3f}")
        print(f"  Max difference: {diff.max():.3f}")
        print(f"  Features changed (>0.1): {(diff > 0.1).sum()}/40")
        
        # Should see significant difference
        assert diff.sum() > 1.0, "Anomalous state not different enough from normal"
        assert (diff > 0.1).sum() >= 5, "Too few features changed for anomaly"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
