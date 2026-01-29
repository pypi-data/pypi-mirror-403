"""
Dredd Core - DA-BFT Tribunal Engine
Divergent Arbiter Byzantine Fault Tolerance for multi-model consensus.
"""

__version__ = "0.1.0"

from dredd_core.engine import (
    DabftEngine,
    ModelConfig,
    Prompts,
    ContextManager,
    Lazarus,
    PersonaManager,
    AppHealingManager,
)

__all__ = [
    "DabftEngine",
    "ModelConfig",
    "Prompts",
    "ContextManager",
    "Lazarus",
    "PersonaManager",
    "AppHealingManager",
    "__version__",
]
