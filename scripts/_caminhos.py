"""Permite que os scripts importem os módulos de src/ (importe este arquivo primeiro)."""

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ / "src") not in sys.path:
    sys.path.insert(0, str(RAIZ / "src"))

# Terminal do Windows: garante acentos corretos na saída.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
