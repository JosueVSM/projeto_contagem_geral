"""Painel dos resultados (Streamlit): erro de cada contagem por classe.

Uso (a partir da raiz do projeto, com o ambiente virtual ativado):
  streamlit run app/painel.py

Lê SOMENTE o que os scripts 04, 05 e 06 já gravaram. Não calcula nada novo e
não inventa valores: se uma tabela não existe, a aba avisa qual script rodar.
"""

import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
from configuracao import ORDEM_CLASSES, carregar_config, resolver_pasta  # noqa: E402

CORES = {"manual": "#2a78d6", "yolo26n": "#eb6834", "yolo26l": "#1baf7a"}
NOMES = {"gabarito": "Gabarito", "manual": "Manual (ao vivo)", "yolo26n": "YOLO26-n (nano)", "yolo26l": "YOLO26-l (large)"}
ROTULO = {"carro": "Carro", "moto": "Moto", "bicicleta": "Bicicleta", "pessoa": "Pessoa", "cachorro": "Cachorro",
          "onibus": "Ônibus", "caminhao": "Caminhão", "caminhao_onibus": "Caminhão/ônibus", "total": "Total"}

st.set_page_config(page_title="Contagem de tráfego — erro por classe", layout="wide", initial_sidebar_state="collapsed")
cfg = carregar_config()
PASTA_RES = resolver_pasta(cfg["pastas"]["resultados"])
PASTA_TAB = PASTA_RES / "tabelas"
PASTA_GRAF = PASTA_RES / "graficos"
PASTA_DEMO = resolver_pasta(cfg["pastas"].get("videos_demo", "~/dados_visao/videos_demo"))


@st.cache_data
def _ler_csv(caminho: str, modificado_em: float):
    # 'modificado_em' entra na chave do cache: se o arquivo mudar, o painel relê sozinho.
    return pd.read_csv(caminho, sep=";", decimal=",", encoding="utf-8-sig")


def ler(nome: str):
    caminho = PASTA_TAB / nome
    if not caminho.is_file():
        return None
    return _ler_csv(str(caminho), caminho.stat().st_mtime)


def fmt_erro(erro, pct, hifen=False):
    """'−3 (−12,0 %)'; sem % quando o gabarito é 0.

    hifen=True usa o hífen comum (-): o st.metric só desenha a seta para baixo
    quando o texto começa com ele (o sinal tipográfico − ele não reconhece).
    """
    sinal = "+" if erro > 0 else (("-" if hifen else "−") if erro < 0 else "")
    txt = f"{sinal}{abs(int(erro))}"
    if pd.notna(pct):
        txt += f" ({sinal}{abs(pct):.1f} %)".replace(".", ",")
    return txt


st.title("Contagem classificada de tráfego — erro por classe")
st.caption("Referência = **gabarito** (contagem minuciosa assistindo ao vídeo, feita por Gabriela Passos, que não "
           "participou da filmagem nem da contagem ao vivo). "
           "Erro = contagem − gabarito: **positivo = contou a mais, negativo = contou a menos**.")

aba_erro, aba_noite, aba_videos, aba_vel, aba_graf = st.tabs(
    ["Erro por classe", "Dia × noite", "Vídeos (demonstração)", "Velocidade dos modelos", "Gráficos (PNG)"])

