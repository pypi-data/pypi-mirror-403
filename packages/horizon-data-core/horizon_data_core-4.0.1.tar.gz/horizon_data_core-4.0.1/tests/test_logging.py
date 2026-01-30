import logging
import pytest
from unittest.mock import Mock
from horizon_data_core.logging import setup_extra_logger, log_calls


def test_setup_extra_logger() -> None:
    """Test that setup_extra_logger returns a logger."""
    logger = setup_extra_logger()
    assert isinstance(logger, logging.Logger)


def test_log_calls_exception() -> None:
    """Test that log_calls decorator logs exceptions and re-raises them."""
    mock_logger = Mock(spec=logging.Logger)
    
    @log_calls(mock_logger, logging.INFO)
    def failing_function() -> None:
        raise ValueError("Test error")
    
    # Call the decorated function and verify exception is raised
    with pytest.raises(ValueError, match="Test error"):
        failing_function()
    
    # Verify exception was logged
    assert mock_logger.log.called
    # Check that ERROR log was called with exception details
    error_calls = [call for call in mock_logger.log.call_args_list if "ERROR" in str(call)]
    assert len(error_calls) > 0