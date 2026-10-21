"""Passo 2: detectar, rastrear e contar com YOLO (cada vídeo x cada modelo).

Uso:
  python scripts/02_contar_yolo.py                       # todos os vídeos existentes, todos os modelos
  python scripts/02_contar_yolo.py --video teste --salvar-video
  python scripts/02_contar_yolo.py --video v1_meio_dia --modelo yolo26n --max-segundos 60 --mostrar

Saídas em resultados/yolo/<video>/<modelo>/:
  eventos.csv              um objeto contado por linha (tempo, minuto, classe, sentido)
  contagem_por_minuto.csv  tabela minuto x classe
  trilhas.csv              todas as trilhas, inclusive descartadas, com o motivo
  desempenho.json          tempos de processamento e dados da máquina
  ms_por_quadro.csv        tempo de cada quadro (para o gráfico de distribuição)
"""

import _caminhos  # noqa: F401
import argparse
import json

import pandas as pd

from configuracao import carregar_config, inicio_contagem, ler_videos, linha_do_video, resolver_pasta
from metricas import contagem_por_minuto, minuto_relativo
from processamento import processar_video


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--video", nargs="*", help="ids dos vídeos (padrão: todos que existem)")
    ap.add_argument("--modelo", nargs="*", help="modelos (padrão: os do config.yaml)")
    ap.add_argument("--salvar-video", action="store_true", help="grava o vídeo anotado (fora do repositório)")
    ap.add_argument("--mostrar", action="store_true", help="mostra o processamento numa janela")
    ap.add_argument("--max-segundos", type=float, help="processa só o começo do vídeo (para testes rápidos)")
    ap.add_argument("--refazer", action="store_true", help="refaz mesmo se o resultado já existir")
    args = ap.parse_args()

    cfg = carregar_config()
    videos = ler_videos(cfg)
    if args.video:
        desconhecidos = set(args.video) - set(videos["id"])
        if desconhecidos:
            raise SystemExit(f"Ids não encontrados em config/videos.csv: {desconhecidos}")
        videos = videos[videos["id"].isin(args.video)]
    modelos = args.modelo or cfg["modelos"]
    pasta_res = resolver_pasta(cfg["pastas"]["resultados"]) / "yolo"
    pasta_anot = resolver_pasta(cfg["pastas"]["videos_anotados"])

    for _, v in videos.iterrows():
        if not v["existe"]:
            print(f"[pulando] {v['id']}: arquivo {v['caminho']} não encontrado.")
            continue
        linha = linha_do_video(v["id"])
        inicio = inicio_contagem(v)
        for nome in modelos:
            destino = pasta_res / v["id"] / nome
            if (destino / "eventos.csv").is_file() and not args.refazer and not args.max_segundos:
                print(f"[já existe] {v['id']} / {nome} (use --refazer para processar de novo)")
                continue
            print(f"\n=== {v['id']} | {nome} ===")
            saida_video = pasta_anot / f"{v['id']}_{nome}.mp4" if args.salvar_video else None
            r = processar_video(
                v["caminho"], nome, linha, cfg,
                caminho_saida_video=saida_video, max_segundos=args.max_segundos,
                mostrar=args.mostrar, inicio_s=inicio,
            )
            if args.max_segundos:
                destino = destino.with_name(f"{nome}_parcial_{int(args.max_segundos)}s")
            destino.mkdir(parents=True, exist_ok=True)

            eventos = pd.DataFrame(r["eventos"], columns=["id_trilha", "t_video_s", "classe", "sentido", "conf_media", "n_quadros"])
            eventos.insert(0, "video", v["id"])
            eventos.insert(1, "modelo", nome)
            eventos["minuto"] = minuto_relativo(eventos["t_video_s"], inicio) if len(eventos) else []
            eventos["t_video_s"] = eventos["t_video_s"].round(3)
            eventos.to_csv(destino / "eventos.csv", sep=";", index=False)

            tabela = contagem_por_minuto(eventos, inicio, v["duracao_s"])
            tabela.to_csv(destino / "contagem_por_minuto.csv", sep=";")
            pd.DataFrame(r["trilhas"]).to_csv(destino / "trilhas.csv", sep=";", index=False)
            pd.DataFrame({"ms": r["ms_por_quadro"]}).round(3).to_csv(destino / "ms_por_quadro.csv", sep=";", index=False)
            d = r["desempenho"] | {"inicio_contagem_s": inicio, "duracao_contagem_s": v["duracao_s"]}
            with open(destino / "desempenho.json", "w", encoding="utf-8") as f:
                json.dump(d, f, indent=2, ensure_ascii=False)

            print(f"  {d['quadros_processados']} quadros em {d['tempo_total_s']} s "
                  f"({d['quadros_por_segundo']} quadros/s, {d['ms_por_quadro_deteccao_rastreamento_mediana']} ms/quadro)")
            print(f"  Contados na janela de análise: {int(tabela.values.sum())} -> {tabela.sum().to_dict()}")
            print(f"  Salvo em {destino}")


if __name__ == "__main__":
    main()
