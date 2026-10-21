"""Passo 5: gráficos (PNG, 300 dpi) a partir das tabelas do passo 4.

Por decisão do trabalho, os gráficos tratam só do ERRO POR CLASSE (sem análise
por minuto nem por horário), além da velocidade dos modelos.

Uso:
  python scripts/05_graficos.py           # resultados/tabelas -> resultados/graficos
  python scripts/05_graficos.py --teste   # resultados/calibracao/...

Cada gráfico só é gerado se a tabela que ele usa existir (ex.: sem gabarito
não há gráfico de precisão). Os números exatos estão nas tabelas CSV.

Cores fixas por método (iguais em todos os gráficos):
  gabarito = cinza escuro (referência) | manual = azul | YOLO-n = laranja | YOLO-l = verde-água
"""

import _caminhos  # noqa: F401
import argparse

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from configuracao import ORDEM_CLASSES, carregar_config, resolver_pasta  # noqa: E402

CORES = {"gabarito": "#52514e", "manual": "#2a78d6", "yolo26n": "#eb6834", "yolo26l": "#1baf7a"}
NOMES = {"gabarito": "Gabarito", "manual": "Manual (ao vivo)", "yolo26n": "YOLO26-n (nano)", "yolo26l": "YOLO26-l (large)"}
ROTULO_CLASSE = {"carro": "Carro", "moto": "Moto", "bicicleta": "Bicicleta", "pessoa": "Pessoa",
                 "cachorro": "Cachorro", "onibus": "Ônibus", "caminhao": "Caminhão", "caminhao_onibus": "Caminhão/\nônibus", "total": "Total", "todas": "Todas",
                 "nao_existe": "(não existe)", "nao_detectado": "(não detectado)"}
TINTA, TINTA_2, MUDO, GRADE, EIXO = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"

plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans", "sans-serif"],
    "font.size": 9,
    "axes.edgecolor": EIXO,
    "axes.linewidth": 0.8,
    "axes.labelcolor": TINTA_2,
    "axes.titlesize": 10,
    "axes.titlecolor": TINTA,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "axes.grid.axis": "y",
    "grid.color": GRADE,
    "grid.linewidth": 0.6,
    "axes.axisbelow": True,
    "xtick.color": MUDO,
    "ytick.color": MUDO,
    "xtick.labelcolor": TINTA_2,
    "ytick.labelcolor": TINTA_2,
    "legend.frameon": False,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})


def ler(pasta, nome):
    caminho = pasta / nome
    if not caminho.is_file():
        return None
    return pd.read_csv(caminho, sep=";", decimal=",", encoding="utf-8-sig")


def salvar(fig, pasta, nome, gerados):
    fig.savefig(pasta / nome)
    plt.close(fig)
    gerados.append(nome)


def barras_agrupadas(ax, df, categorias, metodos, col_cat, col_valor, col_metodo=None, rotular_zeros=False):
    """Barras lado a lado. df em formato largo (col por método) ou longo (col_metodo)."""
    n = len(metodos)
    largura = 0.8 / n
    x = np.arange(len(categorias))
    for i, m in enumerate(metodos):
        if col_metodo:
            serie = df[df[col_metodo] == m].set_index(col_cat)[col_valor]
        else:
            serie = df.set_index(col_cat)[m]
        y = serie.reindex(categorias).to_numpy(dtype=float)
        xs = x - 0.4 + largura * (i + 0.5)
        ax.bar(xs, y, largura, color=CORES[m], label=NOMES[m], edgecolor="white", linewidth=1.0)
        if rotular_zeros:  # barra de altura 0 é invisível: escreve "0" para não parecer dado faltando
            for xi, yi in zip(xs, y):
                if yi == 0:
                    ax.annotate("0", (xi, 0), xytext=(0, 2), textcoords="offset points", ha="center",
                                va="bottom", fontsize=7, color=TINTA_2)
    ax.set_xticks(x, [ROTULO_CLASSE.get(c, c) for c in categorias])
    ax.axhline(0, color=EIXO, linewidth=0.8)


def legenda_figura(fig, metodos):
    alcas = [plt.Rectangle((0, 0), 1, 1, color=CORES[m]) for m in metodos]
    fig.legend(alcas, [NOMES[m] for m in metodos], loc="upper center", ncol=len(metodos),
               bbox_to_anchor=(0.5, 1.02), handlelength=1.0, columnspacing=1.5)


