"""Tests for the paxx bundled features system."""

import shutil
from pathlib import Path

import pytest

from paxx.templates.features import (
    get_feature_dir,
    get_features_dir,
    list_available_features,
)


class TestFeaturesModule:
    """Tests for the features module utilities."""

    def test_get_features_dir_returns_path(self):
        """Test that get_features_dir returns a valid path."""
        features_dir = get_features_dir()
        assert isinstance(features_dir, Path)
        assert features_dir.exists()
        assert features_dir.is_dir()

    def test_get_feature_dir_returns_none_for_nonexistent(self):
        """Test that get_feature_dir returns None for non-existent features."""
        result = get_feature_dir("nonexistent_feature_xyz")
        assert result is None

    def test_list_available_features_returns_list(self):
        """Test that list_available_features returns a list."""
        features = list_available_features()
        assert isinstance(features, list)

    def test_list_available_features_excludes_private(self):
        """Test that private directories are excluded from features list."""
        features = list_available_features()
        for feature in features:
            assert not feature.startswith("_")
            assert not feature.startswith(".")

    @pytest.fixture
    def mock_feature(self):
        """Create a mock feature for testing."""
        features_dir = get_features_dir()
        feature_dir = features_dir / "mock_test_feature"
        feature_dir.mkdir(exist_ok=True)
        (feature_dir / "__init__.py").write_text('"""Mock feature."""\n')

        yield feature_dir

        # Cleanup
        shutil.rmtree(feature_dir)

    def test_get_feature_dir_finds_existing_feature(self, mock_feature):
        """Test that get_feature_dir finds an existing feature."""
        result = get_feature_dir("mock_test_feature")
        assert result is not None
        assert result == mock_feature

    def test_list_available_features_finds_feature(self, mock_feature):
        """Test that list_available_features finds the mock feature."""
        features = list_available_features()
        assert "mock_test_feature" in features

    def test_list_available_features_is_sorted(self, mock_feature):
        """Test that list_available_features returns sorted list."""
        features = list_available_features()
        assert features == sorted(features)
