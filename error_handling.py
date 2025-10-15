"""
Error handling and logging framework for MicroMelon Rover Control System
Provides centralized logging, retry logic, and graceful error recovery.
"""

import logging
import functools
import time
import traceback
import sys
from typing import Any, Callable, Optional, Dict, List
from pathlib import Path
from datetime import datetime
from config import RoverConfig


class RoverLogger:
    """Centralized logging system for rover operations"""
    
    def __init__(self, config: RoverConfig):
        self.config = config
        self.loggers = {}
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration based on config"""
        # Clear existing handlers to avoid duplicates
        logging.getLogger().handlers.clear()
        
        # Set log level
        level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        logging.getLogger().setLevel(level)
        
        # Create formatter
        formatter = logging.Formatter(
            fmt='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler (always present)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        logging.getLogger().addHandler(console_handler)
        
        # File handler (if enabled)
        if self.config.log_to_file:
            try:
                # Ensure log directory exists
                log_path = Path(self.config.log_file_path)
                log_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Create rotating file handler
                from logging.handlers import RotatingFileHandler
                file_handler = RotatingFileHandler(
                    self.config.log_file_path,
                    maxBytes=self.config.max_log_size,
                    backupCount=5,
                    encoding='utf-8'
                )
                file_handler.setFormatter(formatter)
                file_handler.setLevel(level)
                logging.getLogger().addHandler(file_handler)
                
            except Exception as e:
                print(f"Warning: Could not setup file logging: {e}")
        
        # Log startup info
        logger = self.get_logger("RoverLogger")
        logger.info("=" * 60)
        logger.info("MicroMelon Rover Control System Started")
        logger.info(f"Log level: {self.config.log_level}")
        logger.info(f"File logging: {'Enabled' if self.config.log_to_file else 'Disabled'}")
        logger.info("=" * 60)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get or create a named logger"""
        if name not in self.loggers:
            self.loggers[name] = logging.getLogger(name)
        return self.loggers[name]


class RoverException(Exception):
    """Base exception for rover-related errors"""
    def __init__(self, message: str, error_code: str = None, recoverable: bool = True):
        super().__init__(message)
        self.error_code = error_code or "ROVER_ERROR"
        self.recoverable = recoverable
        self.timestamp = datetime.now()


class ConnectionError(RoverException):
    """Rover connection related errors"""
    def __init__(self, message: str, connection_type: str = "unknown"):
        super().__init__(message, "CONNECTION_ERROR", recoverable=True)
        self.connection_type = connection_type


class SensorError(RoverException):
    """Sensor reading related errors"""
    def __init__(self, message: str, sensor_type: str = "unknown"):
        super().__init__(message, "SENSOR_ERROR", recoverable=True)
        self.sensor_type = sensor_type


class SafetyError(RoverException):
    """Safety system related errors"""
    def __init__(self, message: str):
        super().__init__(message, "SAFETY_ERROR", recoverable=False)


def retry_on_failure(max_attempts: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)):
    """
    Decorator to retry function calls on failure
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Delay between retries in seconds
        exceptions: Tuple of exception types to retry on
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__name__)
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                    
                except exceptions as e:
                    if attempt == max_attempts - 1:
                        logger.error(f"Function {func.__name__} failed after {max_attempts} attempts: {e}")
                        raise
                    
                    logger.warning(f"Attempt {attempt + 1}/{max_attempts} failed: {e}")
                    if delay > 0:
                        logger.info(f"Retrying in {delay}s...")
                        time.sleep(delay)
                        
                except Exception as e:
                    # Don't retry on unexpected exceptions
                    logger.error(f"Unexpected error in {func.__name__}: {e}")
                    raise
                    
        return wrapper
    return decorator


def handle_exceptions(default_return=None, log_traceback: bool = True):
    """
    Decorator to handle exceptions gracefully with logging
    
    Args:
        default_return: Value to return if exception occurs
        log_traceback: Whether to log full traceback
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__name__)
            
            try:
                return func(*args, **kwargs)
            except RoverException as e:
                logger.error(f"Rover error in {func.__name__}: {e}")
                if log_traceback:
                    logger.debug(f"Traceback: {traceback.format_exc()}")
                return default_return
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {e}")
                if log_traceback:
                    logger.error(f"Traceback: {traceback.format_exc()}")
                return default_return
                
        return wrapper
    return decorator


