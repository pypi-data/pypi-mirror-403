"""
Test synthetic data generator to verify anomalies are detectable.
"""

import numpy as np
from oculus.anomaly_detection.test_data_generator import SyntheticDataGenerator
from oculus.anomaly_detection import (
    RobotConfig,
    extract_episode_features
)


def test_synthetic_anomalies():
    """Test that synthetic anomalies create distinguishable features."""
    
    generator = SyntheticDataGenerator(num_joints=12, random_seed=42)
    
    robot_cfg = RobotConfig(
        robot_id="test",
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
    
    print("\n" + "="*70)
    print("Testing Synthetic Data Quality")
    print("="*70)
    
    # Generate normal episode
    print("\n[1/5] Generating normal episode...")
    normal_states = generator.generate_normal_episode(duration=5.0)
    normal_features = extract_episode_features(normal_states, robot_cfg)
    
    print(f"  ✓ Normal episode: {len(normal_states)} steps")
    print(f"  ✓ Feature shape: {normal_features.shape}")
    print(f"  ✓ Feature range: [{normal_features.min():.3f}, {normal_features.max():.3f}]")
    print(f"  ✓ Feature mean: {normal_features.mean():.3f}")
    print(f"  ✓ Feature std: {normal_features.std():.3f}")
    
    # Test each anomaly type
    anomaly_types = ["torque_spike", "velocity_jump", "contact_loss", "instability"]
    
    for i, anomaly_type in enumerate(anomaly_types, 2):
        print(f"\n[{i}/5] Testing {anomaly_type} anomaly...")
        
        # Generate anomalous episode
        anomalous_states = generator.generate_anomalous_episode(
            duration=10.0,
            anomaly_type=anomaly_type,
            anomaly_start=5.0,
            anomaly_duration=2.0
        )
        anomalous_features = extract_episode_features(anomalous_states, robot_cfg)
        
        # Compare features before and after anomaly injection
        start_idx = int(5.0 / generator.dt)
        end_idx = int(7.0 / generator.dt)
        
        normal_period = anomalous_features[:start_idx]
        anomaly_period = anomalous_features[start_idx:end_idx]
        
        # Calculate differences
        normal_mean = normal_period.mean(axis=0)
        anomaly_mean = anomaly_period.mean(axis=0)
        feature_diff = np.abs(anomaly_mean - normal_mean)
        
        print(f"  ✓ Episode: {len(anomalous_states)} steps")
        print(f"  ✓ Anomaly period: steps {start_idx}-{end_idx}")
        print(f"  ✓ Feature difference (mean): {feature_diff.mean():.3f}")
        print(f"  ✓ Feature difference (max): {feature_diff.max():.3f}")
        print(f"  ✓ Features changed (>0.1): {(feature_diff > 0.1).sum()}/40")
        print(f"  ✓ Features changed (>0.5): {(feature_diff > 0.5).sum()}/40")
        
        # Assertions
        assert feature_diff.mean() > 0.05, f"{anomaly_type}: Mean difference too small"
        assert (feature_diff > 0.1).sum() >= 3, f"{anomaly_type}: Too few features changed"
        
        # Print top changed features
        top_indices = np.argsort(feature_diff)[-5:][::-1]
        print(f"  ✓ Top 5 changed features:")
        for idx in top_indices:
            print(f"     - Feature {idx}: Δ={feature_diff[idx]:.3f}")
    
    print("\n" + "="*70)
    print("✅ All synthetic anomaly tests passed!")
    print("="*70)


if __name__ == "__main__":
    test_synthetic_anomalies()
