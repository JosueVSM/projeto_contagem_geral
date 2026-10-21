"""Passo 4: comparar YOLO (2 modelos), contagem manual e gabarito -> tabelas.

Uso:
  python scripts/04_comparar.py           # vídeos do experimento (usar_na_analise = sim)
  python scripts/04_comparar.py --teste   # só vídeos de teste/calibração -> resultados/calibracao/

Só entra o que existir de verdade: se faltar a contagem manual ou o gabarito
de um vídeo, as tabelas que dependem deles simplesmente não incluem esse
vídeo (e o RESUMO.md avisa). Nenhum número é inventado.

Tabelas (CSV com ';' e vírgula decimal, abre direto no Excel):
  T01_totais_janela_completa.csv    total por classe: YOLO-n, YOLO-l, manual (10 min)
  T01b_totais_minutos_gabarito.csv  total por classe nos minutos revisados: + gabarito
  T02_yolo_vs_manual.csv            DIFERENÇA YOLO - manual por classe (manual como referência)
  T03_erro_vs_gabarito.csv          ERRO de cada método (manual, YOLO-n, YOLO-l) contra o gabarito
  T03b_erro_por_classe_todos.csv    erro por classe, somando os vídeos (contagens + WAPE)
  T03c_erro_por_classe_por_video.csv  ERRO DE CADA CONTAGEM por classe e vídeo: contagem, erro (contagem − gabarito) e erro %
  T05_precisao_revocacao.csv        precisão / revocação / F1 por classe (só se o gabarito for por evento)
  T06_confusao_<modelo>.csv         matriz de confusão gabarito x modelo (só se o gabarito for por evento)
  T07_desempenho_modelos.csv        velocidade de processamento de cada modelo
  RESUMO.md                         principais tabelas em Markdown

(Por decisão do trabalho, NÃO há análise por minuto nem por horário: o foco é o erro por classe.)
"""

import _caminhos  # noqa: F401
import argparse
import json
import math

import numpy as np
import pandas as pd

from configuracao import ORDEM_CLASSES, carregar_config, interpretar_minutos, ler_csv_flexivel, ler_videos, resolver_pasta
from dados import ler_gabarito, ler_gabarito_contagem, ler_manual
from metricas import (
    agregar_blocos,
    avaliar_eventos,
    contagem_por_minuto,
    erro_contagem,
    filtrar_minutos,
    matriz_confusao,
)


def salvar(df: pd.DataFrame, pasta, nome, index=False):
    df.to_csv(pasta / nome, sep=";", decimal=",", index=index, encoding="utf-8-sig")


