#!/usr/bin/env python3
"""
Python API for telert - Send Telegram alerts from Python code.

This module provides functions to send Telegram notifications directly from Python.
It shares the same configuration as the CLI tool.

Usage:
    from telert import telert, send
    
    # Send a simple notification
    send("My script finished processing")
    
    # Use with a context manager to time execution
    with telert("Long computation"):
        # Your code here
        result = compute_something_expensive()
    
    # The notification will be sent when the block exits,
    # including the execution time.
"""
from __future__ import annotations

import time
import traceback
import contextlib
import functools
from typing import Optional, Any, Callable, Union, TypeVar, cast

from telert.cli import _send, _load, _human

# Type variable for function return type
T = TypeVar('T')

def send(message: str) -> None:
    """
    Send a Telegram message using telert configuration.
    
    Args:
        message: The message text to send
    """
    _send(message)

class telert:
    """
    Context manager for sending Telegram notifications.
    
    When used as a context manager, it will time the code execution and 
    send a notification when the block exits, including the execution time
    and any exceptions that were raised.
    
    Examples:
        # Basic usage with default message
        with telert():
            do_something_lengthy()
        
        # Custom message
        with telert("Database backup"):
            backup_database()
        
        # Handle return value
        with telert("Processing data") as t:
            result = process_data()
            t.result = result  # This will be included in the notification
    """
    
    def __init__(
        self, 
        label: Optional[str] = None, 
        only_fail: bool = False, 
        include_traceback: bool = True,
        callback: Optional[Callable[[str], Any]] = None
    ):
        """
        Initialize a telert context manager.
        
        Args:
            label: Optional label to identify this operation in the notification
            only_fail: If True, only send notification on failure (exception)
            include_traceback: If True, include traceback in notification when an exception occurs
            callback: Optional callback function to run with the notification message
        """
        self.label = label or "Python task"
        self.only_fail = only_fail
        self.include_traceback = include_traceback
        self.callback = callback
        self.result = None
        self.start_time = None
        self.exception = None
        
    def __enter__(self):
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = _human(time.time() - self.start_time)
        
        if exc_type is not None:
            self.exception = exc_val
            status = "failed"
            
            if self.include_traceback:
                tb = "".join(traceback.format_exception(exc_type, exc_val, exc_tb))
                message = f"{self.label} {status} in {duration}\n\n--- traceback ---\n{tb}"
            else:
                message = f"{self.label} {status} in {duration}: {exc_val}"
                
            _send(message)
            return False  # Re-raise the exception
            
        status = "completed"
        
        # Only send notification on success if only_fail is False
        if not self.only_fail:
            message = f"{self.label} {status} in {duration}"
            
            # Include the result if it was set
            if self.result is not None:
                result_str = str(self.result)
                if len(result_str) > 1000:
                    result_str = result_str[:997] + "..."
                message += f"\n\n--- result ---\n{result_str}"
                
            _send(message)
            
        # If a callback was provided, call it with the message
        if self.callback and not self.only_fail:
            self.callback(message)
            
        return False
        
        
def notify(
    label: Optional[str] = None,
    only_fail: bool = False,
    include_traceback: bool = True
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to send Telegram notifications when a function completes.
    
    Args:
        label: Optional label to identify this operation in the notification
        only_fail: If True, only send notification on failure (exception)
        include_traceback: If True, include traceback in notification when an exception occurs
        
    Returns:
        A decorator function
        
    Examples:
        @notify("Database backup")
        def backup_database():
            # Your code here
            
        @notify(only_fail=True)
        def critical_operation():
            # Your code here
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Use the function name if no label is provided
            func_label = label or func.__name__
            
            with telert(func_label, only_fail, include_traceback) as t:
                result = func(*args, **kwargs)
                t.result = result
                return result
                
        return wrapper
    
    return decorator