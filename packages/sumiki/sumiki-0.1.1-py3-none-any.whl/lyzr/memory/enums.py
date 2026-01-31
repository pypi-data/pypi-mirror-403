"""
Enums for Memory module
"""

from enum import Enum


class MemoryProvider(str, Enum):
    """Supported memory provider types"""
    LYZR = "lyzr"
    AWS_AGENTCORE = "aws-agentcore"
    MEM0 = "mem0"
    SUPERMEMORY = "supermemory"


class MemoryStatus(str, Enum):
    """Memory connection status"""
    PENDING = "pending"
    VALIDATING = "validating"
    ACTIVE = "active"
    FAILED = "failed"
    CREATING = "creating"  # AWS AgentCore only
    VALIDATED = "validated"  # After successful validation
