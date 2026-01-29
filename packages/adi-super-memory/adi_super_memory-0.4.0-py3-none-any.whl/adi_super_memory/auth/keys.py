from dataclasses import dataclass
from typing import List
import base64, hmac, hashlib, json, secrets, time

@dataclass(frozen=True)
class ApiKey:
    tenant: str
    key_id: str
    scopes: List[str]

class ApiKeyManager:
    def __init__(self, secret: str):
        self.secret = secret.encode("utf-8")
    def create(self, tenant: str, scopes: List[str]) -> str:
        payload={"tenant":tenant,"kid":secrets.token_hex(6),"scopes":scopes,"iat":int(time.time())}
        body=json.dumps(payload, separators=(",",":"), sort_keys=True).encode("utf-8")
        sig=hmac.new(self.secret, body, hashlib.sha256).digest()
        return "asm_" + _b64(body) + "." + _b64(sig)
    def verify(self, token: str) -> ApiKey:
        if not token.startswith("asm_"):
            raise ValueError("Invalid token prefix")
        rest=token[len("asm_"):]
        body_b64, sig_b64 = rest.split(".", 1)
        body=_ub64(body_b64); sig=_ub64(sig_b64)
        exp=hmac.new(self.secret, body, hashlib.sha256).digest()
        if not hmac.compare_digest(sig, exp):
            raise ValueError("Invalid token signature")
        payload=json.loads(body.decode("utf-8"))
        return ApiKey(tenant=str(payload["tenant"]), key_id=str(payload["kid"]), scopes=list(payload.get("scopes") or []))

def _b64(b: bytes)->str:
    return base64.urlsafe_b64encode(b).decode("ascii").rstrip("=")
def _ub64(s: str)->bytes:
    pad="=" * (-len(s)%4)
    return base64.urlsafe_b64decode(s + pad)
