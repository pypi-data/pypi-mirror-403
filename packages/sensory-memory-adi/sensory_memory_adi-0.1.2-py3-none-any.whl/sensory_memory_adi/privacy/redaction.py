import re
from typing import Callable
Redactor = Callable[[str], str]
_PATTERNS=[
 (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED_SSN]"),
 (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[REDACTED_EMAIL]"),
 (re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"), "[REDACTED_PHONE]"),
]
def default_redactor(text: str) -> str:
    out=text or ""
    for p,r in _PATTERNS:
        out=p.sub(r,out)
    return out