def tabela_md(df: pd.DataFrame) -> str:
    def fmt(x):
        if isinstance(x, float):
            return "—" if np.isnan(x) else f"{x:.3g}".replace(".", ",") if abs(x) < 1 else f"{x:.1f}".replace(".", ",")
        return str(x)

    cab = "| " + " | ".join(map(str, df.columns)) + " |"
    sep = "|" + "---|" * len(df.columns)
    linhas = ["| " + " | ".join(fmt(x) for x in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join([cab, sep, *linhas])


def empilhar(tabelas: list[pd.DataFrame]) -> pd.DataFrame:
    """Junta tabelas minuto x classe de vários vídeos, renumerando as linhas."""
    return pd.concat(tabelas, ignore_index=True) if tabelas else pd.DataFrame(columns=ORDEM_CLASSES)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--teste", action="store_true", help="usa só os vídeos de teste (usar_na_analise = nao)")
    args = ap.parse_args()

    cfg = carregar_config()
    modelos = cfg["modelos"]
    tol = float(cfg["comparacao"]["tolerancia_s"])
    pasta_res = resolver_pasta(cfg["pastas"]["resultados"])
    saida = pasta_res / ("calibracao" if args.teste else "") / "tabelas"
    saida.mkdir(parents=True, exist_ok=True)

    videos = ler_videos(cfg)
    videos = videos[videos["usar"] != args.teste]

    t01, t01b, t02, t03, t05, t07 = [], [], [], [], [], []
    pilhas = {}  # (referencia, metodo) -> {"ref": [...], "met": [...]} para os totais "todos"
    confusao = {m: None for m in modelos}
    gab_todos, pred_todos = [], {m: [] for m in modelos}
    avisos = []

    for ordem, (_, v) in enumerate(videos.iterrows()):
        vid, periodo = v["id"], v["periodo"]
        inicio = v["inicio_contagem_s"] if v["inicio_contagem_s"] is not None and not pd.isna(v["inicio_contagem_s"]) else 0.0
        dur = v["duracao_s"]
        todos_min = list(range(1, math.ceil(dur / 60) + 1))
        base = {"video": vid, "periodo": periodo}

        tabelas, eventos = {}, {}
        for m in modelos:
            pasta = pasta_res / "yolo" / vid / m
            if (pasta / "eventos.csv").is_file():
                ev = ler_csv_flexivel(pasta / "eventos.csv")
                ev["t_video_s"] = ev["t_video_s"].astype(float) if len(ev) else pd.Series(dtype=float)
                eventos[m] = ev[["t_video_s", "classe"]] if len(ev) else pd.DataFrame(columns=["t_video_s", "classe"])
                tabelas[m] = contagem_por_minuto(eventos[m], inicio, dur)
                with open(pasta / "desempenho.json", encoding="utf-8") as f:
                    t07.append(json.load(f) | base)  # base por último: mantém o id do vídeo
            else:
                avisos.append(f"{vid}: sem resultado do {m} (rode o passo 2)")
        manual = ler_manual(vid, len(todos_min))  # por minuto, por blocos ou total
        if manual is None:
            avisos.append(f"{vid}: sem contagem manual (dados/manual/{vid}.csv)")
        elif not manual.por_minuto and list(manual.blocos) != ["total"]:
            avisos.append(f"{vid}: contagem manual em blocos {list(manual.blocos)} -> sem análise minuto a minuto do humano")
        gab = ler_gabarito(vid)  # gabarito por evento (ferramenta 03)
        gab_cont = ler_gabarito_contagem(vid, len(todos_min)) if gab is None else None  # gabarito só com contagens
        min_gab = interpretar_minutos(v["minutos_gabarito"])
        if gab is not None:
            tabelas["gabarito"] = contagem_por_minuto(gab, inicio, dur).reindex(min_gab, fill_value=0)
        elif gab_cont is not None:
            pass  # gabarito só com o total: é o formato esperado no experimento
        else:
            avisos.append(f"{vid}: sem gabarito (dados/gabarito/{vid}.csv)")
        if not tabelas and manual is None and gab_cont is None:
            continue

        # Blocos da contagem manual que estão inteiros dentro dos minutos do gabarito.
        blocos_gab_manual = {r: ms for r, ms in manual.blocos.items() if set(ms) <= set(min_gab)} if manual else {}
        manual_cobre_gab = bool(blocos_gab_manual) and sorted(
            m for ms in blocos_gab_manual.values() for m in ms) == sorted(min_gab)

        # --- totais ---------------------------------------------------------
        totais = {k: tabelas[k].sum() for k in modelos if k in tabelas}
        if manual is not None:
            totais["manual"] = manual.tabela.sum()
            if manual.minutos != todos_min:
                avisos.append(f"{vid}: contagem manual cobre os minutos {manual.minutos}, janela é {todos_min[0]}..{todos_min[-1]}")
        if gab_cont is not None and gab_cont.minutos == todos_min:
            totais = {"gabarito": gab_cont.tabela.sum(), **totais}
        if totais:
            t = pd.DataFrame(totais)
            t.loc["total"] = t.sum()
            t01.append(t.reset_index(names="classe").assign(**base))
        if "gabarito" in tabelas:
            totais = {k: tabelas[k].loc[min_gab].sum() for k in ["gabarito", *modelos] if k in tabelas}
            if manual_cobre_gab:
                totais["manual"] = manual.tabela.loc[list(blocos_gab_manual)].sum()
            t = pd.DataFrame(totais)
            t.loc["total"] = t.sum()
            t01b.append(t.reset_index(names="classe").assign(**base, minutos=v["minutos_gabarito"]))

        # --- referências: manual (diferença) e gabarito (erro) ------------
        # Cada comparação: (referência, método, tabela ref, tabela método, blocos)
        comparacoes = []
        if manual is not None:
            comparacoes += [("manual", m, manual.tabela, agregar_blocos(tabelas[m], manual.blocos), manual.blocos)
                            for m in modelos if m in tabelas]
        if "gabarito" in tabelas:
            por_min = {mm: [mm] for mm in min_gab}
            comparacoes += [("gabarito", m, tabelas["gabarito"], tabelas[m].reindex(min_gab, fill_value=0), por_min)
                            for m in modelos if m in tabelas]
            if blocos_gab_manual:
                comparacoes.append(("gabarito", "manual", agregar_blocos(tabelas["gabarito"], blocos_gab_manual),
                                    manual.tabela, blocos_gab_manual))
            elif manual is not None:
                avisos.append(f"{vid}: nenhum bloco da contagem manual cabe nos minutos do gabarito "
                              f"({v['minutos_gabarito']}) -> erro do humano contra o gabarito não calculado")
        if gab_cont is not None:
            bl = gab_cont.blocos
            comparacoes += [("gabarito", m, gab_cont.tabela, agregar_blocos(tabelas[m], bl), bl)
                            for m in modelos if m in tabelas]
            if manual is not None and manual.blocos == bl:
                comparacoes.append(("gabarito", "manual", gab_cont.tabela, manual.tabela, bl))
            elif manual is not None and manual.por_minuto:
                comparacoes.append(("gabarito", "manual", gab_cont.tabela,
                                    agregar_blocos(manual.tabela_por_minuto(), bl), bl))
            elif manual is not None:
                avisos.append(f"{vid}: blocos da contagem manual {list(manual.blocos)} diferentes dos do gabarito "
                              f"{list(bl)} -> erro do humano não calculado")
        for ref_nome, met_nome, ref, met, blocos in comparacoes:
            rotulos = list(blocos)
            n_min = sum(len(ms) for ms in blocos.values())
            e = erro_contagem(ref, met, rotulos, n_min).assign(**base, metodo=met_nome, referencia_tipo=ref_nome)
            (t02 if ref_nome == "manual" else t03).append(e)
            p = pilhas.setdefault((ref_nome, met_nome), {"ref": [], "met": [], "n_min": 0})
            p["ref"].append(ref.loc[rotulos])
            p["met"].append(met.loc[rotulos])
            p["n_min"] += n_min

        # --- precisão / revocação por evento (só com gabarito) ------------
        if gab is not None:
            ref_ev = filtrar_minutos(gab, inicio, min_gab)
            deslocamento = ordem * 100000.0  # evita casar eventos de vídeos diferentes no total
            gab_todos.append(ref_ev.assign(t_video_s=ref_ev["t_video_s"] + deslocamento))
            for m in modelos:
                if m not in eventos:
                    continue
                pred_ev = filtrar_minutos(eventos[m], inicio, min_gab)
                t05.append(avaliar_eventos(ref_ev, pred_ev, tol).assign(**base, modelo=m))
                pred_todos[m].append(pred_ev.assign(t_video_s=pred_ev["t_video_s"] + deslocamento))
                mc = matriz_confusao(ref_ev, pred_ev, tol)
                confusao[m] = mc if confusao[m] is None else confusao[m] + mc

    # ---------------------------------------------------------------------
    # Totais "todos os vídeos"
    for (ref_nome, met_nome), p in pilhas.items():
        r, x = empilhar(p["ref"]), empilhar(p["met"])
        e = erro_contagem(r, x, list(r.index), p["n_min"]).assign(
            video="todos", periodo="todos", metodo=met_nome, referencia_tipo=ref_nome)
        (t02 if ref_nome == "manual" else t03).append(e)
    if gab_todos:
        g = pd.concat(gab_todos, ignore_index=True)
        for m in modelos:
            if pred_todos[m]:
                pr = pd.concat(pred_todos[m], ignore_index=True)
                t05.append(avaliar_eventos(g, pr, tol).assign(video="todos", periodo="todos", modelo=m))

    ordem_cols = lambda df, primeiras: df[[*primeiras, *[c for c in df.columns if c not in primeiras]]]  # noqa: E731
    resumo = ["# Resumo dos resultados", ""]
    if args.teste:
        resumo += ["> **ATENÇÃO: vídeos de TESTE/CALIBRAÇÃO. Estes números NÃO são resultados do experimento.**", ""]
    if avisos:
        resumo += ["## Observações sobre os dados", "", *[f"- {a}" for a in avisos], ""]

    def publicar(lista, nome, primeiras, titulo=None, filtro=None):
        if not lista:
            return None
        df = ordem_cols(pd.concat(lista, ignore_index=True), primeiras)
        salvar(df, saida, nome)
        if titulo:
            vis = df if filtro is None else filtro(df)
            resumo.extend([f"## {titulo}", "", tabela_md(vis), ""])
        return df

    d01 = publicar(t01, "T01_totais_janela_completa.csv", ["video", "periodo", "classe"])
    publicar(t01b, "T01b_totais_minutos_gabarito.csv", ["video", "periodo", "minutos", "classe"], "Totais nos minutos do gabarito")
    # Sem colunas "por minuto": o trabalho analisa só o erro por classe nos 10 min.
    def sem_minuto(lista):
        return [d.drop(columns=["eam_por_minuto", "n_minutos", "n_blocos"], errors="ignore") for d in lista]

    publicar(sem_minuto(t02), "T02_yolo_vs_manual.csv", ["video", "periodo", "referencia_tipo", "metodo", "classe"])
    d03 = publicar(sem_minuto(t03), "T03_erro_vs_gabarito.csv", ["video", "periodo", "referencia_tipo", "metodo", "classe"])
    if d03 is not None:
        tod = d03[(d03["video"] == "todos") & (d03["classe"] != "total")]
        if not tod.empty:
            piv = tod.pivot_table(index="classe", columns="metodo", values=["referencia", "contagem_metodo", "wape_pct", "vies_pct"],
                                  sort=False, aggfunc="first")
            tabela = pd.DataFrame({"classe": [c for c in ORDEM_CLASSES if c in piv.index]})
            tabela["gabarito"] = [int(piv.loc[c, ("referencia", tod["metodo"].iloc[0])]) for c in tabela["classe"]]
            for m in dict.fromkeys(tod["metodo"]):
                tabela[f"{m}"] = [int(piv.loc[c, ("contagem_metodo", m)]) for c in tabela["classe"]]
            for m in dict.fromkeys(tod["metodo"]):
                tabela[f"WAPE_{m}"] = [piv.loc[c, ("wape_pct", m)] for c in tabela["classe"]]
            salvar(tabela, saida, "T03b_erro_por_classe_todos.csv")
            resumo.extend(["## Erro contra o gabarito por classe (soma dos vídeos)", "", tabela_md(tabela), "",
                           "Colunas sem prefixo = total contado; WAPE_ = erro percentual contra o gabarito.", ""])
    # T03c: o erro de CADA contagem, por classe e por vídeo (+ soma dos vídeos)
    if d01 is not None and "gabarito" in d01.columns:
        com_gab = d01[d01["gabarito"].notna()]
        soma = (com_gab.groupby("classe", sort=False).sum(numeric_only=True).reset_index()
                .assign(video="todos", periodo="todos"))
        tab = pd.concat([com_gab, soma], ignore_index=True)
        metodos_t = [m for m in ["manual", *modelos] if m in tab.columns]
        cols = ["video", "periodo", "classe", "gabarito"]
        for m in metodos_t:
            tab[f"erro_{m}"] = tab[m] - tab["gabarito"]
            tab[f"erro_pct_{m}"] = np.where(tab["gabarito"] > 0,
                                            (100 * tab[f"erro_{m}"] / tab["gabarito"].where(tab["gabarito"] > 0)).round(1),
                                            np.nan)
            cols += [m, f"erro_{m}", f"erro_pct_{m}"]
        tab = tab[cols]
        for c in ["gabarito", *metodos_t, *[f"erro_{m}" for m in metodos_t]]:
            tab[c] = tab[c].astype(int)
        salvar(tab, saida, "T03c_erro_por_classe_por_video.csv")
        for vid in dict.fromkeys(tab["video"]):
            t = tab[tab["video"] == vid].drop(columns=["video", "periodo"])
            per = tab.loc[tab["video"] == vid, "periodo"].iloc[0]
            titulo = "Soma dos 4 vídeos" if vid == "todos" else f"{vid} ({per})"
            resumo.extend([f"## Erro de cada contagem por classe — {titulo}", "", tabela_md(t), ""])
        resumo.extend(["erro = contagem − gabarito (negativo = contou a menos); erro_pct = erro ÷ gabarito.", ""])

    publicar(t05, "T05_precisao_revocacao.csv", ["video", "periodo", "modelo", "classe"],
             "Precisão / revocação (todas as classes)", lambda d: d[d["classe"] == "todas"])

    for m, mc in confusao.items():
        if mc is not None:
            salvar(mc, saida, f"T06_confusao_{m}.csv", index=True)
            resumo.extend([f"## Matriz de confusão — {m}", "", tabela_md(mc.reset_index()), ""])

    if t07:
        d07 = pd.DataFrame(t07)
        cols = ["video", "periodo", "modelo", "quadros_processados", "tempo_total_s", "quadros_por_segundo",
                "ms_por_quadro_deteccao_rastreamento_mediana", "ms_inferencia_mediana", "tempo_real_x", "memoria_gpu_pico_mb", "gpu"]
        d07 = d07[[c for c in cols if c in d07.columns]]
        media = d07.groupby("modelo", sort=False).mean(numeric_only=True).round(2).reset_index().assign(video="média", periodo="")
        d07 = pd.concat([d07, media], ignore_index=True)
        salvar(d07, saida, "T07_desempenho_modelos.csv")
        resumo.extend(["## Desempenho (velocidade)", "", tabela_md(d07[d07["video"] == "média"]), ""])

    (saida / "RESUMO.md").write_text("\n".join(resumo), encoding="utf-8")
    print(f"Tabelas salvas em {saida}")
    for a in avisos:
        print(f"[aviso] {a}")


if __name__ == "__main__":
    main()
