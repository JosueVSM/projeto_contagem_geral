"""Leitura e validação da contagem manual (papel) e do gabarito.

Formatos esperados (separador ';' ou ','):

dados/manual/<id_video>.csv  -> a coluna "minuto" aceita TRÊS formatos:
    por minuto      por blocos        só o total
    minuto;carro..  minuto;carro..    minuto;carro..
    1;23;...        1-3;61;...        total;198;...
    2;19;...        4-7;80;...
    ...             8-10;57;...
  ("total" = todos os minutos da janela de contagem; blocos não podem se sobrepor)

dados/gabarito/<id_video>.csv -> DOIS formatos possíveis:
  a) um cruzamento por linha (gerado pela ferramenta 03) -> permite precisão/revocação:
       t_video_s;classe
       12.433;carro
  b) contagem, no mesmo formato da contagem manual (ex.: só o total):
       minuto;carro;moto;...
       total;76;25;...
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from configuracao import CLASSES_DETECTOR, GRUPOS_CLASSES, ORDEM_CLASSES, RAIZ, classe_analise, ler_csv_flexivel, numero

PASTA_MANUAL = RAIZ / "dados" / "manual"
PASTA_GABARITO = RAIZ / "dados" / "gabarito"


def caminho_manual(id_video: str) -> Path:
    return PASTA_MANUAL / f"{id_video}.csv"


def caminho_gabarito(id_video: str) -> Path:
    return PASTA_GABARITO / f"{id_video}.csv"


@dataclass
class ContagemManual:
    """Contagem manual em blocos de minutos.

    tabela: linhas = rótulo do bloco ("3", "1-3" ou "total"), colunas = classes.
    blocos: rótulo -> lista de minutos que o bloco cobre.
    """

    tabela: pd.DataFrame
    blocos: dict[str, list[int]]

    @property
    def por_minuto(self) -> bool:
        return all(len(m) == 1 for m in self.blocos.values())

    @property
    def minutos(self) -> list[int]:
        return sorted(m for ms in self.blocos.values() for m in ms)

    def tabela_por_minuto(self) -> pd.DataFrame:
        """Só existe se a contagem foi feita minuto a minuto."""
        t = self.tabela.copy()
        t.index = [self.blocos[r][0] for r in t.index]
        t.index.name = "minuto"
        return t.sort_index()


def _minutos_do_rotulo(rotulo: str, n_minutos: int | None, arquivo: str) -> list[int]:
    r = rotulo.strip().lower()
    if r == "total":
        if n_minutos is None:
            raise ValueError(f"{arquivo}: 'total' precisa saber a duração da contagem")
        return list(range(1, n_minutos + 1))
    if "-" in r:
        a, b = (int(x) for x in r.split("-"))
        if b < a:
            raise ValueError(f"{arquivo}: bloco '{rotulo}' invertido")
        return list(range(a, b + 1))
    return [int(r)]


def _ler_contagem(caminho: Path, n_minutos: int | None) -> ContagemManual | None:
    """Lê um CSV de contagem (por minuto, por blocos ou total) -> ContagemManual.

    Se o arquivo tiver as classes separadas (ex.: 'onibus' e 'caminhao') e a
    análise usar a classe agrupada ('caminhao_onibus'), as colunas são somadas.
    Gera erro claro se faltar coluna, bloco repetido/sobreposto ou célula vazia,
    para nenhum dado digitado errado passar despercebido.
    """
    df = ler_csv_flexivel(caminho)
    for grupo, membros in GRUPOS_CLASSES.items():
        if grupo not in df.columns and all(m in df.columns for m in membros):
            vazio = (df[membros] == "").all(axis=1)
            soma = sum(df[m].map(lambda t: numero(t, 0.0)) for m in membros)
            df[grupo] = [("" if v else str(int(x))) for v, x in zip(vazio, soma)]
    faltando = [c for c in ["minuto", *ORDEM_CLASSES] if c not in df.columns]
    if faltando:
        raise ValueError(f"{caminho.name}: faltam as colunas {faltando}")
    df = df[df["minuto"] != ""].copy()
    if (df[ORDEM_CLASSES] == "").all().all():
        print(f"[aviso] {caminho.name}: planilha ainda não preenchida (todas as células vazias) -> ignorada")
        return None
    df["minuto"] = df["minuto"].str.lower()
    blocos = {r: _minutos_do_rotulo(r, n_minutos, caminho.name) for r in df["minuto"]}
    todos = [m for ms in blocos.values() for m in ms]
    if df["minuto"].duplicated().any() or len(todos) != len(set(todos)):
        raise ValueError(f"{caminho.name}: minutos repetidos ou blocos sobrepostos ({list(df['minuto'])})")
    for c in ORDEM_CLASSES:
        vazios = df.loc[df[c] == "", "minuto"].tolist()
        if vazios:
            raise ValueError(f"{caminho.name}: coluna '{c}' vazia em {vazios} (use 0 se não passou nenhum)")
        df[c] = df[c].map(lambda t: int(numero(t)))
    if n_minutos is not None and set(todos) != set(range(1, n_minutos + 1)):
        print(f"[aviso] {caminho.name}: cobre os minutos {sorted(todos)} (janela tem 1..{n_minutos})")
    ordem = sorted(blocos, key=lambda r: blocos[r][0])
    tabela = df.set_index("minuto")[ORDEM_CLASSES].loc[ordem]
    tabela.index.name = "bloco"
    return ContagemManual(tabela, {r: blocos[r] for r in ordem})


def ler_manual(id_video: str, n_minutos: int | None = None) -> ContagemManual | None:
    """Contagem manual (ao vivo) do vídeo. None se não existir ou estiver vazia."""
    caminho = caminho_manual(id_video)
    return _ler_contagem(caminho, n_minutos) if caminho.is_file() else None


def formato_gabarito(id_video: str) -> str | None:
    """'eventos' (t_video_s;classe, da ferramenta 03), 'contagem' (minuto;classes...) ou None."""
    caminho = caminho_gabarito(id_video)
    if not caminho.is_file():
        return None
    colunas = set(ler_csv_flexivel(caminho).columns)
    if "t_video_s" in colunas:
        return "eventos"
    if "minuto" in colunas:
        return "contagem"
    raise ValueError(f"{caminho.name}: formato de gabarito desconhecido (colunas {sorted(colunas)})")


def ler_gabarito(id_video: str) -> pd.DataFrame | None:
    """Gabarito por EVENTO (t_video_s, classe). None se não existir ou se for só contagem."""
    if formato_gabarito(id_video) != "eventos":
        return None
    caminho = caminho_gabarito(id_video)
    df = ler_csv_flexivel(caminho)
    if df.empty:
        return pd.DataFrame(columns=["t_video_s", "classe"])
    df["t_video_s"] = df["t_video_s"].map(numero).astype(float)
    invalidas = set(df["classe"]) - set(ORDEM_CLASSES) - set(CLASSES_DETECTOR)
    if invalidas:
        raise ValueError(f"{caminho.name}: classes desconhecidas {invalidas}")
    df["classe"] = df["classe"].map(classe_analise)
    return df[["t_video_s", "classe"]].sort_values("t_video_s").reset_index(drop=True)


def ler_gabarito_contagem(id_video: str, n_minutos: int | None = None) -> ContagemManual | None:
    """Gabarito só com contagens (ex.: total por classe). None se não existir ou for por evento."""
    if formato_gabarito(id_video) != "contagem":
        return None
    return _ler_contagem(caminho_gabarito(id_video), n_minutos)


def salvar_gabarito(id_video: str, eventos: list[dict]) -> Path:
    caminho = caminho_gabarito(id_video)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(eventos, columns=["t_video_s", "classe"]).sort_values("t_video_s")
    df["t_video_s"] = df["t_video_s"].round(3)
    df.to_csv(caminho, sep=";", index=False, encoding="utf-8")
    return caminho
