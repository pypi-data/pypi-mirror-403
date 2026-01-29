"""
Unit tests for IsolationForestModel.
"""

import pytest
import numpy as np
import tempfile
import shutil
from pathlib import Path

from oculus.anomaly_detection.model import IsolationForestModel


class TestIsolationForestModel:
    """Test suite for IsolationForestModel."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.n_samples = 1000
        self.n_features = 40
        self.X_train = np.random.randn(self.n_samples, self.n_features)
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup after tests."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test model initialization."""
        model = IsolationForestModel(n_estimators=100, contamination=0.1)
        
        assert model.n_estimators == 100
        assert model.contamination == 0.1
        assert not model.is_fitted
        assert model.n_features_in_ is None
    
    def test_fit(self):
        """Test model training."""
        model = IsolationForestModel(n_estimators=100)
        model.fit(self.X_train)
        
        assert model.is_fitted
        assert model.n_features_in_ == self.n_features
        assert model.training_samples_ == self.n_samples
    
    def test_fit_invalid_shape(self):
        """Test fit with invalid input shape."""
        model = IsolationForestModel()
        
        with pytest.raises(ValueError):
            model.fit(np.array([1, 2, 3]))  # 1D array
    
    def test_fit_with_nan(self):
        """Test fit rejects NaN values."""
        model = IsolationForestModel()
        X_bad = self.X_train.copy()
        X_bad[0, 0] = np.nan
        
        with pytest.raises(ValueError):
            model.fit(X_bad)
    
    def test_predict_score(self):
        """Test anomaly score prediction."""
        model = IsolationForestModel(n_estimators=100)
        model.fit(self.X_train)
        
        # Single sample
        x_single = self.X_train[0]
        score = model.predict_score(x_single)
        assert isinstance(score, (float, np.floating))
        assert 0.0 <= score <= 1.0
        
        # Batch
        scores = model.predict_score(self.X_train[:10])
        assert scores.shape == (10,)
        assert np.all((scores >= 0) & (scores <= 1))
    
    def test_predict_before_fit(self):
        """Test predict raises error before fitting."""
        model = IsolationForestModel()
        
        with pytest.raises(ValueError):
            model.predict_score(self.X_train[0])
    
    def test_predict_wrong_features(self):
        """Test predict with wrong number of features."""
        model = IsolationForestModel()
        model.fit(self.X_train)
        
        X_wrong = np.random.randn(10, 30)  # Wrong feature count
        
        with pytest.raises(ValueError):
            model.predict_score(X_wrong)
    
    def test_predict_labels(self):
        """Test binary label prediction."""
        model = IsolationForestModel(n_estimators=100)
        model.fit(self.X_train)
        
        labels = model.predict(self.X_train[:10])
        assert labels.shape == (10,)
        assert set(labels).issubset({-1, 1})
    
    def test_save_and_load(self):
        """Test model persistence."""
        # Train model
        model = IsolationForestModel(n_estimators=100, random_state=42)
        model.fit(self.X_train)
        
        # Get predictions
        scores_original = model.predict_score(self.X_train[:10])
        
        # Save
        save_path = Path(self.temp_dir) / "test_model"
        model.save(save_path)
        
        # Check files exist
        assert (save_path / "iforest_model.pkl").exists()
        assert (save_path / "feature_scaler.pkl").exists()
        assert (save_path / "config.json").exists()
        
        # Load
        loaded_model = IsolationForestModel.load(save_path)
        
        # Check metadata
        assert loaded_model.is_fitted
        assert loaded_model.n_features_in_ == self.n_features
        assert loaded_model.n_estimators == 100
        
        # Check predictions match
        scores_loaded = loaded_model.predict_score(self.X_train[:10])
        np.testing.assert_array_almost_equal(scores_original, scores_loaded)
    
    def test_save_before_fit(self):
        """Test save raises error before fitting."""
        model = IsolationForestModel()
        
        with pytest.raises(ValueError):
            model.save(self.temp_dir)
    
    def test_get_params(self):
        """Test parameter retrieval."""
        model = IsolationForestModel(n_estimators=200, contamination=0.05)
        params = model.get_params()
        
        assert params["n_estimators"] == 200
        assert params["contamination"] == 0.05
        assert not params["is_fitted"]
    
    def test_repr(self):
        """Test string representation."""
        model = IsolationForestModel(n_estimators=100)
        repr_str = repr(model)
        
        assert "IsolationForestModel" in repr_str
        assert "not fitted" in repr_str
        
        model.fit(self.X_train)
        repr_str = repr(model)
        assert "fitted" in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
