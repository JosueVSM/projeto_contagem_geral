"""Testes das métricas com números ARTIFICIAIS (conferíveis à mão)."""

import numpy as np
import pandas as pd
import pytest

import dados
from configuracao import ORDEM_CLASSES, classe_analise, interpretar_minutos, numero
from metricas import (
    avaliar_eventos,
    casar_eventos,
    contagem_por_minuto,
    erro_contagem,
    matriz_confusao,
    tendencia,
)


def ev(lista):
    return pd.DataFrame(lista, columns=["t_video_s", "classe"])


def test_interpretar_minutos_e_numero():
    assert interpretar_minutos("1-3,8-10") == [1, 2, 3, 8, 9, 10]
    assert interpretar_minutos("2") == [2]
    assert numero("12,5") == 12.5
    assert numero("", 7) == 7


def test_contagem_por_minuto_respeita_inicio_e_janela():
    e = ev([(5, "carro"), (10, "carro"), (69.9, "carro"), (70, "moto"), (130, "pessoa")])
    t = contagem_por_minuto(e, inicio_s=10, duracao_s=120)
    assert list(t.index) == [1, 2]
    assert t.loc[1, "carro"] == 2      # 10 s e 69,9 s
    assert t.loc[2, "moto"] == 1       # 70 s
    assert t.values.sum() == 3         # 5 s (antes do início) e 130 s (após o fim) ficam fora


def test_casar_eventos_um_para_um_e_tolerancia():
    pares = casar_eventos([10.0, 20.0], [10.4, 10.6, 25.0], tolerancia_s=1.5)
    assert len(pares) == 1             # só um dos dois perto de 10 s pode casar; 25 s está longe de 20 s
    assert pares[0][0] == 0


def test_precisao_revocacao():
    ref = ev([(10, "carro"), (20, "carro"), (30, "moto")])
    pred = ev([(10.5, "carro"), (40, "carro"), (30.2, "moto")])
    r = avaliar_eventos(ref, pred, 1.5).set_index("classe")
    assert (r.loc["carro", "vp"], r.loc["carro", "fp"], r.loc["carro", "fn"]) == (1, 1, 1)
    assert r.loc["carro", "precisao"] == 0.5 and r.loc["carro", "revocacao"] == 0.5
    assert r.loc["moto", "f1"] == 1.0
    assert r.loc["todas", "vp"] == 2


def test_matriz_confusao_mostra_troca_de_classe():
    ref = ev([(10, "carro"), (20, "moto")])
    pred = ev([(10.3, "caminhao"), (50, "pessoa")])
    m = matriz_confusao(ref, pred, 1.5)
    assert m.loc["carro", classe_analise("caminhao")] == 1   # caminhão entra na classe agrupada, se houver
    assert m.loc["moto", "nao_detectado"] == 1
    assert m.loc["nao_existe", "pessoa"] == 1


def test_matriz_confusao_prioriza_mesma_classe():
    # moto e carro cruzam quase juntos: não pode virar "carro -> moto" + "moto -> carro"
    ref = ev([(10.0, "carro"), (10.4, "moto")])
    pred = ev([(10.35, "carro"), (10.05, "moto")])
    m = matriz_confusao(ref, pred, 1.5)
    assert m.loc["carro", "carro"] == 1 and m.loc["moto", "moto"] == 1
    assert m.values.sum() == 2


def test_erro_contagem():
    ref = pd.DataFrame({"carro": [10, 10], "moto": [2, 0]}, index=[1, 2]).reindex(columns=ORDEM_CLASSES, fill_value=0)
    met = ref.copy()
    met.loc[1, "carro"] = 8   # -2
    met.loc[2, "carro"] = 11  # +1
    r = erro_contagem(ref, met).set_index("classe")
    assert r.loc["carro", "vies"] == -1
    assert r.loc["carro", "eam_por_minuto"] == 1.5
    assert r.loc["carro", "wape_pct"] == 15.0
    assert np.isnan(r.loc["cachorro", "wape_pct"])   # sem referência -> não dá para calcular %
    assert r.loc["total", "referencia"] == 22


def test_tendencia_crescente():
    t = tendencia([1, 2, 3, 4, 5, 6], [0, 1, 1, 2, 3, 3])
    assert t["inclinacao_por_min"] > 0 and t["spearman_rho"] > 0.9


def test_leitura_manual_valida(tmp_path, monkeypatch):
    monkeypatch.setattr(dados, "PASTA_MANUAL", tmp_path)
    (tmp_path / "x.csv").write_text(
        "minuto;carro;moto;bicicleta;pessoa;cachorro;onibus;caminhao;observacoes\n"
        "1;10;3;0;2;0;1;0;\n2;8;4;1;0;0;0;1;chuva fina\n",
        encoding="utf-8",
    )
    m = dados.ler_manual("x", n_minutos=2)
    assert m.por_minuto
    t = m.tabela_por_minuto()
    assert t.loc[2, "moto"] == 4 and t.values.sum() == 30


