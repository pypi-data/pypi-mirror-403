
import sys
import os
import pytest
from unittest.mock import patch

# Add scripts directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../.ontos/scripts')))

from ontos_config import PROJECT_ROOT, SKIP_PATTERNS
from ontos_config_defaults import is_ontos_repo

def test_is_ontos_repo_contributor_mode():
    with patch("os.path.exists") as mock_exists:
        # Mock .ontos-internal existing
        def side_effect(path):
            return '.ontos-internal' in path
        mock_exists.side_effect = side_effect
        assert is_ontos_repo() is True

def test_is_ontos_repo_user_mode():
    with patch("os.path.exists", return_value=False):
        assert is_ontos_repo() is False

def test_skip_patterns_contains_archive():
    assert any('archive/' in p for p in SKIP_PATTERNS)


# =============================================================================
# v2.4: Mode Resolution Tests
# =============================================================================

class TestResolveConfig:
    """Tests for resolve_config() mode-aware configuration resolution."""
    
    def test_resolve_config_import(self):
        """Verify resolve_config is importable."""
        from ontos.core.paths import resolve_config
        assert callable(resolve_config)
    
    def test_resolve_config_mode_preset_automated(self):
        """Test that automated mode preset returns correct values."""
        from ontos.core.paths import resolve_config
        from ontos_config_defaults import MODE_PRESETS
        
        # Verify preset exists and has expected values
        assert 'automated' in MODE_PRESETS
        assert MODE_PRESETS['automated']['AUTO_ARCHIVE_ON_PUSH'] == True
        assert MODE_PRESETS['automated']['ENFORCE_ARCHIVE_BEFORE_PUSH'] == False
        assert MODE_PRESETS['automated']['REQUIRE_SOURCE_IN_LOGS'] == False
    
    def test_resolve_config_mode_preset_prompted(self):
        """Test that prompted mode preset returns correct values."""
        from ontos_config_defaults import MODE_PRESETS
        
        assert 'prompted' in MODE_PRESETS
        assert MODE_PRESETS['prompted']['AUTO_ARCHIVE_ON_PUSH'] == False
        assert MODE_PRESETS['prompted']['ENFORCE_ARCHIVE_BEFORE_PUSH'] == True
        assert MODE_PRESETS['prompted']['REQUIRE_SOURCE_IN_LOGS'] == True
    
    def test_resolve_config_mode_preset_advisory(self):
        """Test that advisory mode preset returns correct values."""
        from ontos_config_defaults import MODE_PRESETS
        
        assert 'advisory' in MODE_PRESETS
        assert MODE_PRESETS['advisory']['AUTO_ARCHIVE_ON_PUSH'] == False
        assert MODE_PRESETS['advisory']['ENFORCE_ARCHIVE_BEFORE_PUSH'] == False
        assert MODE_PRESETS['advisory']['REQUIRE_SOURCE_IN_LOGS'] == False
    
    def test_resolve_config_default_fallback(self):
        """Test that default parameter is used when setting not found."""
        from ontos.core.paths import resolve_config
        
        result = resolve_config('NON_EXISTENT_SETTING', 'my_default')
        assert result == 'my_default'
    
    def test_valid_modes_set(self):
        """Test VALID_MODES contains all mode names."""
        from ontos_config_defaults import VALID_MODES, MODE_PRESETS
        
        assert VALID_MODES == set(MODE_PRESETS.keys())
        assert 'automated' in VALID_MODES
        assert 'prompted' in VALID_MODES
        assert 'advisory' in VALID_MODES

