"""Teste de integração: roda o pipeline INTEIRO num vídeo SINTÉTICO.

O vídeo é montado com as imagens de exemplo que vêm com a Ultralytics
(um ônibus e duas pessoas) deslizando sobre um fundo cinza. Contagem
manual e gabarito também são inventados aqui, só para o software ter o
que comparar. Tudo acontece numa pasta TEMPORÁRIA, apagada no final:
nada disso vira resultado do experimento.

Serve para provar que GPU + YOLO + rastreador + contagem + tabelas +
gráficos funcionam juntos antes de existir qualquer vídeo real.

Uso (demora ~1 min; baixa os pesos do YOLO na 1ª vez):
  python testes/teste_integracao.py
  python testes/teste_integracao.py --manter   # não apaga a pasta temporária
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np
import yaml

RAIZ = Path(__file__).resolve().parents[1]
LARG, ALT, FPS, SEGUNDOS = 1280, 720, 30, 8


def colar(fundo, img, x, y):
    """Cola img em fundo na posição (x, y), cortando o que sair da tela."""
    h, w = img.shape[:2]
    x1, y1, x2, y2 = max(x, 0), max(y, 0), min(x + w, fundo.shape[1]), min(y + h, fundo.shape[0])
    if x1 < x2 and y1 < y2:
        fundo[y1:y2, x1:x2] = img[y1 - y:y2 - y, x1 - x:x2 - x]


def gerar_video(caminho: Path):
    from ultralytics.utils import ASSETS

    onibus = cv2.resize(cv2.imread(str(ASSETS / "bus.jpg")), (300, 400))
    pessoas = cv2.resize(cv2.imread(str(ASSETS / "zidane.jpg")), (400, 225))
    vw = cv2.VideoWriter(str(caminho), cv2.VideoWriter_fourcc(*"mp4v"), FPS, (LARG, ALT))
    n = SEGUNDOS * FPS
    for i in range(n):
        q = np.full((ALT, LARG, 3), 90, np.uint8)
        colar(q, onibus, int(-300 + (LARG + 300) * i / n), 300)   # esquerda -> direita
        colar(q, pessoas, int(LARG - (LARG + 400) * i / n), 20)   # direita -> esquerda
        vw.write(q)
    vw.release()


def rodar(cmd, cwd):
    print(f"\n$ {' '.join(map(str, cmd))}")
    r = subprocess.run([sys.executable, *map(str, cmd)], cwd=cwd, text=True, capture_output=True, encoding="utf-8")
    print(r.stdout[-3000:])
    if r.returncode != 0:
        print(r.stderr[-5000:])
        raise SystemExit(f"FALHOU: {cmd}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manter", action="store_true")
    args = ap.parse_args()

    tmp = Path(tempfile.mkdtemp(prefix="teste_contagem_"))
    print(f"Pasta temporária: {tmp}")
    try:
        for pasta in ("src", "scripts", "config"):
            shutil.copytree(RAIZ / pasta, tmp / pasta, ignore=shutil.ignore_patterns("__pycache__", "linhas.json"))
        (tmp / "videos").mkdir()
        gerar_video(tmp / "videos" / "sint.mp4")

        cfg = yaml.safe_load((RAIZ / "config" / "config.yaml").read_text(encoding="utf-8"))
        cfg["pastas"] = {
            "videos": str(tmp / "videos"),
            "videos_anotados": str(tmp / "anotados"),
            "modelos": str(RAIZ / "modelos"),  # reaproveita os pesos já baixados
            "resultados": "resultados",
        }
        (tmp / "config" / "config.yaml").write_text(yaml.safe_dump(cfg, allow_unicode=True), encoding="utf-8")
        (tmp / "config" / "videos.csv").write_text(
            "id;arquivo;usar_na_analise;data;hora_inicio;periodo;iluminacao;inicio_contagem_s;duracao_s;minutos_gabarito;observacoes\n"
            f"sint;sint.mp4;sim;;;sintetico;;0;{SEGUNDOS};1;teste de software\n",
            encoding="utf-8",
        )
        (tmp / "config" / "linhas.json").write_text(json.dumps(
            {"sint": {"p1": [640, 0], "p2": [640, 720], "largura": LARG, "altura": ALT}}), encoding="utf-8")
        # Contagens inventadas (apenas para exercitar as comparações).
        (tmp / "dados" / "manual").mkdir(parents=True)
        (tmp / "dados" / "manual" / "sint.csv").write_text(
            "minuto;carro;moto;bicicleta;pessoa;cachorro;onibus;caminhao;observacoes\n1;0;0;0;2;0;1;0;\n", encoding="utf-8")
        (tmp / "dados" / "gabarito").mkdir(parents=True)
        (tmp / "dados" / "gabarito" / "sint.csv").write_text(
            "t_video_s;classe\n3.2;pessoa\n3.6;pessoa\n4.2;onibus\n", encoding="utf-8")

        rodar(["scripts/02_contar_yolo.py", "--salvar-video"], tmp)
        rodar(["scripts/04_comparar.py"], tmp)
        if (tmp / "scripts" / "05_graficos.py").is_file():
            rodar(["scripts/05_graficos.py"], tmp)
        # Mesma comparação com a contagem manual SÓ EM TOTAL (formato alternativo).
        (tmp / "dados" / "manual" / "sint.csv").write_text(
            "minuto;carro;moto;bicicleta;pessoa;cachorro;onibus;caminhao\ntotal;0;0;0;2;0;1;0\n", encoding="utf-8")
        rodar(["scripts/04_comparar.py"], tmp)
        rodar(["scripts/05_graficos.py"], tmp)

        gerados = sorted(p.relative_to(tmp).as_posix() for p in (tmp / "resultados").rglob("*") if p.is_file())
        print("\nArquivos gerados:")
        for g in gerados:
            print("  ", g)
        for m in cfg["modelos"]:
            ev = (tmp / "resultados" / "yolo" / "sint" / m / "eventos.csv").read_text(encoding="utf-8")
            print(f"\nEventos {m}:\n{ev}")
        print("\nOK: pipeline completo rodou sem erros.")
    finally:
        if args.manter:
            print(f"(pasta mantida em {tmp})")
        else:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
