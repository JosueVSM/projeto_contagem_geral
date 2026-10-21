"""Teste da ferramenta de gabarito (scripts/03_gabarito.py) SEM janela e SEM teclado.

A janela do OpenCV é trocada por uma função que não mostra nada, e as teclas
vêm de uma lista programada. Assim dá para conferir, de forma repetível, que:
  - cada tecla grava a classe certa no instante certo;
  - 'z' desfaz a última marcação;
  - pausa + '.' avança quadro a quadro;
  - a ferramenta pula sozinha do fim de um bloco de minutos para o próximo;
  - o arquivo é salvo e pode ser retomado.
O vídeo é sintético (fundo cinza com o número do quadro) e fica numa pasta temporária.
"""

import importlib.util
import json
import sys
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from configuracao import ORDEM_CLASSES  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
FPS = 10  # vídeo leve: 10 quadros/s, 320x180


def _carregar_script():
    sys.path.insert(0, str(RAIZ / "scripts"))
    spec = importlib.util.spec_from_file_location("gabarito_script", RAIZ / "scripts" / "03_gabarito.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def ambiente(tmp_path, monkeypatch):
    """Config, vídeo e pastas temporárias; nada toca no projeto real."""
    import configuracao
    import dados

    (tmp_path / "videos").mkdir()
    vw = cv2.VideoWriter(str(tmp_path / "videos" / "g.mp4"), cv2.VideoWriter_fourcc(*"mp4v"), FPS, (320, 180))
    for i in range(int(200 * FPS)):  # 200 s
        q = np.full((180, 320, 3), 90, np.uint8)
        cv2.putText(q, str(i), (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        vw.write(q)
    vw.release()

    cfg = yaml.safe_load((RAIZ / "config" / "config.yaml").read_text(encoding="utf-8"))
    cfg["pastas"]["videos"] = str(tmp_path / "videos")
    (tmp_path / "config.yaml").write_text(yaml.safe_dump(cfg), encoding="utf-8")
    (tmp_path / "videos.csv").write_text(
        "id;arquivo;usar_na_analise;data;hora_inicio;periodo;iluminacao;inicio_contagem_s;duracao_s;minutos_gabarito;observacoes\n"
        "g;g.mp4;nao;;;teste;;0;180;1,3;\n", encoding="utf-8")
    (tmp_path / "linhas.json").write_text(json.dumps({"g": {"p1": [160, 0], "p2": [160, 180], "largura": 320, "altura": 180}}))
    monkeypatch.setattr(configuracao, "ARQ_CONFIG", tmp_path / "config.yaml")
    monkeypatch.setattr(configuracao, "ARQ_VIDEOS", tmp_path / "videos.csv")
    monkeypatch.setattr(configuracao, "ARQ_LINHAS", tmp_path / "linhas.json")
    monkeypatch.setattr(dados, "PASTA_GABARITO", tmp_path / "gabarito")
    return tmp_path


def _rodar(monkeypatch, roteiro, args):
    """roteiro: lista de teclas; None = nenhuma tecla naquele ciclo."""
    teclas = iter(roteiro)
    telas = []
    monkeypatch.setattr(cv2, "imshow", lambda nome, img: telas.append(img))
    monkeypatch.setattr(cv2, "waitKey", lambda ms: (lambda k: 255 if k is None else ord(k))(next(teclas, "q")))
    monkeypatch.setattr(cv2, "getWindowProperty", lambda *a: 1)
    monkeypatch.setattr(cv2, "destroyAllWindows", lambda: None)
    monkeypatch.setattr(sys, "argv", ["03_gabarito.py", *args])
    _carregar_script().main()
    return telas


def test_marcar_desfazer_pausar_e_pular_bloco(ambiente, monkeypatch):
    roteiro = (
        [None] * 49 + ["1"]          # carro em ~5,0 s
        + [None] * 20 + ["2", "z"]   # moto em ~7,1 s, desfeita
        + [" ", ".", ".", ".", "4", " "]  # pausa, avança 3 quadros, pessoa
        + [None] * 600               # roda até o fim do minuto 1 -> pula sozinho para o minuto 3 (120 s)
        + [None] * 30 + ["6"]        # caminhão/ônibus (tecla 6) depois do salto para o minuto 3
        + ["q"]
    )
    _rodar(monkeypatch, roteiro, ["--video", "g", "--velocidade", "1"])
    g = pd.read_csv(ambiente / "gabarito" / "g.csv", sep=";")
    assert list(g["classe"]) == ["carro", "pessoa", ORDEM_CLASSES[5]]
    t = g["t_video_s"].to_numpy()
    assert t[0] == pytest.approx(5.0, abs=0.15)
    assert t[1] == pytest.approx(t[0] + 2.0 + 0.3, abs=0.15)   # 20 ciclos + 3 quadros depois (teclas não avançam o vídeo)
    assert 120.0 <= t[2] < 180.0                               # minuto 3, depois do salto automático
    assert not ((t > 60) & (t < 120)).any()                    # nada marcado no minuto 2 (não revisado)


def test_retoma_marcacoes_salvas(ambiente, monkeypatch):
    _rodar(monkeypatch, [None] * 10 + ["3", "q"], ["--video", "g", "--velocidade", "1"])
    _rodar(monkeypatch, [None] * 30 + ["5", "q"], ["--video", "g", "--velocidade", "1"])
    g = pd.read_csv(ambiente / "gabarito" / "g.csv", sep=";")
    assert sorted(g["classe"]) == ["bicicleta", "cachorro"]
