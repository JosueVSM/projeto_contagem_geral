"""Configuração do pytest: permite importar os módulos de src/ nos testes."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
