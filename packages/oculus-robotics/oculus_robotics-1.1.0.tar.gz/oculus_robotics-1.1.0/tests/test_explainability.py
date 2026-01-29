"""
Test SHAP explainability integration.

Tests ShapExplainer with Isolation Forest for feature attribution.
"""

import pytest
import numpy as np
from sklearn.metrics import accuracy_score

from oculus.anomaly_detection import (
    IsolationForestModel,
    ShapExplainer,
    FEATURE_NAMES,
    RobotConfig,
    AnomalyDetectionInference
)
from oculus.anomaly_detection.test_data_generator import create_test_dataset
from oculus.anomaly_detection.features import extract_episode_features


class TestShapExplainer:
    """Test SHAP explainability features."""
    
    @pytest.fixture
    def trained_model_and_data(self):
        """Create trained model and test data."""
        # Generate synthetic data
        train_episodes, test_episodes, test_labels = create_test_dataset(
            num_joints=12,
            num_train_normal=30,
            num_test_normal=5,
            num_test_anomalous=5
        )
        
        # Robot config
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
        
        # Extract features
        X_train = []
        for episode_states in train_episodes:
            features = extract_episode_features(episode_states, robot_cfg)
            X_train.append(features)
        X_train = np.vstack(X_train)
        
        # Train model
        model = IsolationForestModel(n_estimators=100, random_state=42)
        model.fit(X_train)
        
        return model, X_train, robot_cfg
    
    def test_explainer_initialization(self, trained_model_and_data):
        """Test ShapExplainer initialization."""
        model, X_train, robot_cfg = trained_model_and_data
        
        # Create explainer
        explainer = ShapExplainer(
            model=model,
            background_data=X_train[:100],
            feature_names=FEATURE_NAMES
        )
        
        assert explainer.model == model
        assert explainer.background_data.shape[0] <= 100
        assert len(explainer.feature_names) == 40
        assert explainer.explainer is not None
    
    def test_explainer_requires_fitted_model(self):
        """Test that explainer requires fitted model."""
        model = IsolationForestModel()
        X_dummy = np.random.rand(100, 40)
        
        with pytest.raises(ValueError, match="must be fitted"):
            ShapExplainer(model=model, background_data=X_dummy)
    
    def test_explainer_validates_background_data(self, trained_model_and_data):
        """Test background data validation."""
        model, _, _ = trained_model_and_data
        
        # Empty data (wrong shape)
        with pytest.raises(ValueError, match="must be 2D"):
            ShapExplainer(model=model, background_data=np.array([]))
        
        # Wrong dimensionality
        with pytest.raises(ValueError, match="must be 2D"):
            ShapExplainer(model=model, background_data=np.random.rand(100))
        
        # Feature count mismatch
        with pytest.raises(ValueError, match="Feature count mismatch"):
            ShapExplainer(
                model=model,
                background_data=np.random.rand(100, 30),  # Wrong feature count
                feature_names=FEATURE_NAMES
            )
    
    def test_explain_instance(self, trained_model_and_data):
        """Test single instance explanation."""
        model, X_train, robot_cfg = trained_model_and_data
        
        explainer = ShapExplainer(
            model=model,
            background_data=X_train[:100]
        )
        
        # Explain single instance
        X_test = X_train[0]
        explanation = explainer.explain_instance(X_test, top_k=5)
        
        # Check structure
        assert "anomaly_score" in explanation
        assert "base_value" in explanation
        assert "shap_values" in explanation
        assert "top_features" in explanation
        
        # Check types
        assert isinstance(explanation["anomaly_score"], float)
        assert isinstance(explanation["base_value"], float)
        assert isinstance(explanation["shap_values"], np.ndarray)
        assert len(explanation["shap_values"]) == 40
        
        # Check top features
        assert len(explanation["top_features"]) == 5
        for feat in explanation["top_features"]:
            assert "rank" in feat
            assert "feature_name" in feat
            assert "feature_value" in feat
            assert "shap_value" in feat
            assert "abs_shap_value" in feat
        
        # Ranks should be ordered
        ranks = [f["rank"] for f in explanation["top_features"]]
        assert ranks == [1, 2, 3, 4, 5]
        
        # SHAP values should be ordered by absolute value (descending)
        abs_shap_values = [f["abs_shap_value"] for f in explanation["top_features"]]
        assert abs_shap_values == sorted(abs_shap_values, reverse=True)
    
    def test_explain_instance_reshapes_input(self, trained_model_and_data):
        """Test that explain_instance handles different input shapes."""
        model, X_train, robot_cfg = trained_model_and_data
        
        explainer = ShapExplainer(model=model, background_data=X_train[:100])
        
        # Test with 1D input
        X_1d = X_train[0]  # Shape: (40,)
        explanation_1d = explainer.explain_instance(X_1d)
        
        # Test with 2D input
        X_2d = X_train[0:1]  # Shape: (1, 40)
        explanation_2d = explainer.explain_instance(X_2d)
        
        # Should produce same results
        assert explanation_1d["anomaly_score"] == explanation_2d["anomaly_score"]
        np.testing.assert_array_almost_equal(
            explanation_1d["shap_values"],
            explanation_2d["shap_values"]
        )
    
    def test_explain_batch(self, trained_model_and_data):
        """Test batch explanation."""
        model, X_train, robot_cfg = trained_model_and_data
        
        explainer = ShapExplainer(model=model, background_data=X_train[:100])
        
        # Explain batch
        X_batch = X_train[:10]
        explanations = explainer.explain_batch(X_batch, top_k=3)
        
        # Check we get one explanation per sample
        assert len(explanations) == 10
        
        # Check each explanation
        for exp in explanations:
            assert "anomaly_score" in exp
            assert "base_value" in exp
            assert "shap_values" in exp
            assert "top_features" in exp
            assert len(exp["top_features"]) == 3
    
    def test_global_feature_importance(self, trained_model_and_data):
        """Test global feature importance computation."""
        model, X_train, robot_cfg = trained_model_and_data
        
        explainer = ShapExplainer(model=model, background_data=X_train[:100])
        
        # Get global importance
        importance = explainer.global_feature_importance()
        
        # Check structure
        assert isinstance(importance, dict)
        assert len(importance) == 40
        
        # All features should have importance >= 0
        for feature_name, score in importance.items():
            assert isinstance(feature_name, str)
            assert isinstance(score, float)
            assert score >= 0
        
        # Should be sorted by importance (descending)
        scores = list(importance.values())
        assert scores == sorted(scores, reverse=True)
        
        # Top feature should have highest importance
        top_feature = list(importance.keys())[0]
        assert importance[top_feature] == max(importance.values())
    
    def test_global_importance_save(self, trained_model_and_data, tmp_path):
        """Test saving global feature importance."""
        model, X_train, robot_cfg = trained_model_and_data
        
        explainer = ShapExplainer(model=model, background_data=X_train[:100])
        
        # Save importance
        save_path = tmp_path / "feature_importance.json"
        explainer.save_global_importance(str(save_path))
        
        # Check file exists
        assert save_path.exists()
        
        # Load and verify
        import json
        with open(save_path, 'r') as f:
            loaded_importance = json.load(f)
        
        assert len(loaded_importance) == 40
        assert all(isinstance(v, float) for v in loaded_importance.values())
    
    def test_inference_with_explainer(self, trained_model_and_data):
        """Test inference engine with explainer."""
        model, X_train, robot_cfg = trained_model_and_data
        
        # Create explainer
        explainer = ShapExplainer(model=model, background_data=X_train[:100])
        
        # Create inference engine with explainer
        inference = AnomalyDetectionInference(
            model=model,
            robot_config=robot_cfg,
            explainer=explainer
        )
        
        # Generate test state
        from oculus.anomaly_detection.test_data_generator import SyntheticDataGenerator
        generator = SyntheticDataGenerator(num_joints=12)
        states = generator.generate_normal_episode(duration=1.0)
        
        # Process without explanation
        result_no_explain = inference.process_step(states[10], explain=False)
        assert result_no_explain.shap_values is None
        assert result_no_explain.top_features is None
        
        # Process with explanation
        result_with_explain = inference.process_step(states[20], explain=True)
        assert result_with_explain.shap_values is not None
        assert result_with_explain.top_features is not None
        assert len(result_with_explain.top_features) == 5  # Default top_k
        assert result_with_explain.base_value is not None
    
    def test_anomaly_result_to_dict_with_shap(self, trained_model_and_data):
        """Test AnomalyResult.to_dict with SHAP data."""
        from oculus.anomaly_detection.inference import AnomalyResult
        
        # Create result with SHAP data
        result = AnomalyResult(
            anomaly_score=0.85,
            is_anomaly=True,
            features=np.random.rand(40),
            timestamp=123.45,
            shap_values=np.random.rand(40),
            base_value=0.5,
            top_features=[
                {"rank": 1, "feature_name": "test", "feature_value": 0.9, "shap_value": 0.3}
            ]
        )
        
        # Convert without SHAP
        dict_no_shap = result.to_dict(include_shap=False)
        assert "shap_values" not in dict_no_shap
        assert "top_features" not in dict_no_shap
        assert "anomaly_score" in dict_no_shap
        
        # Convert with SHAP
        dict_with_shap = result.to_dict(include_shap=True)
        assert "shap_values" in dict_with_shap
        assert "base_value" in dict_with_shap
        assert "top_features" in dict_with_shap
        assert len(dict_with_shap["shap_values"]) == 40
        assert dict_with_shap["base_value"] == 0.5
    
    def test_repr(self, trained_model_and_data):
        """Test ShapExplainer __repr__."""
        model, X_train, robot_cfg = trained_model_and_data
        
        explainer = ShapExplainer(model=model, background_data=X_train[:50])
        repr_str = repr(explainer)
        
        assert "ShapExplainer" in repr_str
        assert "40" in repr_str  # n_features
        assert "50" in repr_str  # background samples


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
