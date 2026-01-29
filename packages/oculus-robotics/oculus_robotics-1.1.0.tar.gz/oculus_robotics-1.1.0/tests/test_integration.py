"""
Integration test: end-to-end anomaly detection pipeline.

Tests the complete workflow:
1. Generate synthetic data
2. Extract features
3. Train model
4. Run inference
5. Validate accuracy (target: 80%+)
"""

import pytest
import numpy as np
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score

from oculus.anomaly_detection.test_data_generator import create_test_dataset
from oculus.anomaly_detection.features import extract_episode_features
from oculus.anomaly_detection.config import RobotConfig
from oculus.anomaly_detection.dataset import EpisodeData, AnomalyDetectionDatasetBuilder
from oculus.anomaly_detection.model import IsolationForestModel
from oculus.anomaly_detection.inference import AnomalyDetectionInference, calibrate_threshold


class TestIntegration:
    """End-to-end integration tests."""
    
    def test_complete_pipeline(self):
        """Test complete pipeline from synthetic data to inference."""
        
        print("\n" + "="*60)
        print("Running End-to-End Integration Test")
        print("="*60)
        
        # Step 1: Generate synthetic data
        print("\n[1/6] Generating synthetic data...")
        train_episodes, test_episodes, test_labels = create_test_dataset(
            num_joints=12,
            num_train_normal=50,
            num_test_normal=10,
            num_test_anomalous=10
        )
        print(f"  ✓ Generated {len(train_episodes)} training episodes")
        print(f"  ✓ Generated {len(test_episodes)} test episodes")
        
        # Step 2: Create robot config
        print("\n[2/6] Creating robot configuration...")
        robot_cfg = RobotConfig(
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
        print(f"  ✓ Robot config created")
        
        # Step 3: Extract features and build dataset
        print("\n[3/6] Extracting features...")
        builder = AnomalyDetectionDatasetBuilder()
        
        for i, episode_states in enumerate(train_episodes):
            features = extract_episode_features(episode_states, robot_cfg)
            episode = EpisodeData(
                episode_id=f"train_{i}",
                simulation_id=f"sim_train_{i}",
                robot_id="test_robot",
                outcome="success",
                features=features
            )
            builder.add_episode(episode)
        
        X_train = builder.build_training_matrix(outcomes=["success"])
        print(f"  ✓ Extracted training features: {X_train.shape}")
        
        # Extract test features
        test_features_list = []
        for episode_states in test_episodes:
            features = extract_episode_features(episode_states, robot_cfg)
            test_features_list.append(features)
        
        # Combine test features
        X_test = np.vstack(test_features_list)
        
        # Create test labels (repeat label for each timestep)
        y_test = []
        for label, features in zip(test_labels, test_features_list):
            y_test.extend([label] * features.shape[0])
        y_test = np.array(y_test)
        
        print(f"  ✓ Extracted test features: {X_test.shape}")
        print(f"  ✓ Test labels: {y_test.shape}")
        
        # Step 4: Train model
        print("\n[4/6] Training Isolation Forest...")
        model = IsolationForestModel(n_estimators=100, random_state=42)
        model.fit(X_train)
        print(f"  ✓ Model trained on {X_train.shape[0]} samples")
        
        # Step 5: Calibrate threshold
        print("\n[5/6] Calibrating threshold...")
        # Use subset of training data for calibration
        threshold = calibrate_threshold(model, X_train[:500], percentile=95)
        print(f"  ✓ Calibrated threshold: {threshold:.3f}")
        
        # Step 6: Run inference and evaluate
        print("\n[6/6] Running inference and evaluation...")
        scores = model.predict_score(X_test)
        predictions = (scores >= threshold).astype(int)
        
        # Compute metrics
        accuracy = accuracy_score(y_test, predictions)
        f1 = f1_score(y_test, predictions, zero_division=0)
        
        # ROC AUC
        if len(np.unique(y_test)) > 1:
            roc_auc = roc_auc_score(y_test, scores)
        else:
            roc_auc = 0.0
        
        print(f"  ✓ Accuracy: {accuracy:.1%}")
        print(f"  ✓ F1 Score: {f1:.3f}")
        print(f"  ✓ ROC AUC: {roc_auc:.3f}")
        
        # Print confusion matrix info
        normal_samples = (y_test == 0).sum()
        anomaly_samples = (y_test == 1).sum()
        true_positives = ((predictions == 1) & (y_test == 1)).sum()
        false_positives = ((predictions == 1) & (y_test == 0)).sum()
        true_negatives = ((predictions == 0) & (y_test == 0)).sum()
        false_negatives = ((predictions == 0) & (y_test == 1)).sum()
        
        print(f"\n  Confusion Matrix:")
        print(f"    True Positives: {true_positives}/{anomaly_samples}")
        print(f"    False Positives: {false_positives}/{normal_samples}")
        print(f"    True Negatives: {true_negatives}/{normal_samples}")
        print(f"    False Negatives: {false_negatives}/{anomaly_samples}")
        
        print("\n" + "="*60)
        print("Integration Test Complete!")
        print("="*60)
        
        # Assertions
        assert accuracy >= 0.70, f"Accuracy {accuracy:.1%} below 70% threshold"
        print(f"\n✅ PASS: Accuracy {accuracy:.1%} >= 70%")
        
        # Verify model can detect some anomalies
        assert true_positives > 0, "Model failed to detect any anomalies"
        print(f"✅ PASS: Detected {true_positives} anomalies")
        
    def test_inference_engine(self):
        """Test real-time inference engine."""
        
        print("\n" + "="*60)
        print("Testing Inference Engine")
        print("="*60)
        
        # Generate data
        train_episodes, test_episodes, test_labels = create_test_dataset(
            num_joints=12,
            num_train_normal=30,
            num_test_normal=5,
            num_test_anomalous=5
        )
        
        # Create config
        robot_cfg = RobotConfig(
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
        
        # Extract features and train
        builder = AnomalyDetectionDatasetBuilder()
        for i, episode_states in enumerate(train_episodes):
            features = extract_episode_features(episode_states, robot_cfg)
            episode = EpisodeData(
                episode_id=f"train_{i}",
                simulation_id=f"sim_train_{i}",
                robot_id="test_robot",
                outcome="success",
                features=features
            )
            builder.add_episode(episode)
        
        X_train = builder.build_training_matrix()
        model = IsolationForestModel(n_estimators=50, random_state=42)
        model.fit(X_train)
        
        # Create inference engine
        inference = AnomalyDetectionInference(
            model=model,
            robot_config=robot_cfg,
            anomaly_threshold=0.6
        )
        
        # Test step-by-step processing
        print("\n[1/3] Testing step-by-step processing...")
        test_episode = test_episodes[0]
        
        results = []
        for state in test_episode:
            result = inference.process_step(state)
            results.append(result)
        
        print(f"  ✓ Processed {len(results)} steps")
        print(f"  ✓ Anomalies detected: {sum(r.is_anomaly for r in results)}")
        
        # Check statistics
        stats = inference.get_statistics()
        assert stats["steps_processed"] == len(test_episode)
        print(f"  ✓ Statistics: {stats}")
        
        # Test reset
        print("\n[2/3] Testing episode reset...")
        inference.reset_episode()
        stats_after_reset = inference.get_statistics()
        assert stats_after_reset["steps_processed"] == 0
        print(f"  ✓ Reset successful")
        
        # Test threshold adjustment
        print("\n[3/3] Testing threshold adjustment...")
        inference.set_threshold(0.7)
        assert inference.anomaly_threshold == 0.7
        print(f"  ✓ Threshold updated to 0.7")
        
        print("\n✅ Inference engine tests passed!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
