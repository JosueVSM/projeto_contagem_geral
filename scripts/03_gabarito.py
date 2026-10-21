"""Passo 3: ferramenta para criar o GABARITO (contagem de referência).

Você assiste ao vídeo com calma (pode pausar, voltar e mudar a velocidade)
e aperta uma tecla no instante em que o MEIO do objeto passa pela linha
amarela. Cada tecla grava (tempo no vídeo, classe) em dados/gabarito/<id>.csv.
A ferramenta só mostra os minutos escolhidos (padrão: coluna minutos_gabarito) e pula
sozinha de um bloco para o outro. NÃO mostra as caixas do YOLO, para o
gabarito não ser influenciado pelo modelo.

Uso:
  python scripts/03_gabarito.py --video v1_meio_dia
  python scripts/03_gabarito.py --video teste --minutos 1-2 --velocidade 0.5

Teclas:
  1 carro   2 moto   3 bicicleta   4 pessoa   5 cachorro   6 ônibus   7 caminhão
  espaço  pausar/continuar          z  desfazer a última marcação
  a / d   voltar / avançar 2 s      , / .  quadro anterior / próximo (pausado)
  - / +   diminuir / aumentar velocidade
  n       pular para o próximo bloco de minutos
  q       salvar e sair  (também salva automaticamente a cada marcação)
"""

import _caminhos  # noqa: F401
import argparse
import time

import cv2

from configuracao import ORDEM_CLASSES, carregar_config, inicio_contagem, interpretar_minutos, linha_do_video, video_por_id
from dados import ler_gabarito, salvar_gabarito

TECLAS = {ord(str(i + 1)): c for i, c in enumerate(ORDEM_CLASSES)}
LARGURA_JANELA = 1280
VELOCIDADES = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0]


def blocos_de_minutos(minutos):
    """[1,2,3,8,9,10] -> [(1,3), (8,10)]"""
    blocos, ini = [], None
    for i, m in enumerate(minutos):
        if ini is None:
            ini = m
        if i == len(minutos) - 1 or minutos[i + 1] != m + 1:
            blocos.append((ini, m))
            ini = None
    return blocos


