"""
Unit tests for finlearner.portfolio module.
"""
import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
from finlearner.portfolio import PortfolioOptimizer


class TestPortfolioOptimizer:
    """Tests for the PortfolioOptimizer class."""
    
    @patch('yfinance.download')
    def test_init_downloads_data(self, mock_download, sample_multi_ticker_data):
        """Test that initialization downloads and processes data."""
        # Create multi-level columns like yfinance returns
        mock_data = pd.DataFrame({
            ('Adj Close', 'AAPL'): sample_multi_ticker_data['AAPL'],
            ('Adj Close', 'GOOG'): sample_multi_ticker_data['GOOG'],
            ('Adj Close', 'MSFT'): sample_multi_ticker_data['MSFT'],
        }, index=sample_multi_ticker_data.index)
        mock_download.return_value = mock_data
        
        optimizer = PortfolioOptimizer(
            tickers=['AAPL', 'GOOG', 'MSFT'],
            start='2023-01-01',
            end='2023-04-10'
        )
        
        mock_download.assert_called_once()
        assert optimizer.data is not None
        assert optimizer.returns is not None
    
    @patch('yfinance.download')
    def test_optimize_returns_correct_structure(self, mock_download, sample_multi_ticker_data):
        """Test that optimize() returns results, allocation, and metrics."""
        mock_data = pd.DataFrame({
            ('Adj Close', 'AAPL'): sample_multi_ticker_data['AAPL'],
            ('Adj Close', 'GOOG'): sample_multi_ticker_data['GOOG'],
            ('Adj Close', 'MSFT'): sample_multi_ticker_data['MSFT'],
        }, index=sample_multi_ticker_data.index)
        mock_download.return_value = mock_data
        
        optimizer = PortfolioOptimizer(
            tickers=['AAPL', 'GOOG', 'MSFT'],
            start='2023-01-01',
            end='2023-04-10'
        )
        
        results, allocation, metrics = optimizer.optimize(num_portfolios=100)
        
        # Results should be (3, num_portfolios) - volatility, return, sharpe
        assert results.shape == (3, 100)
        
        # Allocation should be a DataFrame
        assert isinstance(allocation, pd.DataFrame)
        assert 'allocation' in allocation.columns
        
        # Metrics should be a tuple (volatility, return)
        assert isinstance(metrics, tuple)
        assert len(metrics) == 2
    
    @patch('yfinance.download')
    def test_optimize_weights_sum_to_one(self, mock_download, sample_multi_ticker_data):
        """Test that portfolio weights sum to 1."""
        mock_data = pd.DataFrame({
            ('Adj Close', 'AAPL'): sample_multi_ticker_data['AAPL'],
            ('Adj Close', 'GOOG'): sample_multi_ticker_data['GOOG'],
            ('Adj Close', 'MSFT'): sample_multi_ticker_data['MSFT'],
        }, index=sample_multi_ticker_data.index)
        mock_download.return_value = mock_data
        
        optimizer = PortfolioOptimizer(
            tickers=['AAPL', 'GOOG', 'MSFT'],
            start='2023-01-01',
            end='2023-04-10'
        )
        
        results, allocation, metrics = optimizer.optimize(num_portfolios=50)
        
        # Weights should sum to approximately 1
        total_weight = allocation['allocation'].sum()
        assert np.isclose(total_weight, 1.0, atol=0.01)
    
    @patch('yfinance.download')
    def test_optimize_sharpe_ratio_calculated(self, mock_download, sample_multi_ticker_data):
        """Test that Sharpe ratio is correctly calculated."""
        mock_data = pd.DataFrame({
            ('Adj Close', 'AAPL'): sample_multi_ticker_data['AAPL'],
            ('Adj Close', 'GOOG'): sample_multi_ticker_data['GOOG'],
            ('Adj Close', 'MSFT'): sample_multi_ticker_data['MSFT'],
        }, index=sample_multi_ticker_data.index)
        mock_download.return_value = mock_data
        
        optimizer = PortfolioOptimizer(
            tickers=['AAPL', 'GOOG', 'MSFT'],
            start='2023-01-01',
            end='2023-04-10'
        )
        
        results, allocation, metrics = optimizer.optimize(num_portfolios=100)
        
        # Sharpe ratios should be return / volatility
        for i in range(100):
            if results[0, i] != 0:  # Avoid division by zero
                expected_sharpe = results[1, i] / results[0, i]
                assert np.isclose(results[2, i], expected_sharpe, atol=0.001)
    
    @patch('yfinance.download')
    def test_optimize_finds_max_sharpe(self, mock_download, sample_multi_ticker_data):
        """Test that the allocation corresponds to max Sharpe ratio portfolio."""
        mock_data = pd.DataFrame({
            ('Adj Close', 'AAPL'): sample_multi_ticker_data['AAPL'],
            ('Adj Close', 'GOOG'): sample_multi_ticker_data['GOOG'],
            ('Adj Close', 'MSFT'): sample_multi_ticker_data['MSFT'],
        }, index=sample_multi_ticker_data.index)
        mock_download.return_value = mock_data
        
        optimizer = PortfolioOptimizer(
            tickers=['AAPL', 'GOOG', 'MSFT'],
            start='2023-01-01',
            end='2023-04-10'
        )
        
        results, allocation, metrics = optimizer.optimize(num_portfolios=100)
        
        # The returned metrics should correspond to max Sharpe ratio
        max_sharpe_idx = np.argmax(results[2])
        assert metrics[0] == results[0, max_sharpe_idx]  # volatility
        assert metrics[1] == results[1, max_sharpe_idx]  # return
