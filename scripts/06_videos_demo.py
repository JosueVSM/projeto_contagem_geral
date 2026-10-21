"""Passo 6: clipes de demonstração com o YOLO contando (para apresentação).

Para cada vídeo, gera 2 clipes de N segundos (padrão 30 s):
  <id>_inicio.mp4 -> primeiros N s da janela de contagem
  <id>_fim.mp4    -> últimos N s da janela de contagem
Cada clipe mostra os dois modelos LADO A LADO (nano | large), com caixas, id da
trilha, classe e a linha de contagem.

O CONTADOR é ACUMULADO desde o início da contagem (00:00) e vem da contagem
OFICIAL do passo 2 (resultados/yolo/<id>/<modelo>/eventos.csv): no clipe final
ele já começa com tudo o que foi contado até 09:30 e termina exatamente no total
das tabelas. As caixas são do YOLO rodando no próprio trecho (3 s antes servem
para "aquecer" o rastreador); por isso o instante em que uma caixa fica grossa
pode diferir em frações de segundo do instante em que o contador sobe.

Os clipes são gravados em H.264 (abrem no navegador, no Streamlit e no
PowerPoint) e ficam FORA do repositório (pastas.videos_demo no config.yaml),
porque mostram rostos e placas.

Uso:
  python scripts/06_videos_demo.py                     # todos os vídeos do experimento
  python scripts/06_videos_demo.py --video v4_18h --segundos 20
"""

import _caminhos  # noqa: F401
import argparse
import subprocess
from collections import Counter

import cv2
import numpy as np

from configuracao import (
    ORDEM_CLASSES, carregar_config, classe_analise, inicio_contagem, ler_csv_flexivel, ler_videos, linha_do_video,
    mapa_coco_para_pt, resolver_pasta,
)
from contador import ContadorLinha, Deteccao
from processamento import CORES, carregar_modelo

AQUECIMENTO_S = 3.0
LARG_PAINEL, ALT_PAINEL, ALT_TITULO = 960, 540, 56
# cv2.putText não desenha acentos: rótulos em ASCII.
ROTULO = {"carro": "carro", "moto": "moto", "bicicleta": "bicicleta", "pessoa": "pessoa",
          "cachorro": "cachorro", "onibus": "onibus", "caminhao": "caminhao", "caminhao_onibus": "caminhao/onibus"}
NOME_MODELO = {"yolo26n": "YOLO26-n (nano)", "yolo26l": "YOLO26-l (large)"}


def abrir_ffmpeg(saida, largura, altura, fps):
    import imageio_ffmpeg

    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{largura}x{altura}", "-r", f"{fps:.3f}", "-i", "-",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23", "-preset", "veryfast",
           "-movflags", "+faststart", str(saida)]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)


def eventos_oficiais(cfg, id_video, modelo, ini, fim):
    """Eventos contados pelo passo 2 dentro da janela de contagem: lista de (t, classe da análise)."""
    caminho = resolver_pasta(cfg["pastas"]["resultados"]) / "yolo" / id_video / modelo / "eventos.csv"
    if not caminho.is_file():
        raise SystemExit(f"Falta {caminho} (rode o passo 2 antes do 6).")
    ev = ler_csv_flexivel(caminho)
    if ev.empty:
        return []
    return sorted((float(t), classe_analise(c)) for t, c in zip(ev["t_video_s"], ev["classe"]) if ini <= float(t) < fim)


def acumulado_ate(eventos, t) -> Counter:
    return Counter(c for te, c in eventos if te <= t)


