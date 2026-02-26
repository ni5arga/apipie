from __future__ import annotations

import re

_DELETE = re.compile(r'\b(delete|remove|destroy|purge|revoke|unsubscribe)\b', re.I)
_PATCH  = re.compile(r'\b(update|edit|patch|modify|change|rename)\b', re.I)
_POST   = re.compile(
    r'\b(send|create|add|submit|login|signin|signup|register|upload|save|'
    r'generate|otp|verify|validate|authenticate|token|captcha|push|'
    r'notify|invite|assign|import|enable|disable|reset|activate|'
    r'deactivate|confirm|checkout|subscribe|search|query)\b',
    re.I,
)


def infer_method(url: str) -> str:
    segments = url.split("?")[0].split("/")
    path = "-".join(s for s in segments if s).lower()
    if _DELETE.search(path):
        return "DELETE"
    if _PATCH.search(path):
        return "PATCH"
    if _POST.search(path):
        return "POST"
    return "GET"
