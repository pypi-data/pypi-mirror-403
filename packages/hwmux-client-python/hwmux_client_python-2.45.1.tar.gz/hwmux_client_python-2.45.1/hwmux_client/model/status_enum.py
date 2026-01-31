"""
Backward compatibility module for StatusEnum.

This module provides backward compatibility after StatusEnum was renamed to StatusF44Enum
due to naming collision detection in OpenAPI Generator.

DEPRECATED: Use StatusF44Enum directly from status_f44_enum module instead.
This compatibility layer will be removed in a future major version.
"""

# Re-export StatusF44Enum as StatusEnum for backward compatibility
from hwmux_client.model.status_f44_enum import StatusF44Enum as StatusEnum

__all__ = ['StatusEnum']
