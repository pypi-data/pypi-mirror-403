from dataclasses import dataclass
from typing import Callable
from .redaction import default_redactor

@dataclass(frozen=True)
class SafetyMode:
    name: str
    redaction: Callable[[str], str]
    allow_external_network: bool
    allow_cloud_models: bool
    require_signed_audit: bool

@dataclass(frozen=True)
class EnterpriseSafetyMode(SafetyMode):
    @staticmethod
    def default():
        return EnterpriseSafetyMode("enterprise", default_redactor, True, True, True)

@dataclass(frozen=True)
class GovernmentSafetyMode(SafetyMode):
    @staticmethod
    def default():
        return GovernmentSafetyMode("government", default_redactor, False, False, True)
