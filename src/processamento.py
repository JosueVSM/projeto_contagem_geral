"""Laço principal: lê o vídeo quadro a quadro, roda YOLO + ByteTrack e conta.

Também mede o tempo de processamento de cada quadro, usado na comparação
entre o modelo pequeno e o grande.
"""

from __future__ import annotations

import platform
import statistics
import time
from pathlib import Path

import cv2
import numpy as np

from configuracao import mapa_coco_para_pt, resolver_pasta
from contador import ContadorLinha, Deteccao

# Cor (BGR) de cada classe no vídeo anotado.
CORES = {
    "carro": (60, 180, 255),
    "moto": (255, 120, 60),
    "bicicleta": (80, 220, 80),
    "pessoa": (200, 80, 220),
    "cachorro": (40, 40, 220),
    "onibus": (0, 220, 220),
    "caminhao": (180, 180, 180),
}

QUADROS_AQUECIMENTO = 30  # primeiros quadros (GPU "esquentando") ficam fora das medianas de tempo


def carregar_modelo(nome: str, cfg: dict):
    """Carrega o YOLO pelo nome (ex.: 'yolo26n'). Baixa os pesos na 1ª vez."""
    from ultralytics import YOLO

    pasta = resolver_pasta(cfg["pastas"]["modelos"])
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / f"{nome}.pt"
    if not caminho.is_file():
        # A Ultralytics baixa o arquivo na pasta atual; depois movemos para modelos/.
        modelo = YOLO(f"{nome}.pt")
        baixado = Path(f"{nome}.pt")
        if baixado.is_file():
            baixado.replace(caminho)
        return YOLO(str(caminho)) if caminho.is_file() else modelo
    return YOLO(str(caminho))


def _aquecer(nome_modelo: str, cfg: dict, altura: int, largura: int, precisao: int, vezes: int = 15):
    """Roda o modelo algumas vezes numa imagem preta ANTES de medir o tempo.

    Sem isso, o primeiro modelo a rodar paga sozinho a inicialização da GPU
    (CUDA), o que distorce a comparação de velocidade entre os modelos.
    Usa uma instância separada para não "sujar" o rastreador.
    """
    det = cfg["deteccao"]
    aquecimento = carregar_modelo(nome_modelo, cfg)
    imagem = np.zeros((altura, largura, 3), dtype=np.uint8)
    for _ in range(vezes):
        aquecimento.predict(imagem, imgsz=det["imgsz"], device=det["dispositivo"], quantize=precisao, verbose=False)
    del aquecimento


