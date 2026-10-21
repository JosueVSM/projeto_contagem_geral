"""Leitura da configuração do projeto: config.yaml, videos.csv e linhas.json."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yaml

RAIZ = Path(__file__).resolve().parents[1]
PASTA_CONFIG = RAIZ / "config"
ARQ_CONFIG = PASTA_CONFIG / "config.yaml"
ARQ_VIDEOS = PASTA_CONFIG / "videos.csv"
ARQ_LINHAS = PASTA_CONFIG / "linhas.json"

# Classes que o detector conhece (nomes em português das classes COCO usadas).
CLASSES_DETECTOR = ["carro", "moto", "bicicleta", "pessoa", "cachorro", "onibus", "caminhao"]


def _classes_de_analise() -> tuple[list[str], dict[str, str], dict[str, list[str]]]:
    """Lê analise.agrupar_classes do config.yaml.

    Devolve (ordem das classes na análise, mapa classe_detector -> classe_análise,
    grupos {classe_agrupada: [membros]}). Ex.: caminhão e ônibus -> caminhao_onibus.
    """
    try:
        with open(ARQ_CONFIG, encoding="utf-8") as f:
            grupos = (yaml.safe_load(f).get("analise") or {}).get("agrupar_classes") or {}
    except FileNotFoundError:
        grupos = {}
    mapa = {m: g for g, membros in grupos.items() for m in membros}
    ordem = []
    for c in CLASSES_DETECTOR:
        alvo = mapa.get(c, c)
        if alvo not in ordem:
            ordem.append(alvo)
    return ordem, mapa, {g: list(m) for g, m in grupos.items()}


# Ordem fixa das classes em tabelas e gráficos (já com os agrupamentos).
ORDEM_CLASSES, MAPA_ANALISE, GRUPOS_CLASSES = _classes_de_analise()


def classe_analise(classe: str) -> str:
    """Classe do detector -> classe usada na comparação (ex.: 'onibus' -> 'caminhao_onibus')."""
    return MAPA_ANALISE.get(classe, classe)


def carregar_config(caminho: str | Path | None = None) -> dict:
    """Lê o config.yaml e devolve um dicionário."""
    caminho = Path(caminho) if caminho else ARQ_CONFIG
    with open(caminho, encoding="utf-8") as f:
        return yaml.safe_load(f)


def resolver_pasta(caminho_txt: str) -> Path:
    """Converte um caminho do config em Path absoluto.

    "~" vira a pasta do usuário; caminhos relativos partem da raiz do projeto.
    """
    p = Path(caminho_txt).expanduser()
    return p if p.is_absolute() else RAIZ / p


def ler_csv_flexivel(caminho: str | Path) -> pd.DataFrame:
    """Lê CSV separado por ';' (Excel em português) ou ','.

    Também tolera arquivos salvos pelo Excel em ANSI (latin-1) em vez de UTF-8.
    Tudo é lido como texto; a conversão de tipos fica a cargo de quem chama.
    """
    caminho = Path(caminho)
    for codificacao in ("utf-8-sig", "latin-1"):
        try:
            with open(caminho, encoding=codificacao) as f:
                cabecalho = f.readline()
            sep = ";" if ";" in cabecalho else ","
            try:
                df = pd.read_csv(caminho, sep=sep, encoding=codificacao, dtype=str, keep_default_na=False)
            except pd.errors.ParserError as erro:
                raise ValueError(
                    f"{caminho.name}: alguma linha tem colunas a mais. Provavelmente há '{sep}' dentro de um "
                    f"texto (ex.: na coluna observacoes). Troque por vírgula ou hífen. Detalhe: {erro}"
                ) from None
            df.columns = [c.strip().lower() for c in df.columns]
            return df.apply(lambda col: col.str.strip())
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Não consegui ler {caminho} (codificação desconhecida).")


def numero(texto: str, padrao: float | None = None) -> float | None:
    """Converte texto em número aceitando vírgula decimal ("12,5")."""
    texto = (texto or "").strip().replace(",", ".")
    if texto == "":
        return padrao
    return float(texto)


def interpretar_minutos(texto: str) -> list[int]:
    """'1-3,8-10' -> [1, 2, 3, 8, 9, 10]."""
    minutos: set[int] = set()
    for parte in (texto or "").replace(" ", "").split(","):
        if not parte:
            continue
        if "-" in parte:
            ini, fim = parte.split("-")
            minutos.update(range(int(ini), int(fim) + 1))
        else:
            minutos.add(int(parte))
    return sorted(minutos)


def ler_videos(cfg: dict | None = None, caminho: str | Path | None = None) -> pd.DataFrame:
    """Lê config/videos.csv e converte os tipos.

    Colunas extras criadas:
      - caminho: Path completo do arquivo de vídeo
      - existe: se o arquivo já está na pasta de vídeos
      - usar: bool (coluna usar_na_analise = sim/nao)
    """
    cfg = cfg or carregar_config()
    df = ler_csv_flexivel(caminho or ARQ_VIDEOS)
    pasta = resolver_pasta(cfg["pastas"]["videos"])
    padrao_gab = cfg["comparacao"]["minutos_gabarito_padrao"]

    df["usar"] = df["usar_na_analise"].str.lower().isin(["sim", "s", "yes", "1", "true"])
    df["inicio_contagem_s"] = df["inicio_contagem_s"].map(lambda t: numero(t, None))
    df["duracao_s"] = df["duracao_s"].map(lambda t: numero(t, 600.0))
    df["minutos_gabarito"] = df["minutos_gabarito"].map(lambda t: t if t else padrao_gab)
    df["caminho"] = df["arquivo"].map(lambda a: pasta / a)
    df["existe"] = df["caminho"].map(lambda p: p.is_file())
    return df


def video_por_id(id_video: str, cfg: dict | None = None) -> pd.Series:
    df = ler_videos(cfg)
    linha = df[df["id"] == id_video]
    if linha.empty:
        raise KeyError(f"Vídeo '{id_video}' não está em config/videos.csv. Ids: {list(df['id'])}")
    return linha.iloc[0]


def inicio_contagem(video: pd.Series) -> float:
    """Segundo do vídeo em que a contagem começa (0 se ainda não informado)."""
    ini = video["inicio_contagem_s"]
    if ini is None or pd.isna(ini):
        print(f"[aviso] {video['id']}: inicio_contagem_s vazio em videos.csv -> usando 0 s.")
        return 0.0
    return float(ini)


def ler_linhas() -> dict:
    if ARQ_LINHAS.is_file():
        with open(ARQ_LINHAS, encoding="utf-8") as f:
            return json.load(f)
    return {}


def linha_do_video(id_video: str) -> tuple[tuple[float, float], tuple[float, float]]:
    """Devolve os dois pontos (p1, p2) da linha de contagem do vídeo."""
    linhas = ler_linhas()
    if id_video not in linhas:
        raise KeyError(
            f"Linha de contagem do vídeo '{id_video}' não definida. "
            f"Rode: python scripts/01_definir_linha.py --video {id_video}"
        )
    d = linhas[id_video]
    return tuple(d["p1"]), tuple(d["p2"])


def salvar_linha(id_video: str, p1, p2, largura: int, altura: int) -> None:
    linhas = ler_linhas()
    linhas[id_video] = {"p1": list(p1), "p2": list(p2), "largura": largura, "altura": altura}
    with open(ARQ_LINHAS, "w", encoding="utf-8") as f:
        json.dump(linhas, f, indent=2, ensure_ascii=False)


def mapa_coco_para_pt(cfg: dict) -> dict[int, str]:
    """{2: 'carro', 3: 'moto', ...}"""
    return {int(i): nome for nome, i in cfg["classes"].items()}
