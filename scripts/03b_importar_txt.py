"""Passo 3b: importar contagens TOTAIS escritas em .txt (ex.: Video01.txt).

Formato aceito (uma classe por linha, "Nome = número"; acentos e maiúsculas tanto faz):
    Video01
    Horário: 12:10 as 12:20
    Carros = 74
    Motos = 25
    Pessoas = 20
    Bicicletas = 3
    Caminhões ou Ônibus = 3
    Cachorros = 0

Para cada vídeo de config/videos.csv com a coluna `contagem_txt` preenchida (ex.: Video01):
  dados/manual/Video01.txt           -> dados/manual/<id>.csv    (contagem ao vivo)
  dados/manual/Video01_Gabarito.txt  -> dados/gabarito/<id>.csv  (gabarito, só total)
Os .txt originais NÃO são alterados.

Uso:
  python scripts/03b_importar_txt.py            # não sobrescreve CSVs que já existem
  python scripts/03b_importar_txt.py --refazer
"""

import _caminhos  # noqa: F401
import argparse
import re
import unicodedata

from configuracao import ORDEM_CLASSES, carregar_config, ler_videos
from dados import PASTA_GABARITO, PASTA_MANUAL

# nome escrito no .txt (sem acento, minúsculo) -> classe da análise
NOMES = {
    "carro": "carro", "carros": "carro",
    "moto": "moto", "motos": "moto",
    "pessoa": "pessoa", "pessoas": "pessoa", "pedestre": "pessoa", "pedestres": "pessoa",
    "bicicleta": "bicicleta", "bicicletas": "bicicleta",
    "cachorro": "cachorro", "cachorros": "cachorro",
    "onibus": "onibus", "caminhao": "caminhao", "caminhoes": "caminhao",
    "caminhoes ou onibus": "caminhao_onibus", "caminhao ou onibus": "caminhao_onibus",
    "onibus ou caminhoes": "caminhao_onibus", "caminhoes e onibus": "caminhao_onibus",
}


def sem_acento(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn").lower().strip()


def ler_txt(caminho):
    """-> (contagens {classe: n}, texto do horário ou '')."""
    contagens, horario = {}, ""
    for linha in caminho.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        if ":" in linha and sem_acento(linha).startswith("horario"):
            horario = linha.split(":", 1)[1].strip()
            continue
        m = re.match(r"\s*(.+?)\s*=\s*(\d+)\s*$", linha)
        if not m:
            continue
        nome = sem_acento(m.group(1))
        if nome not in NOMES:
            raise ValueError(f"{caminho.name}: não reconheço a classe '{m.group(1)}'")
        classe = NOMES[nome]
        if classe in contagens:
            raise ValueError(f"{caminho.name}: classe '{classe}' aparece duas vezes")
        contagens[classe] = int(m.group(2))
    # Se a análise agrupa caminhão+ônibus e o .txt trouxe separado, soma.
    if "caminhao_onibus" in ORDEM_CLASSES and "caminhao_onibus" not in contagens:
        if "caminhao" in contagens or "onibus" in contagens:
            contagens["caminhao_onibus"] = contagens.pop("caminhao", 0) + contagens.pop("onibus", 0)
    faltando = [c for c in ORDEM_CLASSES if c not in contagens]
    if faltando:
        raise ValueError(f"{caminho.name}: faltam as classes {faltando}")
    return contagens, horario


def escrever_csv(destino, contagens, origem, horario):
    destino.parent.mkdir(parents=True, exist_ok=True)
    obs = f"importado de {origem}" + (f" (horario {horario})" if horario else "")
    linhas = ["minuto;" + ";".join(ORDEM_CLASSES) + ";observacoes",
              "total;" + ";".join(str(contagens[c]) for c in ORDEM_CLASSES) + ";" + obs.replace(";", ",")]
    destino.write_text("\n".join(linhas) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--refazer", action="store_true", help="sobrescreve CSVs já existentes")
    args = ap.parse_args()

    videos = ler_videos(carregar_config())
    if "contagem_txt" not in videos.columns:
        raise SystemExit("config/videos.csv não tem a coluna 'contagem_txt' (ex.: Video01).")
    for _, v in videos[videos["contagem_txt"] != ""].iterrows():
        for sufixo, pasta, rotulo in [("", PASTA_MANUAL, "ao vivo"), ("_Gabarito", PASTA_GABARITO, "gabarito")]:
            origem = PASTA_MANUAL / f"{v['contagem_txt']}{sufixo}.txt"
            destino = pasta / f"{v['id']}.csv"
            if not origem.is_file():
                print(f"[falta] {origem.name} ({rotulo} de {v['id']})")
                continue
            if destino.is_file() and not args.refazer:
                print(f"[já existe] {destino.relative_to(pasta.parents[1])} (use --refazer)")
                continue
            contagens, horario = ler_txt(origem)
            escrever_csv(destino, contagens, origem.name, horario)
            print(f"{origem.name:<22} -> {destino.relative_to(pasta.parents[1])}  {contagens}  horário: {horario}")


if __name__ == "__main__":
    main()
