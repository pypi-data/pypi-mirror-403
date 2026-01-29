"""
Basic tests for FinVista.

Run with: pytest tests/test_basic.py -v
"""

import pytest

import finvista as fv
from finvista._core.exceptions import FinVistaError, ValidationError


class TestImport:
    """Test library import."""

    def test_version(self):
        """Test version is accessible."""
        assert fv.__version__ is not None
        assert isinstance(fv.__version__, str)

    def test_public_api(self):
        """Test public API is accessible."""
        # China Stock Functions
        assert callable(fv.get_cn_stock_daily)
        assert callable(fv.get_cn_stock_quote)
        assert callable(fv.list_cn_stock_symbols)
        assert callable(fv.search_cn_stock)

        # China Index Functions
        assert callable(fv.get_cn_index_daily)
        assert callable(fv.get_cn_index_quote)
        assert callable(fv.list_cn_major_indices)

        # China Fund Functions
        assert callable(fv.get_cn_fund_nav)
        assert callable(fv.get_cn_fund_quote)
        assert callable(fv.list_cn_fund_symbols)
        assert callable(fv.search_cn_fund)
        assert callable(fv.get_cn_fund_info)

        # US Stock Functions
        assert callable(fv.get_us_stock_daily)
        assert callable(fv.get_us_stock_quote)
        assert callable(fv.get_us_stock_info)
        assert callable(fv.search_us_stock)

        # Macro Functions
        assert callable(fv.get_cn_macro_gdp)
        assert callable(fv.get_cn_macro_cpi)
        assert callable(fv.get_cn_macro_ppi)
        assert callable(fv.get_cn_macro_pmi)
        assert callable(fv.get_cn_macro_money_supply)
        assert callable(fv.get_cn_macro_social_financing)

        # Config functions
        assert callable(fv.set_proxies)
        assert callable(fv.set_timeout)
        assert callable(fv.set_cache)
        assert callable(fv.get_source_health)


class TestConfiguration:
    """Test configuration functions."""

    def test_set_timeout(self):
        """Test setting timeout."""
        fv.set_timeout(60)
        assert fv.config.http.timeout == 60
        fv.set_timeout(30)  # Reset

    def test_set_timeout_invalid(self):
        """Test setting invalid timeout."""
        with pytest.raises(fv.ConfigError):
            fv.set_timeout(0)

    def test_set_cache(self):
        """Test cache configuration."""
        fv.set_cache(enabled=True, ttl=600)
        assert fv.config.cache.enabled is True
        assert fv.config.cache.ttl == 600
        fv.set_cache(enabled=True, ttl=300)  # Reset

    def test_source_health(self):
        """Test getting source health."""
        health = fv.get_source_health()
        assert isinstance(health, dict)
        assert "cn_stock_daily" in health


class TestExceptions:
    """Test exception classes."""

    def test_finvista_error(self):
        """Test base exception."""
        with pytest.raises(FinVistaError):
            raise fv.FinVistaError("Test error")

    def test_validation_error(self):
        """Test validation error."""
        with pytest.raises(ValidationError):
            raise fv.ValidationError("Invalid value", param_name="test")

    def test_exception_hierarchy(self):
        """Test exception inheritance."""
        assert issubclass(fv.ValidationError, fv.FinVistaError)
        assert issubclass(fv.NetworkError, fv.FinVistaError)
        assert issubclass(fv.APIError, fv.FinVistaError)
        assert issubclass(fv.RateLimitError, fv.APIError)


class TestValidation:
    """Test input validation."""

    def test_invalid_symbol_format(self):
        """Test invalid symbol format."""
        with pytest.raises(ValidationError):
            fv.get_cn_stock_daily("invalid")

    def test_empty_symbol(self):
        """Test empty symbol."""
        with pytest.raises(ValidationError):
            fv.get_cn_stock_daily("")

    def test_invalid_adjust(self):
        """Test invalid adjust type."""
        with pytest.raises(ValidationError):
            fv.get_cn_stock_daily("000001", adjust="invalid")


class TestMajorIndices:
    """Test major indices listing."""

    def test_list_major_indices(self):
        """Test listing major indices."""
        df = fv.list_cn_major_indices()
        assert len(df) > 0
        assert "symbol" in df.columns
        assert "name" in df.columns


# Integration tests (require network)
class TestIntegration:
    """Integration tests that require network access."""

    @pytest.mark.integration
    def test_get_stock_daily(self):
        """Test fetching daily stock data."""
        df = fv.get_cn_stock_daily("000001", start_date="2024-01-01", end_date="2024-01-10")
        assert len(df) > 0
        assert "date" in df.columns
        assert "close" in df.columns
        assert "source" in df.attrs

    @pytest.mark.integration
    def test_list_stock_symbols(self):
        """Test listing stock symbols."""
        df = fv.list_cn_stock_symbols(market="main")
        assert len(df) > 0
        assert "symbol" in df.columns
        assert "name" in df.columns

    @pytest.mark.integration
    def test_get_stock_quote(self):
        """Test fetching real-time quotes."""
        df = fv.get_cn_stock_quote(["000001", "600519"])
        assert len(df) > 0
        assert "symbol" in df.columns
        assert "price" in df.columns

    @pytest.mark.integration
    def test_search_stock(self):
        """Test searching for stocks."""
        df = fv.search_cn_stock("银行")
        assert len(df) > 0
        assert "symbol" in df.columns
        assert "name" in df.columns

    @pytest.mark.integration
    def test_get_index_daily(self):
        """Test fetching index daily data."""
        df = fv.get_cn_index_daily("000001", start_date="2024-01-01", end_date="2024-01-10")
        assert len(df) > 0
        assert "date" in df.columns
        assert "close" in df.columns

    @pytest.mark.integration
    def test_get_fund_nav(self):
        """Test fetching fund NAV data."""
        # Use 110011 (易方达中小盘混合) - a popular fund
        df = fv.get_cn_fund_nav("110011", start_date="2024-01-01", end_date="2024-01-31")
        assert len(df) > 0
        assert "date" in df.columns
        assert "nav" in df.columns

    @pytest.mark.integration
    def test_list_fund_symbols(self):
        """Test listing fund symbols."""
        df = fv.list_cn_fund_symbols(fund_type="stock")
        assert len(df) > 0
        assert "symbol" in df.columns
        assert "name" in df.columns

    @pytest.mark.integration
    def test_get_us_stock_daily(self):
        """Test fetching US stock data."""
        df = fv.get_us_stock_daily("AAPL", start_date="2024-01-01", end_date="2024-01-10")
        assert len(df) > 0
        assert "date" in df.columns
        assert "close" in df.columns

    @pytest.mark.integration
    def test_get_macro_gdp(self):
        """Test fetching GDP data."""
        df = fv.get_cn_macro_gdp()
        assert len(df) > 0
        assert "date" in df.columns
        assert "gdp" in df.columns

    @pytest.mark.integration
    def test_get_macro_cpi(self):
        """Test fetching CPI data."""
        df = fv.get_cn_macro_cpi()
        assert len(df) > 0
        assert "date" in df.columns
        assert "cpi" in df.columns