class ErrorRecoveryManager:
    """Manages error recovery strategies"""
    
    def __init__(self, config: RoverConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.error_history: List[Dict] = []
        self.recovery_strategies = {
            'CONNECTION_ERROR': self._recover_connection,
            'SENSOR_ERROR': self._recover_sensor,
            'SAFETY_ERROR': self._emergency_stop,
        }
    
    def handle_error(self, error: RoverException, context: Dict = None) -> bool:
        """
        Handle an error using appropriate recovery strategy
        
        Args:
            error: The rover exception that occurred
            context: Additional context about the error
            
        Returns:
            bool: True if recovery was successful, False otherwise
        """
        self.logger.error(f"Handling error: {error.error_code} - {error}")
        
        # Record error in history
        error_record = {
            'timestamp': error.timestamp,
            'error_code': error.error_code,
            'message': str(error),
            'recoverable': error.recoverable,
            'context': context or {}
        }
        self.error_history.append(error_record)
        
        # Limit error history size
        if len(self.error_history) > 100:
            self.error_history = self.error_history[-50:]  # Keep last 50 errors
        
        # Try recovery if error is recoverable
        if error.recoverable and error.error_code in self.recovery_strategies:
            try:
                return self.recovery_strategies[error.error_code](error, context)
            except Exception as e:
                self.logger.error(f"Recovery strategy failed: {e}")
                return False
        
        return False
    
    def _recover_connection(self, error: ConnectionError, context: Dict) -> bool:
        """Attempt to recover from connection errors"""
        self.logger.info("Attempting connection recovery...")
        
        # Give some time before retry
        time.sleep(2.0)
        
        # This would be implemented by the specific controller
        # For now, just log the attempt
        self.logger.info("Connection recovery attempted")
        return False  # Let the controller handle actual recovery
    
    def _recover_sensor(self, error: SensorError, context: Dict) -> bool:
        """Attempt to recover from sensor errors"""
        self.logger.info(f"Attempting sensor recovery for {error.sensor_type}")
        
        # Clear any cached sensor values
        # Wait a bit for sensor to stabilize
        time.sleep(0.5)
        
        self.logger.info("Sensor recovery attempted")
        return True  # Assume sensors can recover
    
    def _emergency_stop(self, error: SafetyError, context: Dict) -> bool:
        """Handle safety errors with emergency stop"""
        self.logger.critical(f"EMERGENCY STOP triggered: {error}")
        
        # This would trigger emergency stop in the controller
        # For now, just log
        self.logger.critical("EMERGENCY STOP procedures should be activated")
        return False  # Safety errors are not recoverable
    
    def get_error_summary(self) -> Dict:
        """Get summary of recent errors"""
        if not self.error_history:
            return {'total_errors': 0, 'recent_errors': 0, 'error_types': {}}
        
        # Count errors by type
        error_types = {}
        recent_errors = 0
        cutoff_time = datetime.now().timestamp() - 300  # Last 5 minutes
        
        for error in self.error_history:
            error_code = error['error_code']
            error_types[error_code] = error_types.get(error_code, 0) + 1
            
            if error['timestamp'].timestamp() > cutoff_time:
                recent_errors += 1
        
        return {
            'total_errors': len(self.error_history),
            'recent_errors': recent_errors,
            'error_types': error_types,
            'last_error': self.error_history[-1] if self.error_history else None
        }


class PerformanceMonitor:
    """Monitor system performance and log issues"""
    
    def __init__(self, config: RoverConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.enabled = config.enable_performance_monitoring
        
        if self.enabled:
            self.frame_times = []
            self.start_time = time.time()
            self.frame_count = 0
    
    def start_frame(self) -> float:
        """Mark the start of a frame and return timestamp"""
        if not self.enabled:
            return time.time()
        return time.time()
    
    def end_frame(self, start_time: float) -> float:
        """Mark the end of a frame and return duration"""
        if not self.enabled:
            return 0.0
            
        duration = time.time() - start_time
        self.frame_times.append(duration)
        self.frame_count += 1
        
        # Keep only recent frame times
        if len(self.frame_times) > 100:
            self.frame_times = self.frame_times[-50:]
        
        # Log performance warnings
        if duration > self.config.frame_skip_threshold:
            self.logger.warning(f"Slow frame processing: {duration:.3f}s")
        
        # Log periodic performance summary
        if self.frame_count % 100 == 0:
            self.log_performance_summary()
        
        return duration
    
    def log_performance_summary(self):
        """Log performance summary"""
        if not self.enabled or not self.frame_times:
            return
            
        avg_time = sum(self.frame_times) / len(self.frame_times)
        max_time = max(self.frame_times)
        min_time = min(self.frame_times)
        
        avg_fps = 1.0 / avg_time if avg_time > 0 else 0
        
        self.logger.info(f"Performance Summary:")
        self.logger.info(f"  Average FPS: {avg_fps:.1f}")
        self.logger.info(f"  Frame time - Avg: {avg_time*1000:.1f}ms, Min: {min_time*1000:.1f}ms, Max: {max_time*1000:.1f}ms")
        self.logger.info(f"  Total frames processed: {self.frame_count}")


# Global error recovery manager instance
_error_manager = None

def get_error_manager(config: RoverConfig = None) -> ErrorRecoveryManager:
    """Get the global error recovery manager instance"""
    global _error_manager
    if _error_manager is None:
        if config is None:
            config = RoverConfig()
        _error_manager = ErrorRecoveryManager(config)
    return _error_manager


def setup_global_logging(config: RoverConfig) -> RoverLogger:
    """Setup global logging system"""
    return RoverLogger(config)


if __name__ == "__main__":
    # Test the error handling system
    print("Testing MicroMelon Rover Error Handling System")
    print("=" * 50)
    
    # Setup logging
    config = RoverConfig()
    logger_system = setup_global_logging(config)
    logger = logger_system.get_logger("ErrorHandlingTest")
    
    # Test error manager
    error_manager = get_error_manager(config)
    
    # Test different error types
    logger.info("Testing error handling...")
    
    # Test connection error
    conn_error = ConnectionError("Failed to connect to BLE device", "BLE")
    error_manager.handle_error(conn_error, {'port': 1234})
    
    # Test sensor error
    sensor_error = SensorError("Ultrasonic sensor timeout", "ultrasonic")
    error_manager.handle_error(sensor_error, {'last_value': 25.5})
    
    # Test retry decorator
    @retry_on_failure(max_attempts=2, delay=0.1)
    def failing_function():
        logger.info("Attempting operation...")
        raise Exception("Simulated failure")
    
    try:
        failing_function()
    except Exception as e:
        logger.info(f"Function failed as expected: {e}")
    
    # Test performance monitor
    perf_monitor = PerformanceMonitor(config)
    
    start = perf_monitor.start_frame()
    time.sleep(0.01)  # Simulate work
    duration = perf_monitor.end_frame(start)
    logger.info(f"Frame processing took {duration*1000:.1f}ms")
    
    # Get error summary
    summary = error_manager.get_error_summary()
    logger.info(f"Error summary: {summary}")
    
    logger.info("Error handling system test complete")