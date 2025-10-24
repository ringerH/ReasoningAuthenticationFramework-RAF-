import logging
import os
import sys
from datetime import datetime ## Added import
from typing import Optional   ## Added import

_configured_logger = None
_run_timestamp = None

def setup_logger(run_timestamp_str: Optional[str] = None) -> logging.Logger:
    
    global _configured_logger, _run_timestamp
    if _configured_logger:
        
        return _configured_logger

   
    if run_timestamp_str is None:
        
        if _run_timestamp is None:
             _run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") 
        run_timestamp_to_use = _run_timestamp 
    else:
        _run_timestamp = run_timestamp_str
        run_timestamp_to_use = run_timestamp_str


    log_dir = "logs"
    log_file = os.path.join(log_dir, f"benchmark_{run_timestamp_to_use}.log")

    try:
        os.makedirs(log_dir, exist_ok=True)
    except OSError as e:
        print(f"CRITICAL: Could not create log directory {log_dir}. {e}")
        sys.exit(1) # Exit if we can't create log dir

    log_format = (
        "%(asctime)s [%(levelname)s] (%(name)s | %(filename)s:%(lineno)d): %(message)s"
    )
    formatter = logging.Formatter(log_format)

    logger_instance = logging.getLogger()
    if logger_instance.hasHandlers():
        logger_instance.handlers.clear()

    logger_instance.setLevel(logging.INFO) # Set the minimum level to log

    try:
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO) # Log info and above to file
        logger_instance.addHandler(file_handler)
    except IOError as e:
        print(f"CRITICAL: Could not open log file {log_file} for writing. {e}")
        # Continue with just console logging if file fails, but log the error

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO) # Log info and above to console
    logger_instance.addHandler(console_handler)

    _configured_logger = logger_instance # Store the configured instance
    _configured_logger.info(f"Logger initialized. Logging to console and {log_file}")
    return _configured_logger

def get_logger() -> logging.Logger:   
    if _configured_logger is None:
        return setup_logger()
    return _configured_logger

def get_run_timestamp() -> Optional[str]:
    get_logger()
    return _run_timestamp


if __name__ == "__main__":
    test_logger = setup_logger("selftest_run")
    print(f"--- [Logger Self-Test: {get_run_timestamp()}] ---")

    test_logger.debug("This is a DEBUG message. (Should not appear unless level is DEBUG)")
    test_logger.info("This is an INFO message.")
    test_logger.warning("This is a WARNING message.")
    test_logger.error("This is an ERROR message.")
    test_logger.critical("This is a CRITICAL message.")
    print("--- [Self-Test Complete] ---")