def desenhar_painel(quadro, contador, deteccoes, nome_modelo, cont: Counter):
    img = quadro.copy()
    a, b = tuple(map(int, contador.a)), tuple(map(int, contador.b))
    cv2.line(img, a, b, (0, 255, 255), 3)
    for d in deteccoes:
        tr = contador.trilhas.get(d.id_trilha)
        classe = tr.classe_votada if tr else d.classe
        contou = tr is not None and tr.t_cruzamento is not None and contador.motivo_descarte(tr) is None
        cor = CORES.get(classe, (255, 255, 255))
        x1, y1, x2, y2 = map(int, d.caixa)
        cv2.rectangle(img, (x1, y1), (x2, y2), cor, 5 if contou else 2)
        cv2.putText(img, f"{d.id_trilha} {ROTULO.get(classe, classe)}", (x1, max(18, y1 - 6)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, cor, 2)
    img = cv2.resize(img, (LARG_PAINEL, ALT_PAINEL))
    linhas = ([NOME_MODELO.get(nome_modelo, nome_modelo)] + [f"{ROTULO[c]}: {cont.get(c, 0)}" for c in ORDEM_CLASSES]
              + [f"TOTAL: {sum(cont.values())}"])
    cv2.rectangle(img, (0, 0), (250, 12 + 24 * len(linhas)), (0, 0, 0), -1)  # fundo do contador
    for i, txt in enumerate(linhas):
        cv2.putText(img, txt, (8, 26 + 24 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.62 if i else 0.66,
                    (255, 255, 255) if i else (0, 255, 255), 2)
    return img


def gerar_clipe(video, linha, modelos, cfg, t0, t1, titulo, saida, eventos):
    det = cfg["deteccao"]
    coco_pt = mapa_coco_para_pt(cfg)
    import torch

    usa_gpu = det["dispositivo"] != "cpu" and torch.cuda.is_available()
    precisao = 16 if (bool(det["half"]) and usa_gpu) else 32
    instancias = {m: (carregar_modelo(m, cfg), ContadorLinha(linha[0], linha[1], cfg["contagem"])) for m in modelos}

    cap = cv2.VideoCapture(str(video))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    cap.set(cv2.CAP_PROP_POS_MSEC, max(0.0, t0 - AQUECIMENTO_S) * 1000)
    largura, altura = LARG_PAINEL * len(modelos), ALT_PAINEL + ALT_TITULO
    ff = abrir_ffmpeg(saida, largura, altura, fps)
    ultimo, n = None, 0
    while True:
        ok, quadro = cap.read()
        if not ok:
            break
        t = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
        if t > t1:
            break
        paineis = []
        for nome, (modelo, contador) in instancias.items():
            res = modelo.track(quadro, persist=True, tracker=det["rastreador"], conf=det["conf"], iou=det["iou"],
                               imgsz=det["imgsz"], classes=sorted(coco_pt), device=det["dispositivo"],
                               quantize=precisao, verbose=False)[0]
            dets = []
            if res.boxes is not None and res.boxes.id is not None:
                for caixa, i, c, cf in zip(res.boxes.xyxy.cpu().numpy(), res.boxes.id.int().cpu().numpy(),
                                           res.boxes.cls.int().cpu().numpy(), res.boxes.conf.cpu().numpy()):
                    dets.append(Deteccao(int(i), coco_pt[int(c)], float(cf), tuple(map(float, caixa))))
            contador.atualizar(n, t, dets)
            if t >= t0:
                paineis.append(desenhar_painel(quadro, contador, dets, nome, acumulado_ate(eventos[nome], t)))
        n += 1
        if t < t0:
            continue
        barra = np.zeros((ALT_TITULO, largura, 3), np.uint8)
        cv2.putText(barra, f"{titulo}   t = {int(t // 60):02d}:{t % 60:04.1f}", (12, 38),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        ultimo = np.vstack([barra, np.hstack(paineis)])
        ff.stdin.write(ultimo.tobytes())
    if ultimo is not None:  # segura o último quadro 2 s, para dar tempo de ler o contador
        for _ in range(int(2 * fps)):
            ff.stdin.write(ultimo.tobytes())
    ff.stdin.close()
    ff.wait()
    cap.release()
    return {m: dict(acumulado_ate(eventos[m], t1)) for m in instancias}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--video", nargs="*", help="ids (padrão: vídeos do experimento que existem)")
    ap.add_argument("--segundos", type=float, default=30.0)
    ap.add_argument("--modelo", nargs="*", help="modelos lado a lado (padrão: os do config.yaml)")
    ap.add_argument("--refazer", action="store_true")
    args = ap.parse_args()

    cfg = carregar_config()
    videos = ler_videos(cfg)
    videos = videos[videos["id"].isin(args.video)] if args.video else videos[videos["usar"]]
    modelos = args.modelo or cfg["modelos"]
    pasta = resolver_pasta(cfg["pastas"]["videos_demo"])
    pasta.mkdir(parents=True, exist_ok=True)

    for _, v in videos.iterrows():
        if not v["existe"]:
            print(f"[pulando] {v['id']}: vídeo não encontrado")
            continue
        ini = inicio_contagem(v)
        fim = ini + v["duracao_s"]
        eventos = {m: eventos_oficiais(cfg, v["id"], m, ini, fim) for m in modelos}
        for nome, t0, t1 in [("inicio", ini, ini + args.segundos), ("fim", fim - args.segundos, fim)]:
            saida = pasta / f"{v['id']}_{nome}.mp4"
            if saida.is_file() and not args.refazer:
                print(f"[já existe] {saida.name}")
                continue
            titulo = (f"{v['id']} ({v['periodo']}) - trecho {'inicial' if nome == 'inicio' else 'final'} "
                      f"{int(t0 // 60):02d}:{int(t0 % 60):02d}-{int(t1 // 60):02d}:{int(t1 % 60):02d}"
                      " - contagem acumulada desde 00:00")
            cont = gerar_clipe(v["caminho"], linha_do_video(v["id"]), modelos, cfg, t0, t1, titulo, saida, eventos)
            print(f"{saida.name}: {cont}")
    print(f"Clipes em {pasta}")


if __name__ == "__main__":
    main()
