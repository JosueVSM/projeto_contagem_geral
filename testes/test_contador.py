"""Testes da regra de contagem com trajetórias ARTIFICIAIS.

Nada aqui é resultado do experimento: são situações inventadas de propósito
para conferir se o código faz exatamente o que a regra diz.

Cenário: linha vertical em x = 100, de y = 0 até y = 200 (como uma linha
atravessando uma rua horizontal na imagem).
"""

import pytest

from contador import ContadorLinha, Deteccao
from geometria import fracao_dentro, lado_da_linha, posicao_no_segmento

CFG = {"min_quadros_trilha": 3, "sobreposicao_montado": 0.3, "frac_montado_min": 0.5, "margem_segmento": 0.05,
       "min_deslocamento_px": 60}
LINHA = ((100, 0), (100, 200))


def caixa_em(x_centro, y_base, larg=20, alt=20):
    return (x_centro - larg / 2, y_base - alt, x_centro + larg / 2, y_base)


def rodar(trajetorias, cfg=CFG):
    """trajetorias: lista de quadros; cada quadro = lista de (id, classe, conf, x, y_base[, larg, alt])."""
    c = ContadorLinha(*LINHA, cfg)
    for q, dets in enumerate(trajetorias):
        c.atualizar(q, q / 30.0, [Deteccao(i, cl, cf, caixa_em(x, y, *extra)) for i, cl, cf, x, y, *extra in dets])
    return c


# ----------------------------------------------------------------------
def test_geometria_basica():
    a, b = (100, 0), (100, 200)
    assert lado_da_linha((50, 100), a, b) * lado_da_linha((150, 100), a, b) < 0
    assert lado_da_linha((100, 50), a, b) == 0
    assert posicao_no_segmento((80, 100), a, b) == pytest.approx(0.5)
    assert fracao_dentro((0, 0, 10, 10), (5, 0, 20, 10)) == pytest.approx(0.5)


def test_objeto_que_cruza_conta_uma_vez():
    quadros = [[(1, "carro", 0.9, x, 100)] for x in range(40, 170, 10)]
    c = rodar(quadros)
    ev = c.eventos()
    assert len(ev) == 1
    assert ev[0]["classe"] == "carro"
    assert ev[0]["sentido"] == "para_direita"
    # cruzou entre x=90 (quadro 5) e x=110 (quadro 7); x=100 cai em cima (quadro 6, lado 0)
    assert ev[0]["t_video_s"] == pytest.approx(7 / 30.0)


def test_sentido_contrario():
    quadros = [[(1, "moto", 0.9, x, 100)] for x in range(170, 40, -10)]
    ev = rodar(quadros).eventos()
    assert len(ev) == 1 and ev[0]["sentido"] == "para_esquerda"


def test_objeto_que_nao_cruza_nao_conta():
    quadros = [[(1, "carro", 0.9, x, 100)] for x in range(10, 90, 5)]  # para antes da linha
    assert rodar(quadros).eventos() == []


def test_objeto_parado_nao_conta():
    quadros = [[(1, "carro", 0.9, 150, 100)] for _ in range(100)]  # carro estacionado
    assert rodar(quadros).eventos() == []


def test_vai_e_volta_conta_so_uma_vez():
    xs = [60, 80, 120, 140, 120, 80, 60, 80, 120, 140]
    quadros = [[(1, "pessoa", 0.8, x, 100)] for x in xs]
    assert len(rodar(quadros).eventos()) == 1


def test_cruzar_fora_do_segmento_nao_conta():
    # passa em y = 400, bem abaixo da ponta da linha (y = 200)
    quadros = [[(1, "carro", 0.9, x, 400)] for x in range(40, 170, 10)]
    assert rodar(quadros).eventos() == []


def test_classe_por_voto_da_maioria():
    xs = list(range(40, 170, 10))
    quadros = [[(1, "caminhao" if i == 6 else "carro", 0.5 if i == 6 else 0.9, x, 100)] for i, x in enumerate(xs)]
    ev = rodar(quadros).eventos()
    assert len(ev) == 1 and ev[0]["classe"] == "carro"


