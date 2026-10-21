"""Passo 1: desenhar a linha de contagem de um vídeo com dois cliques.

Uso:
  python scripts/01_definir_linha.py --video v1_meio_dia
  python scripts/01_definir_linha.py --video v2_tarde_1 --copiar-de v1_meio_dia

Na janela:
  clique 2 pontos  -> define a linha (de uma calçada até a outra)
  r                -> recomeçar
  s ou Enter       -> salvar em config/linhas.json
  q ou Esc         -> sair sem salvar

Dica: alinhe a linha a uma referência física que você também enxerga da
janela (ex.: a quina onde termina o muro azul), pois a contagem manual
precisa usar EXATAMENTE a mesma referência.
"""

import _caminhos  # noqa: F401
import argparse

import cv2

from configuracao import carregar_config, ler_linhas, resolver_pasta, salvar_linha, video_por_id

LARGURA_JANELA = 1280


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--video", required=True, help="id do vídeo em config/videos.csv")
    ap.add_argument("--segundo", type=float, default=5.0, help="instante do quadro mostrado (s)")
    ap.add_argument("--copiar-de", help="reaproveitar a linha de outro vídeo (câmera no mesmo lugar)")
    args = ap.parse_args()

    cfg = carregar_config()
    video = video_por_id(args.video, cfg)

    if args.copiar_de:
        origem = ler_linhas().get(args.copiar_de)
        if not origem:
            raise SystemExit(f"Vídeo {args.copiar_de} não tem linha definida.")
        salvar_linha(args.video, origem["p1"], origem["p2"], origem["largura"], origem["altura"])
        print(f"Linha de {args.copiar_de} copiada para {args.video}. Confira abrindo este script sem --copiar-de.")
        return

    if not video["existe"]:
        raise SystemExit(f"Arquivo não encontrado: {video['caminho']}")
    cap = cv2.VideoCapture(str(video["caminho"]))
    cap.set(cv2.CAP_PROP_POS_MSEC, args.segundo * 1000)
    ok, quadro = cap.read()
    cap.release()
    if not ok:
        raise SystemExit("Não consegui ler o quadro do vídeo.")

    alt, larg = quadro.shape[:2]
    escala = min(1.0, LARGURA_JANELA / larg)
    base = cv2.resize(quadro, (int(larg * escala), int(alt * escala)))
    pontos = [tuple(int(c * escala) for c in p) for p in (ler_linhas().get(args.video) or {}).values()
              if isinstance(p, list)]

    def desenhar():
        img = base.copy()
        for p in pontos:
            cv2.circle(img, p, 6, (0, 255, 255), -1)
        if len(pontos) == 2:
            cv2.line(img, pontos[0], pontos[1], (0, 255, 255), 3)
        msg = "clique 2 pontos | r = recomecar | s = salvar | q = sair"
        cv2.putText(img, msg, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 4)
        cv2.putText(img, msg, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.imshow(janela, img)

    def ao_clicar(evento, x, y, *_):
        if evento == cv2.EVENT_LBUTTONDOWN:
            if len(pontos) == 2:
                pontos.clear()
            pontos.append((x, y))
            desenhar()

    janela = f"Linha de contagem - {args.video}"
    cv2.namedWindow(janela)
    cv2.setMouseCallback(janela, ao_clicar)
    desenhar()
    while True:
        tecla = cv2.waitKey(50) & 0xFF
        if tecla == ord("r"):
            pontos.clear()
            desenhar()
        elif tecla in (ord("s"), 13) and len(pontos) == 2:
            p1, p2 = [(round(x / escala, 1), round(y / escala, 1)) for x, y in pontos]
            salvar_linha(args.video, p1, p2, larg, alt)
            # Imagem de conferência fica fora do repositório (pode ter rostos e placas).
            pasta = resolver_pasta(cfg["pastas"]["videos_anotados"])
            pasta.mkdir(parents=True, exist_ok=True)
            img = quadro.copy()
            cv2.line(img, tuple(map(int, p1)), tuple(map(int, p2)), (0, 255, 255), 4)
            cv2.imwrite(str(pasta / f"linha_{args.video}.png"), img)
            print(f"Linha salva: p1={p1} p2={p2} (imagem em {pasta})")
            break
        elif tecla in (ord("q"), 27) or cv2.getWindowProperty(janela, cv2.WND_PROP_VISIBLE) < 1:
            print("Saiu sem salvar.")
            break
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