# --- Erro por classe ----------------------------------------------------
with aba_erro:
    t = ler("T03c_erro_por_classe_por_video.csv")
    if t is None:
        st.info("Ainda não há a tabela de erro por classe. Rode `python scripts/04_comparar.py`.")
    else:
        metodos = [m for m in ["manual", *cfg["modelos"]] if m in t.columns]
        videos = list(dict.fromkeys(t["video"]))
        rotulo_video = {v: ("Soma dos 4 vídeos" if v == "todos" else f"{v} — {t.loc[t['video'] == v, 'periodo'].iloc[0]}")
                        for v in videos}
        ordem = ["todos", *[v for v in videos if v != "todos"]]
        vid = st.radio("Vídeo", ordem, format_func=rotulo_video.get, horizontal=True)
        d = t[t["video"] == vid]
        tot = d[d["classe"] == "total"].iloc[0]

        cols = st.columns(len(metodos) + 1)
        cols[0].metric("Gabarito (total)", int(tot["gabarito"]))
        for c, m in zip(cols[1:], metodos):
            c.metric(NOMES[m], int(tot[m]), fmt_erro(tot[f"erro_{m}"], tot[f"erro_pct_{m}"], hifen=True), delta_color="off")

        st.subheader("Contagem e erro de cada método, por classe")
        linhas = []
        for _, r in d.iterrows():
            linha = {"Classe": ROTULO.get(r["classe"], r["classe"]), "Gabarito": int(r["gabarito"])}
            for m in metodos:
                linha[NOMES[m]] = int(r[m])
                linha[f"Erro {NOMES[m].split(' (')[0]}"] = fmt_erro(r[f"erro_{m}"], r[f"erro_pct_{m}"])
            linhas.append(linha)
        st.dataframe(pd.DataFrame(linhas), hide_index=True, width="stretch")

        st.subheader("Erro por classe (contagem − gabarito)")
        longo = d[d["classe"] != "total"].melt(id_vars="classe", value_vars=[f"erro_{m}" for m in metodos],
                                              var_name="metodo", value_name="erro")
        longo["metodo"] = longo["metodo"].str.replace("erro_", "", regex=False)
        longo["Método"] = longo["metodo"].map(NOMES)
        longo["Classe"] = longo["classe"].map(lambda c: ROTULO.get(c, c))
        grafico = (
            alt.Chart(longo)
            .mark_bar()
            .encode(
                x=alt.X("Classe:N", sort=[ROTULO.get(c, c) for c in ORDEM_CLASSES], title=None,
                        axis=alt.Axis(labelAngle=0)),
                xOffset=alt.XOffset("Método:N", sort=[NOMES[m] for m in metodos]),
                y=alt.Y("erro:Q", title="contagem − gabarito"),
                color=alt.Color("Método:N", scale=alt.Scale(domain=[NOMES[m] for m in metodos],
                                                            range=[CORES[m] for m in metodos]),
                                legend=alt.Legend(orient="top", title=None)),
                tooltip=["Método", "Classe", alt.Tooltip("erro:Q", title="erro")],
            )
            .properties(height=340)
        )
        regra = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color="#898781").encode(y="y:Q")
        st.altair_chart(grafico + regra, width="stretch")

        if vid == "todos":
            w = ler("T03b_erro_por_classe_todos.csv")
            if w is not None:
                st.subheader("Erro sem compensação entre vídeos (WAPE)")
                st.caption("Na soma, um vídeo com erro +5 e outro com −5 se anulam. O **WAPE** soma os erros de cada "
                           "vídeo **sem sinal** e divide pelo gabarito: mostra o quanto cada método erra de verdade.")
                tabela = pd.DataFrame({"Classe": w["classe"].map(lambda c: ROTULO.get(c, c)),
                                       "Gabarito": w["gabarito"].astype(int)})
                for m in metodos:
                    if f"WAPE_{m}" in w.columns:
                        tabela[f"WAPE {NOMES[m]}"] = w[f"WAPE_{m}"].map(lambda x: f"{x:.1f} %".replace(".", ","))
                st.dataframe(tabela, hide_index=True, width="stretch")
                st.caption("Cachorro (n = 2) e caminhão/ônibus (n = 5) têm amostra muito pequena: o % é instável.")

