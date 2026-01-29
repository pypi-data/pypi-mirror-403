from __future__ import annotations

import json
import tarfile
from array import array
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional


def _base_lang(lang: str) -> str:
    return (lang or "").split("-", 1)[0].lower()


def _profile_lang(lang: str) -> str:
    # Our mini set uses "zh" filename (not zh-CN).
    base = _base_lang(lang)
    if base == "zh":
        return "zh"
    return base


def _read_f32(buf: bytes) -> array:
    """
    Read ParSon binary float32 arrays in a dependency-free way.
    Supports PRSN header (16 bytes) or raw float32 stream.
    """
    if len(buf) >= 4 and buf[:4] == b"PRSN":
        buf = buf[16:]  # magic + version + vocab_size + dims
    a = array("f")
    a.frombytes(buf)
    return a


@dataclass(frozen=True)
class Axes6:
    P: float
    A: float
    R: float
    S: float
    O: float
    N: float
    method: str = "vocab"

    def to_dict(self) -> dict[str, float | str]:
        return {
            "P": float(self.P),
            "A": float(self.A),
            "R": float(self.R),
            "S": float(self.S),
            "O": float(self.O),
            "N": float(self.N),
            "method": self.method,
        }


class ParsonMini:
    """
    Minimal reader for WikiParSon mini `.parson` archives (tar.gz).

    Expected layout inside archive:
      <lang>-<ver>/
        vocab.json
        distributions/{presence,action,relation,structure,operator,nomination}.bin
    """

    def __init__(
        self,
        lang: str,
        *,
        version: str = "2026.01",
        profiles_dir: Optional[Path] = None,
    ):
        self.lang = _profile_lang(lang)
        self.version = version
        self.profiles_dir = profiles_dir or (Path.home() / "parson_final" / "wikiparson_mini")

        self._vocab: dict[str, int] = {}
        self._P: Optional[array] = None
        self._A: Optional[array] = None
        self._R: Optional[array] = None
        self._S: Optional[array] = None
        self._O: Optional[array] = None
        self._N: Optional[array] = None

        self._load()

    @property
    def path(self) -> Path:
        return self.profiles_dir / f"{self.lang}-{self.version}.parson"

    def _load(self) -> None:
        p = self.path
        if not p.exists():
            raise FileNotFoundError(str(p))

        prefix = f"{self.lang}-{self.version}/"
        with tarfile.open(p, "r:gz") as tf:
            # vocab
            vf = tf.extractfile(prefix + "vocab.json")
            if vf is None:
                raise FileNotFoundError("vocab.json missing in profile")
            vocab_obj = json.loads(vf.read().decode("utf-8", errors="ignore"))
            if isinstance(vocab_obj, dict) and "token_to_id" in vocab_obj:
                vocab_obj = vocab_obj.get("token_to_id")
            if not isinstance(vocab_obj, dict):
                raise ValueError("unexpected vocab.json format")
            self._vocab = {str(k): int(v) for k, v in vocab_obj.items() if isinstance(k, str)}

            def read_bin(name: str) -> array:
                bf = tf.extractfile(prefix + f"distributions/{name}.bin")
                if bf is None:
                    raise FileNotFoundError(f"{name}.bin missing in profile")
                return _read_f32(bf.read())

            self._P = read_bin("presence")
            self._A = read_bin("action")
            self._R = read_bin("relation")
            self._S = read_bin("structure")
            self._O = read_bin("operator")
            self._N = read_bin("nomination")

    def get_axes(self, token: str) -> Optional[Axes6]:
        t = (token or "").strip()
        if not t:
            return None
        idx = self._vocab.get(t)
        if idx is None and _base_lang(self.lang) in {"en", "de", "fr", "es", "it", "pt", "nl"}:
            idx = self._vocab.get(t.lower())
        if idx is None:
            return None

        P = float(self._P[idx]) if self._P is not None and idx < len(self._P) else 0.5
        A = float(self._A[idx]) if self._A is not None and idx < len(self._A) else 0.5
        R = float(self._R[idx]) if self._R is not None and idx < len(self._R) else 0.5
        S = float(self._S[idx]) if self._S is not None and idx < len(self._S) else 0.5
        O = float(self._O[idx]) if self._O is not None and idx < len(self._O) else 0.5
        N = float(self._N[idx]) if self._N is not None and idx < len(self._N) else 0.5
        return Axes6(P=P, A=A, R=R, S=S, O=O, N=N, method="vocab")


@lru_cache(maxsize=64)
def get_parson_mini(lang: str, *, version: str = "2026.01") -> Optional[ParsonMini]:
    try:
        return ParsonMini(lang, version=version)
    except Exception:
        return None

