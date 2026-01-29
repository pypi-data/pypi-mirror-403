"""
Utilities for thread management in the plugin runtime.
"""
import threading

# Thread-local storage to track if we're in a managed worker thread
# This is more reliable than checking thread names
_thread_local = threading.local()


def is_managed_worker_thread() -> bool:
    """
    Check if the current thread is a managed worker thread.
    Returns True if running in a @managed_inbound_processing or @managed_outbound_processing worker.
    
    This is set by the decorator worker functions and is more reliable than checking thread names.
    """
    return getattr(_thread_local, 'is_managed_worker', False)


def set_managed_worker_thread(is_worker: bool):
    """
    Set the flag indicating whether the current thread is a managed worker thread.
    
    This should only be called by the managed processing decorator worker functions.
    """
    _thread_local.is_managed_worker = is_worker