class Leitor:
    """Lê o vídeo e guarda o último quadro válido (para não ficar tela preta no fim)."""

    def __init__(self, caminho):
        self.cap = cv2.VideoCapture(str(caminho))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
        self.larg = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.alt = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.quadro, self.t, self.acabou = None, 0.0, False

    def ir_para(self, t):
        self.cap.set(cv2.CAP_PROP_POS_MSEC, max(0.0, t) * 1000)
        self.acabou = False
        self.proximo()

    def proximo(self):
        ok, q = self.cap.read()
        if ok:
            self.quadro, self.t = q, self.cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
        else:
            self.acabou = True


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--video", required=True)
    ap.add_argument("--minutos", help="ex.: 1-10 ou 1-3,8-10 (padrão: coluna minutos_gabarito de videos.csv)")
    ap.add_argument("--velocidade", type=float, default=0.5)
    args = ap.parse_args()

    cfg = carregar_config()
    v = video_por_id(args.video, cfg)
    if not v["existe"]:
        raise SystemExit(f"Arquivo não encontrado: {v['caminho']}")
    inicio = inicio_contagem(v)
    minutos = interpretar_minutos(args.minutos or v["minutos_gabarito"])
    blocos_min = blocos_de_minutos(minutos)
    blocos = [(inicio + (ini - 1) * 60, inicio + fim * 60) for ini, fim in blocos_min]
    p1, p2 = linha_do_video(args.video)

    existentes = ler_gabarito(args.video)
    marcas = [] if existentes is None else existentes.to_dict("records")
    if marcas:
        print(f"Retomando: {len(marcas)} marcações já salvas em dados/gabarito/{args.video}.csv")
    print(f"Minutos a revisar: {minutos}")

    vid = Leitor(v["caminho"])
    escala = min(1.0, LARGURA_JANELA / vid.larg)
    tam = (int(vid.larg * escala), int(vid.alt * escala))
    a = (int(p1[0] * escala), int(p1[1] * escala))
    b = (int(p2[0] * escala), int(p2[1] * escala))

    i_bloco = 0
    vid.ir_para(blocos[0][0])
    pausado, vel, fim = False, args.velocidade, False
    aviso, aviso_ate = "", 0.0
    janela = f"Gabarito - {args.video}"

    def avisar(txt, seg=1.5):
        nonlocal aviso, aviso_ate
        aviso, aviso_ate = txt, time.time() + seg

    while True:
        # Saiu do bloco atual (ou o vídeo acabou)? Vai para o próximo bloco ou termina.
        if not fim and (vid.acabou or vid.t >= blocos[i_bloco][1]):
            if i_bloco + 1 < len(blocos) and not vid.acabou:
                i_bloco += 1
                vid.ir_para(blocos[i_bloco][0])
                avisar(f"Pulou para o minuto {blocos_min[i_bloco][0]}", 2)
            else:
                fim, pausado = True, True

        if vid.quadro is not None:
            img = cv2.resize(vid.quadro, tam)
            cv2.line(img, a, b, (0, 255, 255), 2)
            t_rel = vid.t - inicio
            minuto = int(t_rel // 60) + 1
            cont = {c: 0 for c in ORDEM_CLASSES}
            for m in marcas:
                if int((m["t_video_s"] - inicio) // 60) + 1 == minuto:
                    cont[m["classe"]] += 1
            hud = [
                f"min {minuto}  {int(t_rel // 60):02d}:{t_rel % 60:05.2f}   vel {vel}x   {'PAUSADO' if pausado else ''}",
                "  ".join(f"{i + 1}:{c[:4]}={cont[c]}" for i, c in enumerate(ORDEM_CLASSES)),
                f"total de marcacoes: {len(marcas)}" + ("   FIM - q para sair" if fim else ""),
            ]
            if time.time() < aviso_ate:
                hud.append(aviso)
            cv2.rectangle(img, (0, 0), (img.shape[1], 28 * len(hud) + 10), (0, 0, 0), -1)
            for i, txt in enumerate(hud):
                cv2.putText(img, txt, (10, 26 + 28 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
            cv2.imshow(janela, img)

        espera = 30 if pausado else max(1, int(1000 / (vid.fps * vel)))
        tecla = cv2.waitKey(espera) & 0xFF
        if cv2.getWindowProperty(janela, cv2.WND_PROP_VISIBLE) < 1:
            break

        if tecla in TECLAS and vid.quadro is not None:
            marcas.append({"t_video_s": round(vid.t, 3), "classe": TECLAS[tecla]})
            salvar_gabarito(args.video, marcas)
            avisar(f"+1 {TECLAS[tecla]} em {vid.t - inicio:.2f} s")
        elif tecla == ord("z") and marcas:
            desfeita = marcas.pop()
            salvar_gabarito(args.video, marcas)
            avisar(f"desfeito: {desfeita['classe']} em {desfeita['t_video_s'] - inicio:.2f} s", 2)
        elif tecla == ord(" "):
            pausado = True if fim else not pausado
        elif tecla in (ord("a"), ord("d")):
            vid.ir_para(vid.t + (-2 if tecla == ord("a") else 2))
            fim = False
        elif tecla == ord(",") and pausado:
            vid.ir_para(vid.t - 1.0 / vid.fps)
            fim = False
        elif tecla == ord(".") and pausado:
            vid.proximo()
        elif tecla in (ord("+"), ord("=")):
            vel = next((x for x in VELOCIDADES if x > vel), vel)
        elif tecla == ord("-"):
            vel = next((x for x in reversed(VELOCIDADES) if x < vel), vel)
        elif tecla == ord("n") and i_bloco + 1 < len(blocos):
            i_bloco += 1
            vid.ir_para(blocos[i_bloco][0])
            fim = False
        elif tecla == ord("q"):
            break
        elif not pausado:
            vid.proximo()

    vid.cap.release()
    cv2.destroyAllWindows()
    salvar_gabarito(args.video, marcas)
    print(f"{len(marcas)} marcações salvas em dados/gabarito/{args.video}.csv")


if __name__ == "__main__":
    main()