def grade(n):
    cols = min(n, 2)
    return int(np.ceil(n / cols)), cols


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--teste", action="store_true")
    args = ap.parse_args()

    cfg = carregar_config()
    modelos = cfg["modelos"]
    base = resolver_pasta(cfg["pastas"]["resultados"]) / ("calibracao" if args.teste else "")
    tab, saida = base / "tabelas", base / "graficos"
    saida.mkdir(parents=True, exist_ok=True)
    gerados = []
    classes = ORDEM_CLASSES

    # G01 / G02: totais por classe em cada vídeo ----------------------------
    for arq, nome, titulo, metodos_base in [
        ("T01_totais_janela_completa.csv", "G01_totais_por_classe.png", "Total contado por classe (janela completa)", ["gabarito", "manual", *modelos]),
        ("T01b_totais_minutos_gabarito.csv", "G02_totais_minutos_gabarito.png", "Total por classe nos minutos do gabarito", ["gabarito", "manual", *modelos]),
    ]:
        df = ler(tab, arq)
        if df is None:
            continue
        metodos = [m for m in metodos_base if m in df.columns]
        videos = list(dict.fromkeys(df["video"]))
        nl, nc = grade(len(videos))
        fig, eixos = plt.subplots(nl, nc, figsize=(7.2 * nc / 2 + 1, 2.6 * nl), squeeze=False, sharey=False)
        for ax, vid in zip(eixos.flat, videos):
            d = df[(df["video"] == vid) & (df["classe"] != "total")]
            barras_agrupadas(ax, d, classes, metodos, "classe", None)
            ax.set_title(f"{d['periodo'].iloc[0]}", loc="left")
            ax.tick_params(axis="x", labelsize=7.5)
            ax.set_ylabel("objetos")
        for ax in list(eixos.flat)[len(videos):]:
            ax.set_visible(False)
        legenda_figura(fig, metodos)
        fig.suptitle(titulo, y=1.08, fontsize=11, color=TINTA)
        fig.tight_layout()
        salvar(fig, saida, nome, gerados)

    # G03 / G04: erro por classe (todos os vídeos) ---------------------------
    for arq, ref, sufixo in [("T03_erro_vs_gabarito.csv", "gabarito", "vs_gabarito"), ("T02_yolo_vs_manual.csv", "manual", "vs_manual")]:
        df = ler(tab, arq)
        if df is None:
            continue
        d = df[df["video"] == "todos"]
        metodos = [m for m in ["manual", *modelos] if m in set(d["metodo"])]
        texto_ref = "erro contra o gabarito" if ref == "gabarito" else "diferença em relação à contagem manual"
        for col, nome, rotulo, curto in [
            ("wape_pct", f"G03_wape_por_classe_{sufixo}.png", "WAPE (%)", "WAPE"),
            ("vies_pct", f"G04_vies_por_classe_{sufixo}.png", "viés (%)  ← conta a menos | conta a mais →", "Viés"),
        ]:
            fig, ax = plt.subplots(figsize=(7.2, 3.2))
            barras_agrupadas(ax, d, [*classes, "total"], metodos, "classe", col, col_metodo="metodo")
            # Tamanho da referência embaixo de cada classe: % sobre n=2 (ex.: cachorro) não é comparável a % sobre n=300.
            n_ref = d.drop_duplicates("classe").set_index("classe")["referencia"]
            ax.set_xticks(range(len(classes) + 1), [f"{ROTULO_CLASSE.get(c, c)}\n(n={int(n_ref.get(c, 0))})"
                                                    for c in [*classes, "total"]], fontsize=8)
            ax.set_ylabel(rotulo)
            ax.set_title(f"{curto} por classe — {texto_ref}, todos os vídeos", loc="left")
            ax.legend(loc="upper left", ncol=len(metodos), fontsize=8)
            salvar(fig, saida, nome, gerados)

    # G02: erro de CADA contagem por classe, em cada vídeo ---------------------
    df = ler(tab, "T03c_erro_por_classe_por_video.csv")
    if df is not None:
        videos = [v for v in dict.fromkeys(df["video"]) if v != "todos"]
        metodos = [m for m in ["manual", *modelos] if f"erro_{m}" in df.columns]
        nl, nc = grade(len(videos))
        fig, eixos = plt.subplots(nl, nc, figsize=(7.2 * nc / 2 + 1, 2.8 * nl), squeeze=False)
        for ax, vid in zip(eixos.flat, videos):
            d = df[(df["video"] == vid) & (df["classe"] != "total")]
            so_erros = d[["classe", *[f"erro_{m}" for m in metodos]]].rename(columns={f"erro_{m}": m for m in metodos})
            barras_agrupadas(ax, so_erros, classes, metodos, "classe", None,
                             rotular_zeros=True)
            ax.set_title(f"{d['periodo'].iloc[0]}  (gabarito: {int(df[(df['video'] == vid) & (df['classe'] == 'total')]['gabarito'].iloc[0])} objetos)",
                         loc="left")
            ax.tick_params(axis="x", labelsize=7.5)
            ax.set_ylabel("contagem − gabarito")
        for ax in list(eixos.flat)[len(videos):]:
            ax.set_visible(False)
        legenda_figura(fig, metodos)
        fig.suptitle("Erro de cada contagem por classe (acima de 0 = contou a mais; abaixo = contou a menos)",
                     y=1.08, fontsize=11, color=TINTA)
        fig.tight_layout()
        salvar(fig, saida, "G02_erro_por_classe_por_video.png", gerados)

    # G08 / G09: velocidade dos modelos -------------------------------------
    df = ler(tab, "T07_desempenho_modelos.csv")
    if df is not None:
        d = df[df["video"] == "média"]
        fig, ax = plt.subplots(figsize=(4.0, 2.8))
        ax.bar([NOMES[m] for m in d["modelo"]], d["quadros_por_segundo"], color=[CORES[m] for m in d["modelo"]], width=0.5)
        ax.axhline(30, color=TINTA_2, linewidth=1)
        ax.annotate("30 quadros/s = tempo real", xy=(1.0, 30), xycoords=("axes fraction", "data"), ha="right",
                    va="bottom", fontsize=8, color=TINTA_2)
        ax.set_ylabel("quadros processados por segundo")
        ax.set_title("Velocidade média de processamento (GPU)", loc="left")
        salvar(fig, saida, "G08_velocidade_modelos.png", gerados)

    # Só os vídeos que entraram nas tabelas (não mistura teste com experimento).
    pasta_yolo = resolver_pasta(cfg["pastas"]["resultados"]) / "yolo"
    d07 = ler(tab, "T07_desempenho_modelos.csv")
    videos_tab = set(d07["video"]) - {"média"} if d07 is not None else set()
    tempos = {}
    for m in modelos:
        arquivos = [pasta_yolo / v / m / "ms_por_quadro.csv" for v in sorted(videos_tab)]
        arquivos = [a for a in arquivos if a.is_file()]
        if arquivos:
            tempos[m] = pd.concat([pd.read_csv(a, sep=";")["ms"].iloc[30:] for a in arquivos]).to_numpy()
    if tempos:
        fig, ax = plt.subplots(figsize=(4.4, 2.8))
        partes = ax.boxplot(list(tempos.values()), tick_labels=[NOMES[m] for m in tempos], showfliers=False,
                            patch_artist=True, widths=0.45, medianprops={"color": TINTA, "linewidth": 1.5})
        for caixa, m in zip(partes["boxes"], tempos):
            caixa.set(facecolor=CORES[m], edgecolor=CORES[m], alpha=0.85)
        ax.set_ylabel("ms por quadro (detecção + rastreamento)")
        ax.set_title("Tempo de processamento por quadro", loc="left")
        salvar(fig, saida, "G09_tempo_por_quadro.png", gerados)

    # G10: precisão / revocação / F1 por classe -----------------------------
    df = ler(tab, "T05_precisao_revocacao.csv")
    if df is not None:
        d = df[df["video"] == "todos"]
        mods = [m for m in modelos if m in set(d["modelo"])]
        fig, eixos = plt.subplots(1, 3, figsize=(10.5, 3.0), sharey=True)
        for ax, col, tit in zip(eixos, ["precisao", "revocacao", "f1"], ["Precisão", "Revocação", "F1"]):
            barras_agrupadas(ax, d.rename(columns={"modelo": "metodo"}), [*classes, "todas"], mods, "classe", col, col_metodo="metodo")
            ax.set_title(tit, loc="left")
            ax.set_ylim(0, 1.05)
            ax.tick_params(axis="x", labelsize=7, rotation=45)
        legenda_figura(fig, mods)
        fig.suptitle("Desempenho por classe contra o gabarito (todos os vídeos)", y=1.10, fontsize=11, color=TINTA)
        fig.tight_layout()
        salvar(fig, saida, "G10_precisao_revocacao_f1.png", gerados)

    # G11: matrizes de confusão ---------------------------------------------
    for m in modelos:
        df = ler(tab, f"T06_confusao_{m}.csv")
        if df is None:
            continue
        mat = df.set_index("gabarito")
        fig, ax = plt.subplots(figsize=(5.6, 4.6))
        ax.grid(False)
        for lado in ax.spines.values():
            lado.set_visible(False)
        im = ax.imshow(mat.to_numpy(), cmap=matplotlib.colors.LinearSegmentedColormap.from_list(
            "azul", ["#ffffff", "#cde2fb", "#6da7ec", "#2a78d6", "#104281"]))
        ax.set_xticks(range(mat.shape[1]), [ROTULO_CLASSE.get(c, c) for c in mat.columns], rotation=45, ha="right")
        ax.set_yticks(range(mat.shape[0]), [ROTULO_CLASSE.get(c, c) for c in mat.index])
        limiar = mat.to_numpy().max() * 0.55
        for i in range(mat.shape[0]):
            for j in range(mat.shape[1]):
                v = mat.iat[i, j]
                if v:
                    ax.text(j, i, int(v), ha="center", va="center", fontsize=8, color="white" if v > limiar else TINTA)
        ax.set_xlabel("classe dada pelo modelo")
        ax.set_ylabel("classe no gabarito")
        ax.set_title(f"Matriz de confusão — {NOMES[m]}", loc="left")
        fig.colorbar(im, ax=ax, shrink=0.75, label="cruzamentos")
        salvar(fig, saida, f"G11_confusao_{m}.png", gerados)

    print(f"{len(gerados)} gráficos em {saida}:")
    for g in gerados:
        print("  ", g)


if __name__ == "__main__":
    main()