# --- Dia × noite -------------------------------------------------------
with aba_noite:
    t = ler("T04_dia_x_noite.csv")
    if t is None:
        st.info("Ainda não há a tabela dia × noite. Rode `python scripts/04_comparar.py`.")
    else:
        metodos = [m for m in ["manual", *cfg["modelos"]] if f"erro_{m}" in t.columns]
        st.caption("Mesmos números da aba **Erro por classe**, lado a lado: meio-dia (claro) × 18h (escuro, de propósito). "
                   "Confiança = média da confiança que o próprio YOLO deu aos objetos que contou (0 a 1).")
        linhas = []
        for _, r in t.iterrows():
            linha = {"Classe": ROTULO.get(r["classe"], r["classe"]), "Horário": f"{r['periodo']} ({r['iluminacao']})",
                     "Gabarito": int(r["gabarito"])}
            for m in metodos:
                linha[f"Erro {NOMES[m].split(' (')[0]}"] = fmt_erro(r[f"erro_{m}"], r[f"erro_pct_{m}"])
            for m in cfg["modelos"]:
                if f"conf_media_{m}" in t.columns:
                    linha[f"Confiança {NOMES[m].split(' (')[0]}"] = f"{r[f'conf_media_{m}']:.2f}".replace(".", ",")
            linhas.append(linha)
        st.dataframe(pd.DataFrame(linhas), hide_index=True, width="stretch")
        png = PASTA_GRAF / "G05_dia_x_noite.png"
        if png.is_file():
            st.image(str(png), width="stretch")
        st.caption("Um vídeo por horário e 19 a 37 objetos por classe: as diferenças são um **indício**, não prova. "
                   "Luz e movimento da rua mudam juntos.")

# --- Vídeos de demonstração --------------------------------------------
with aba_videos:
    clipes = sorted(PASTA_DEMO.glob("*.mp4")) if PASTA_DEMO.is_dir() else []
    ids = list(dict.fromkeys(c.stem.rsplit("_", 1)[0] for c in clipes))
    if not ids:
        st.info("Ainda não há clipes. Rode `python scripts/06_videos_demo.py`.")
    else:
        st.caption("YOLO contando: **nano à esquerda, large à direita**. Linha amarela = linha de contagem; caixa grossa = "
                   "objeto já contado; o contador é **acumulado desde 00:00** (contagem oficial) e, no clipe final, termina no total da tabela. Os clipes ficam fora do repositório "
                   "(rostos e placas).")
        vid = st.selectbox("Vídeo", ids)
        # Um embaixo do outro, em largura total: lado a lado o contador fica pequeno demais para ler.
        for trecho, rotulo in [("inicio", "Primeiros 30 s da contagem (contador começa em 0)"),
                               ("fim", "Últimos 30 s da contagem (contador já vem acumulado e termina no total da tabela)")]:
            arq = PASTA_DEMO / f"{vid}_{trecho}.mp4"
            if arq.is_file():
                st.markdown(f"**{rotulo}**")
                st.video(arq.read_bytes(), format="video/mp4")

# --- Velocidade --------------------------------------------------------
with aba_vel:
    v = ler("T07_desempenho_modelos.csv")
    if v is None:
        st.info("Ainda não há a tabela de desempenho. Rode `python scripts/04_comparar.py`.")
    else:
        media = v[v["video"] == "média"]
        cols = st.columns(max(1, len(media)))
        for c, (_, r) in zip(cols, media.iterrows()):
            c.metric(NOMES.get(r["modelo"], r["modelo"]), f"{r['quadros_por_segundo']:.1f} quadros/s".replace(".", ","))
            c.caption(f"{r['ms_por_quadro_deteccao_rastreamento_mediana']:.1f} ms por quadro (detecção + rastreamento)"
                      .replace(".", ","))
        st.caption("Média dos 4 vídeos (1280×720), GPU RTX 4050 Laptop, imagem de entrada 640 px, FP16. "
                   "30 quadros/s = tempo real.")
        tabela = v[v["video"] != "média"][["video", "periodo", "modelo", "quadros_por_segundo",
                                           "ms_por_quadro_deteccao_rastreamento_mediana", "tempo_total_s",
                                           "memoria_gpu_pico_mb"]]
        tabela.columns = ["Vídeo", "Horário", "Modelo", "Quadros/s", "ms por quadro", "Tempo total (s)", "Memória GPU (MB)"]
        st.dataframe(tabela, hide_index=True, width="stretch")

# --- Gráficos ----------------------------------------------------------
with aba_graf:
    pngs = sorted(PASTA_GRAF.glob("*.png")) if PASTA_GRAF.is_dir() else []
    if not pngs:
        st.info("Ainda não há gráficos. Rode `python scripts/05_graficos.py`.")
    else:
        st.caption(f"Arquivos em `{PASTA_GRAF}` (300 dpi, prontos para o trabalho).")
        for p in pngs:
            st.image(str(p), caption=p.name, width="stretch")
