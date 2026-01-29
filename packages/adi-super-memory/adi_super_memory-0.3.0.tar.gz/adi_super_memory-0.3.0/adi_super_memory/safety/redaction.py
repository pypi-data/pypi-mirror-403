import re
_P=[(re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),"[REDACTED_SSN]"),
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),"[REDACTED_EMAIL]")]
def default_redactor(text: str) -> str:
    out=text
    for p,r in _P: out=p.sub(r,out)
    return out
