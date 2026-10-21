"""Métricas de comparação entre métodos de contagem.

Vocabulário usado no trabalho:
  - referência: a contagem considerada "verdade" (o gabarito; ou, na falta
    dele, a contagem manual, deixando claro que aí medimos só DIFERENÇA).
  - erro por minuto e(m) = contagem_metodo(m) - contagem_referencia(m)
  - viés = soma dos erros (positivo = conta a mais, negativo = conta a menos)
  - EAM (erro absoluto médio) = média de |e(m)| por minuto
  - WAPE = soma |e(m)| / soma referência  (erro percentual que não "explode"
    em minutos com zero objetos, ao contrário do erro % minuto a minuto)
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import linear_sum_assignment

from configuracao import ORDEM_CLASSES, classe_analise


# ----------------------------------------------------------------------
# Contagem por minuto
# ----------------------------------------------------------------------
def minuto_relativo(t_video_s, inicio_s: float):
    """Minuto da contagem (1, 2, ...) a partir do tempo absoluto no vídeo."""
    return np.floor((np.asarray(t_video_s, dtype=float) - inicio_s) / 60.0).astype(int) + 1


def contagem_por_minuto(eventos: pd.DataFrame, inicio_s: float, duracao_s: float) -> pd.DataFrame:
    """Tabela minuto x classe a partir de eventos (colunas t_video_s, classe).

    Só entram eventos dentro da janela [inicio, inicio + duração).
    """
    n_min = math.ceil(duracao_s / 60.0)
    tabela = pd.DataFrame(0, index=pd.RangeIndex(1, n_min + 1, name="minuto"), columns=ORDEM_CLASSES)
    if eventos is None or len(eventos) == 0:
        return tabela
    t_rel = eventos["t_video_s"].astype(float) - inicio_s
    dentro = eventos[(t_rel >= 0) & (t_rel < duracao_s)].copy()
    dentro["classe"] = dentro["classe"].map(classe_analise)
    dentro["minuto"] = minuto_relativo(dentro["t_video_s"], inicio_s)
    contagem = dentro.groupby(["minuto", "classe"]).size().unstack(fill_value=0)
    return contagem.reindex(index=tabela.index, columns=ORDEM_CLASSES, fill_value=0).astype(int)


def agregar_blocos(tabela_min: pd.DataFrame, blocos: dict[str, list[int]]) -> pd.DataFrame:
    """Soma uma tabela minuto x classe nos mesmos blocos da contagem manual.

    Ex.: blocos {"1-3": [1,2,3], "total": [1..10]} -> uma linha por bloco.
    """
    linhas = {r: tabela_min.reindex(ms, fill_value=0).sum() for r, ms in blocos.items()}
    out = pd.DataFrame(linhas).T.reindex(columns=ORDEM_CLASSES, fill_value=0).astype(int)
    out.index.name = "bloco"
    return out


def filtrar_minutos(eventos: pd.DataFrame, inicio_s: float, minutos: list[int]) -> pd.DataFrame:
    if eventos is None or len(eventos) == 0:
        return pd.DataFrame(columns=["t_video_s", "classe"])
    m = minuto_relativo(eventos["t_video_s"], inicio_s)
    return eventos[np.isin(m, minutos)].reset_index(drop=True)


# ----------------------------------------------------------------------
# Erro de contagem (comparação de totais por minuto)
# ----------------------------------------------------------------------
def erro_contagem(ref: pd.DataFrame, metodo: pd.DataFrame, minutos: list | None = None,
                  n_minutos: int | None = None) -> pd.DataFrame:
    """Erro do método contra a referência, por classe, + linha 'total'.

    ref e metodo: tabelas (minuto ou bloco) x classe, com as MESMAS linhas.
    minutos: quais linhas usar (padrão: as comuns às duas tabelas).
    n_minutos: quantos minutos as linhas cobrem no total. Se as linhas forem
      blocos (ex.: "1-3") ou "total", o EAM é dividido pelos minutos, não
      pelos blocos. ATENÇÃO: com blocos, erros de sinais opostos dentro do
      mesmo bloco se cancelam, então o EAM fica subestimado.
    """
    minutos = list(minutos) if minutos is not None else [i for i in ref.index if i in set(metodo.index)]
    r = ref.reindex(minutos).fillna(0)
    m = metodo.reindex(minutos).fillna(0)
    e = m - r
    n_min = n_minutos or len(minutos)
    linhas = []
    for c in [*ORDEM_CLASSES, "total"]:
        if c == "total":
            soma_r, soma_m = r.values.sum(), m.values.sum()
            abs_soma = np.abs(e.values).sum()
            eam = np.abs(e.values).sum() / n_min  # erro absoluto por minuto somando as classes
        else:
            soma_r, soma_m = r[c].sum(), m[c].sum()
            abs_soma = e[c].abs().sum()
            eam = e[c].abs().sum() / n_min
        linhas.append(
            {
                "classe": c,
                "referencia": int(soma_r),
                "contagem_metodo": int(soma_m),
                "vies": int(soma_m - soma_r),
                "vies_pct": round(100 * (soma_m - soma_r) / soma_r, 1) if soma_r else np.nan,
                "eam_por_minuto": round(float(eam), 2),
                "wape_pct": round(100 * abs_soma / soma_r, 1) if soma_r else np.nan,
                "n_minutos": n_min,
                "n_blocos": len(minutos),
            }
        )
    return pd.DataFrame(linhas)


# ----------------------------------------------------------------------
# Casamento de eventos (precisão / revocação)
# ----------------------------------------------------------------------
def casar_eventos(t_ref, t_pred, tolerancia_s: float) -> list[tuple[int, int]]:
    """Casa cada evento previsto com no máximo um evento de referência.

    Usa o algoritmo húngaro (linear_sum_assignment), que minimiza a soma das
    diferenças de tempo; pares com diferença > tolerância são rejeitados.
    """
    t_ref = np.asarray(t_ref, dtype=float)
    t_pred = np.asarray(t_pred, dtype=float)
    if len(t_ref) == 0 or len(t_pred) == 0:
        return []
    custo = np.abs(t_ref[:, None] - t_pred[None, :])
    grande = 1e6
    custo_ok = np.where(custo <= tolerancia_s, custo, grande)
    linhas, colunas = linear_sum_assignment(custo_ok)
    return [(int(i), int(j)) for i, j in zip(linhas, colunas) if custo[i, j] <= tolerancia_s]


def avaliar_eventos(ref: pd.DataFrame, pred: pd.DataFrame, tolerancia_s: float) -> pd.DataFrame:
    """Precisão, revocação e F1 por classe (o casamento exige a MESMA classe)."""
    ref = ref.assign(classe=ref["classe"].map(classe_analise))
    pred = pred.assign(classe=pred["classe"].map(classe_analise))
    linhas = []
    tot_vp = tot_fp = tot_fn = 0
    for c in ORDEM_CLASSES:
        r = ref[ref["classe"] == c]["t_video_s"].to_numpy()
        p = pred[pred["classe"] == c]["t_video_s"].to_numpy()
        vp = len(casar_eventos(r, p, tolerancia_s))
        fp, fn = len(p) - vp, len(r) - vp
        tot_vp, tot_fp, tot_fn = tot_vp + vp, tot_fp + fp, tot_fn + fn
        linhas.append(_linha_prf(c, vp, fp, fn))
    linhas.append(_linha_prf("todas", tot_vp, tot_fp, tot_fn))
    return pd.DataFrame(linhas)


def _linha_prf(classe, vp, fp, fn) -> dict:
    prec = vp / (vp + fp) if vp + fp else np.nan
    rev = vp / (vp + fn) if vp + fn else np.nan
    f1 = 2 * prec * rev / (prec + rev) if (vp and prec + rev) else (0.0 if vp + fp + fn else np.nan)
    return {
        "classe": classe,
        "vp": vp,
        "fp": fp,
        "fn": fn,
        "precisao": round(prec, 3) if not np.isnan(prec) else np.nan,
        "revocacao": round(rev, 3) if not np.isnan(rev) else np.nan,
        "f1": round(f1, 3) if not np.isnan(f1) else np.nan,
    }


def matriz_confusao(ref: pd.DataFrame, pred: pd.DataFrame, tolerancia_s: float) -> pd.DataFrame:
    """Linhas = classe no gabarito, colunas = classe dada pelo modelo.

    Casamento em duas etapas:
      1) casa eventos da MESMA classe (como na precisão/revocação);
      2) o que sobrou é casado só pelo tempo -> revela trocas como carro -> caminhão.
    Sem a etapa 1, uma moto e um carro cruzando juntos poderiam ser casados
    "trocados" e aparecer como confusão falsa.
    'nao_detectado' = gabarito sem par; linha 'nao_existe' = modelo contou
    algo que o gabarito não tem (falso positivo).
    """
    ref = ref.reset_index(drop=True).assign(classe=lambda d: d["classe"].map(classe_analise))
    pred = pred.reset_index(drop=True).assign(classe=lambda d: d["classe"].map(classe_analise))
    pares = []
    for c in ORDEM_CLASSES:
        ir = np.flatnonzero(ref["classe"].to_numpy() == c)
        ip = np.flatnonzero(pred["classe"].to_numpy() == c)
        pares += [(ir[i], ip[j]) for i, j in casar_eventos(ref["t_video_s"].iloc[ir], pred["t_video_s"].iloc[ip], tolerancia_s)]
    sobra_r = np.setdiff1d(np.arange(len(ref)), [i for i, _ in pares]).astype(int)
    sobra_p = np.setdiff1d(np.arange(len(pred)), [j for _, j in pares]).astype(int)
    pares += [(sobra_r[i], sobra_p[j]) for i, j in casar_eventos(
        ref["t_video_s"].iloc[sobra_r], pred["t_video_s"].iloc[sobra_p], tolerancia_s)]

    rotulos_l = [*ORDEM_CLASSES, "nao_existe"]
    rotulos_c = [*ORDEM_CLASSES, "nao_detectado"]
    m = pd.DataFrame(0, index=pd.Index(rotulos_l, name="gabarito"), columns=pd.Index(rotulos_c, name="modelo"))
    usados_r, usados_p = set(), set()
    for i, j in pares:
        m.loc[ref["classe"].iloc[i], pred["classe"].iloc[j]] += 1
        usados_r.add(i)
        usados_p.add(j)
    for i in set(range(len(ref))) - usados_r:
        m.loc[ref["classe"].iloc[i], "nao_detectado"] += 1
    for j in set(range(len(pred))) - usados_p:
        m.loc["nao_existe", pred["classe"].iloc[j]] += 1
    return m


# ----------------------------------------------------------------------
# Tendência ao longo do vídeo (indício de cansaço)
# ----------------------------------------------------------------------
def tendencia(minutos, erro_abs) -> dict:
    """Inclinação da reta erro x minuto e correlação de Spearman.

    Inclinação > 0 com p pequeno sugere que o erro cresce com o tempo.
    Com poucos minutos (ex.: 6 ou 10) o teste tem pouco poder: o resultado
    deve ser apresentado como indício, não como prova.
    """
    x = np.asarray(minutos, dtype=float)
    y = np.asarray(erro_abs, dtype=float)
    if len(x) < 3 or np.all(y == y[0]):
        return {"n": len(x), "inclinacao_por_min": np.nan, "p_regressao": np.nan, "spearman_rho": np.nan, "p_spearman": np.nan}
    reg = stats.linregress(x, y)
    rho, p_rho = stats.spearmanr(x, y)
    return {
        "n": len(x),
        "inclinacao_por_min": round(float(reg.slope), 3),
        "p_regressao": round(float(reg.pvalue), 4),
        "spearman_rho": round(float(rho), 3),
        "p_spearman": round(float(p_rho), 4),
    }