def test_trilha_curta_descartada():
    quadros = [[(1, "carro", 0.9, 90, 100)], [(1, "carro", 0.9, 110, 100)]]  # só 2 quadros
    c = rodar(quadros)
    assert c.eventos() == []
    assert c.resumo_trilhas()[0]["motivo_descarte"] == "trilha_curta"


def test_pessoa_na_moto_nao_conta_como_pessoa():
    quadros = []
    for x in range(40, 170, 10):
        quadros.append([
            (1, "moto", 0.9, x, 100, 40, 30),        # moto
            (2, "pessoa", 0.8, x, 90, 20, 40),       # condutor: base dentro da moto
        ])
    c = rodar(quadros)
    classes = [e["classe"] for e in c.eventos()]
    assert classes == ["moto"]
    motivos = {r["id_trilha"]: r["motivo_descarte"] for r in c.resumo_trilhas()}
    assert motivos[2] == "pessoa_montada"


def test_pedestre_ao_lado_da_moto_conta():
    quadros = []
    for x in range(40, 170, 10):
        quadros.append([
            (1, "moto", 0.9, x, 100, 40, 30),
            (2, "pessoa", 0.8, x, 180, 20, 40),      # na calçada, longe da moto
        ])
    classes = sorted(e["classe"] for e in rodar(quadros).eventos())
    assert classes == ["moto", "pessoa"]


def test_varios_objetos_ids_diferentes():
    quadros = [[(1, "carro", 0.9, x, 50), (2, "onibus", 0.9, 200 - x, 150)] for x in range(40, 170, 10)]
    ev = rodar(quadros).eventos()
    assert sorted(e["classe"] for e in ev) == ["carro", "onibus"]


def test_troca_de_id_depois_da_linha_nao_conta_de_novo():
    # id 1 cruza; o rastreador "perde" e cria id 2 já do outro lado
    quadros = [[(1, "carro", 0.9, x, 100)] for x in range(40, 140, 10)]
    quadros += [[(2, "carro", 0.9, x, 100)] for x in range(140, 200, 10)]
    assert len(rodar(quadros).eventos()) == 1


def test_motorista_visto_pela_janela_nao_conta():
    quadros = []
    for x in range(40, 170, 10):
        quadros.append([
            (1, "carro", 0.9, x, 150, 100, 60),     # caixa do carro: y 90..150
            (2, "pessoa", 0.5, x, 130, 16, 20),     # motorista: inteiro dentro do carro
        ])
    c = rodar(quadros)
    assert [e["classe"] for e in c.eventos()] == ["carro"]
    assert {r["id_trilha"]: r["motivo_descarte"] for r in c.resumo_trilhas()}[2] == "pessoa_em_veiculo"


def test_caixa_duplicada_no_mesmo_veiculo_conta_uma_vez():
    quadros = []
    for x in range(40, 170, 10):
        quadros.append([
            (1, "carro", 0.9, x, 150, 100, 60),
            (2, "carro", 0.6, x + 4, 148, 96, 58),  # 2ª caixa quase igual (IoU alto)
        ])
    c = rodar(quadros)
    assert len(c.eventos()) == 1
    assert "caixa_duplicada" in {r["motivo_descarte"] for r in c.resumo_trilhas()}


def test_dois_carros_lado_a_lado_contam_dois():
    quadros = []
    for x in range(40, 170, 10):
        quadros.append([
            (1, "carro", 0.9, x, 100, 100, 60),     # faixa de cima: y 40..100
            (2, "carro", 0.9, x, 160, 110, 66),     # faixa de baixo: y 94..160 (sobreposição pequena)
        ])
    assert len(rodar(quadros).eventos()) == 2


def test_carro_estacionado_em_cima_da_linha_nao_conta():
    # caixa "pula" de x=105 para x=95 e volta (oclusão), mas o carro não sai do lugar
    xs = [105] * 20 + [95] * 5 + [105] * 20
    quadros = [[(1, "carro", 0.9, x, 100, 120, 60)] for x in xs]
    c = rodar(quadros)
    assert c.eventos() == []
    assert c.resumo_trilhas()[0]["motivo_descarte"] == "quase_parado"
