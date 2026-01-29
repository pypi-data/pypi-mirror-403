"""MaxQuery - MaxCompute SQL execution CLI"""
__version__ = "1.0.0"
__author__ = "Chethan Patel"
__email__ = "chethanpatel100@gmail.com"

from maxquery.core import MaxQueryRunner
from maxquery.credentials import CredentialsManager

__all__ = ["MaxQueryRunner", "CredentialsManager"]