def test_leitura_manual_so_total(tmp_path, monkeypatch):
    monkeypatch.setattr(dados, "PASTA_MANUAL", tmp_path)
    (tmp_path / "t.csv").write_text(
        "minuto;carro;moto;bicicleta;pessoa;cachorro;onibus;caminhao\nTotal;40;9;2;1;0;0;0\n", encoding="utf-8")
    m = dados.ler_manual("t", n_minutos=4)
    assert not m.por_minuto
    assert m.blocos == {"total": [1, 2, 3, 4]}
    assert m.tabela.loc["total", "carro"] == 40


def test_leitura_manual_blocos_e_sobreposicao(tmp_path, monkeypatch):
    monkeypatch.setattr(dados, "PASTA_MANUAL", tmp_path)
    cab = "minuto;carro;moto;bicicleta;pessoa;cachorro;onibus;caminhao\n"
    (tmp_path / "b.csv").write_text(cab + "8-10;5;1;0;0;0;0;0\n1-3;6;2;0;0;0;0;0\n4-7;9;3;0;0;0;0;0\n", encoding="utf-8")
    m = dados.ler_manual("b", n_minutos=10)
    assert list(m.blocos) == ["1-3", "4-7", "8-10"]   # ordenado pelo 1º minuto
    (tmp_path / "s.csv").write_text(cab + "1-3;6;2;0;0;0;0;0\n3-5;9;3;0;0;0;0;0\n", encoding="utf-8")
    with pytest.raises(ValueError, match="sobrepostos"):
        dados.ler_manual("s", n_minutos=10)


def test_agregar_blocos_e_erro_por_bloco():
    from metricas import agregar_blocos

    por_min = pd.DataFrame(0, index=pd.RangeIndex(1, 5, name="minuto"), columns=ORDEM_CLASSES)
    por_min["carro"] = [10, 12, 8, 10]
    blocos = {"1-2": [1, 2], "3-4": [3, 4]}
    yolo = agregar_blocos(por_min, blocos)
    assert yolo.loc["1-2", "carro"] == 22 and yolo.loc["3-4", "carro"] == 18
    manual = yolo.copy()
    manual.loc["1-2", "carro"] = 20     # humano contou 2 a menos no 1º bloco
    r = erro_contagem(manual, yolo, list(blocos), n_minutos=4).set_index("classe")
    assert r.loc["carro", "vies"] == 2
    assert r.loc["carro", "eam_por_minuto"] == 0.5   # 2 de erro em 4 minutos
    assert r.loc["carro", "n_blocos"] == 2


def test_leitura_manual_com_virgula_e_celula_vazia(tmp_path, monkeypatch):
    monkeypatch.setattr(dados, "PASTA_MANUAL", tmp_path)
    (tmp_path / "y.csv").write_text(
        "minuto,carro,moto,bicicleta,pessoa,cachorro,onibus,caminhao\n1,10,,0,2,0,1,0\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="moto"):
        dados.ler_manual("y")


def test_classes_separadas_somadas_na_classe_agrupada(tmp_path, monkeypatch):
    """Planilha com 'onibus' e 'caminhao' separados vira 'caminhao_onibus' se a análise agrupar."""
    import configuracao

    if "caminhao_onibus" not in configuracao.GRUPOS_CLASSES:
        pytest.skip("config.yaml não agrupa caminhão e ônibus")
    monkeypatch.setattr(dados, "PASTA_MANUAL", tmp_path)
    (tmp_path / "g.csv").write_text(
        "minuto;carro;moto;bicicleta;pessoa;cachorro;onibus;caminhao\ntotal;5;1;0;0;0;2;3\n", encoding="utf-8")
    m = dados.ler_manual("g", n_minutos=10)
    assert m.tabela.loc["total", "caminhao_onibus"] == 5


def test_gabarito_so_com_total(tmp_path, monkeypatch):
    monkeypatch.setattr(dados, "PASTA_GABARITO", tmp_path)
    cab = "minuto;" + ";".join(ORDEM_CLASSES) + "\n"
    (tmp_path / "t.csv").write_text(cab + "total;" + ";".join(["3"] * len(ORDEM_CLASSES)) + "\n", encoding="utf-8")
    assert dados.formato_gabarito("t") == "contagem"
    assert dados.ler_gabarito("t") is None              # não é gabarito por evento
    g = dados.ler_gabarito_contagem("t", n_minutos=10)
    assert g.blocos == {"total": list(range(1, 11))} and int(g.tabela.values.sum()) == 3 * len(ORDEM_CLASSES)


def test_csv_com_separador_dentro_do_texto_da_erro_claro(tmp_path):
    from configuracao import ler_csv_flexivel

    (tmp_path / "v.csv").write_text("id;obs\nv1;texto ok\nv2;texto; com ponto e vírgula\n", encoding="utf-8")
    with pytest.raises(ValueError, match="colunas a mais"):
        ler_csv_flexivel(tmp_path / "v.csv")
