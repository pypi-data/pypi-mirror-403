import logging

# Create a logger object for the module.
logger = logging.getLogger("GenericPSO")

# Setup basic configuration for now.
logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s",
                    datefmt="%m/%d/%Y %H:%M:%S", level=logging.INFO)

# Public interface.
__all__ = ["logger"]