def _desenhar(quadro, contador: ContadorLinha, deteccoes: list[Deteccao], t_rel: float):
    a = tuple(map(int, contador.a))
    b = tuple(map(int, contador.b))
    cv2.line(quadro, a, b, (0, 255, 255), 3)
    for d in deteccoes:
        x1, y1, x2, y2 = map(int, d.caixa)
        tr = contador.trilhas.get(d.id_trilha)
        classe = tr.classe_votada if tr else d.classe
        cor = CORES.get(classe, (255, 255, 255))
        espessura = 4 if tr is not None and tr.t_cruzamento is not None else 2
        cv2.rectangle(quadro, (x1, y1), (x2, y2), cor, espessura)
        cv2.putText(quadro, f"{d.id_trilha} {classe}", (x1, max(20, y1 - 6)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, cor, 2)
    parcial = contador.contagem_parcial()
    texto = [f"t = {t_rel:6.1f} s"] + [f"{c}: {parcial.get(c, 0)}" for c in CORES]
    cv2.rectangle(quadro, (0, 0), (230, 30 + 28 * len(texto)), (0, 0, 0), -1)
    for i, linha in enumerate(texto):
        cv2.putText(quadro, linha, (10, 30 + 28 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)


def processar_video(
    caminho_video: Path,
    nome_modelo: str,
    linha: tuple,
    cfg: dict,
    caminho_saida_video: Path | None = None,
    max_segundos: float | None = None,
    mostrar: bool = False,
    inicio_s: float = 0.0,
) -> dict:
    """Processa um vídeo com um modelo e devolve eventos, trilhas e desempenho.

    inicio_s só é usado no relógio desenhado no vídeo anotado; os eventos
    saem com o tempo absoluto do vídeo (t_video_s).
    """
    import torch

    det = cfg["deteccao"]
    coco_pt = mapa_coco_para_pt(cfg)
    ids_coco = sorted(coco_pt)

    cap = cv2.VideoCapture(str(caminho_video))
    if not cap.isOpened():
        raise RuntimeError(f"Não consegui abrir o vídeo {caminho_video}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or None
    largura = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    altura = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    escritor = None
    if caminho_saida_video:
        caminho_saida_video.parent.mkdir(parents=True, exist_ok=True)
        escritor = cv2.VideoWriter(str(caminho_saida_video), cv2.VideoWriter_fourcc(*"mp4v"), fps, (largura, altura))

    usa_gpu = det["dispositivo"] != "cpu" and torch.cuda.is_available()
    precisao = 16 if (bool(det["half"]) and usa_gpu) else 32  # 16 = meia precisão (FP16)
    _aquecer(nome_modelo, cfg, altura, largura, precisao)
    modelo = carregar_modelo(nome_modelo, cfg)  # instância nova = rastreador zerado
    contador = ContadorLinha(linha[0], linha[1], cfg["contagem"])
    if usa_gpu:
        torch.cuda.reset_peak_memory_stats()

    ms_total, ms_pre, ms_inf, ms_pos, ms_leitura = [], [], [], [], []
    n = 0
    t_inicio = time.perf_counter()
    t_anterior = -1.0
    while True:
        t0 = time.perf_counter()
        ok, quadro = cap.read()
        if not ok:
            break
        ms_leitura.append((time.perf_counter() - t0) * 1000)

        # Tempo real do quadro (funciona mesmo com taxa de quadros variável do celular).
        t_s = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
        if t_s <= t_anterior:  # alguns codecs não informam o tempo -> usa índice / fps
            t_s = n / fps
        t_anterior = t_s
        if max_segundos is not None and t_s > max_segundos:
            break

        t1 = time.perf_counter()
        res = modelo.track(
            quadro,
            persist=True,
            tracker=det["rastreador"],
            conf=det["conf"],
            iou=det["iou"],
            imgsz=det["imgsz"],
            classes=ids_coco,
            device=det["dispositivo"],
            quantize=precisao,
            verbose=False,
        )[0]
        caixas = res.boxes
        deteccoes = []
        if caixas is not None and caixas.id is not None:
            xyxy = caixas.xyxy.cpu().numpy()
            ids = caixas.id.int().cpu().numpy()
            cls = caixas.cls.int().cpu().numpy()
            confs = caixas.conf.cpu().numpy()
            for caixa, i, c, cf in zip(xyxy, ids, cls, confs):
                deteccoes.append(Deteccao(int(i), coco_pt[int(c)], float(cf), tuple(map(float, caixa))))
        ms_total.append((time.perf_counter() - t1) * 1000)  # detecção + rastreamento
        ms_pre.append(res.speed.get("preprocess", np.nan))
        ms_inf.append(res.speed.get("inference", np.nan))
        ms_pos.append(res.speed.get("postprocess", np.nan))

        contador.atualizar(n, t_s, deteccoes)

        if escritor is not None or mostrar:
            _desenhar(quadro, contador, deteccoes, t_s - inicio_s)
            if escritor is not None:
                escritor.write(quadro)
            if mostrar:
                cv2.imshow(f"{nome_modelo} - q para sair", cv2.resize(quadro, (largura // 2, altura // 2)))
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

        n += 1
        if n % 300 == 0:
            decorrido = time.perf_counter() - t_inicio
            total_txt = f"/{total}" if total else ""
            print(f"  {nome_modelo}: quadro {n}{total_txt}  ({n / decorrido:.1f} quadros/s)", flush=True)

    tempo_total = time.perf_counter() - t_inicio
    cap.release()
    if escritor is not None:
        escritor.release()
    if mostrar:
        cv2.destroyAllWindows()

    def mediana(v):
        v = [x for x in v[QUADROS_AQUECIMENTO:] if not np.isnan(x)] or [x for x in v if not np.isnan(x)]
        return round(statistics.median(v), 3) if v else None

    desempenho = {
        "modelo": nome_modelo,
        "video": caminho_video.name,
        "resolucao": f"{largura}x{altura}",
        "fps_video": round(fps, 3),
        "quadros_processados": n,
        "duracao_processada_s": round(t_anterior, 2),
        "tempo_total_s": round(tempo_total, 2),
        "quadros_por_segundo": round(n / tempo_total, 2) if tempo_total else None,
        "ms_por_quadro_deteccao_rastreamento_mediana": mediana(ms_total),
        "ms_preprocessamento_mediana": mediana(ms_pre),
        "ms_inferencia_mediana": mediana(ms_inf),
        "ms_posprocessamento_mediana": mediana(ms_pos),
        "ms_leitura_quadro_mediana": mediana(ms_leitura),
        "tempo_real_x": round(t_anterior / tempo_total, 2) if tempo_total else None,
        "memoria_gpu_pico_mb": round(torch.cuda.max_memory_allocated() / 2**20, 1) if usa_gpu else None,
        "gpu": torch.cuda.get_device_name(0) if usa_gpu else "cpu",
        "imgsz": det["imgsz"],
        "half": precisao == 16,
        "video_anotado_salvo": escritor is not None or mostrar,
        "torch": torch.__version__,
        "python": platform.python_version(),
    }
    try:
        import ultralytics

        desempenho["ultralytics"] = ultralytics.__version__
    except Exception:
        pass

    return {
        "eventos": contador.eventos(),
        "trilhas": contador.resumo_trilhas(),
        "desempenho": desempenho,
        "ms_por_quadro": ms_total,
    }
