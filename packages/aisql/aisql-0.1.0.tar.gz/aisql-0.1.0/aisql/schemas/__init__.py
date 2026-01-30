"""Database schemas package"""

from .postgresql import SCHEMA as POSTGRESQL_SCHEMA
from .mongodb import SCHEMA as MONGODB_SCHEMA

__all__ = ["POSTGRESQL_SCHEMA", "MONGODB_SCHEMA"]
