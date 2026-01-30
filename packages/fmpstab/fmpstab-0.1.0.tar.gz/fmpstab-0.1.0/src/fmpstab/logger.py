import os
import sys
import logging
from typing import Optional

class Logger:
    def __init__(self, name: str = "FMPStabLogger", log_file: Optional[str] = None, 
                 level: int = logging.INFO, enabled: bool = True) -> None:
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        if log_file is None:
            if "__main__" in sys.modules and hasattr(sys.modules["__main__"], "__file__"):
                main_dir = os.path.dirname(sys.modules["__main__"].__file__)
            else:
                main_dir = os.getcwd()
            log_file = os.path.join(main_dir, "fmpstab.log")
        if enabled:
            handler = logging.FileHandler(log_file)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        else:
            self.logger.addHandler(logging.NullHandler())

    def info(self, message: str) -> None:
        self.logger.info(message)

    def error(self, message: str) -> None:
        self.logger.error(message)
