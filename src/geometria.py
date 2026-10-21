"""Funções geométricas usadas na regra de contagem por linha virtual.

Ideia: a linha de contagem é um segmento A-B desenhado na imagem. Para saber
de que lado da linha um ponto P está, usamos o sinal do produto vetorial
(B - A) x (P - A): positivo de um lado, negativo do outro, zero em cima.
Quando o sinal muda entre dois quadros, o objeto cruzou a linha.
"""

from __future__ import annotations

Ponto = tuple[float, float]


def lado_da_linha(p: Ponto, a: Ponto, b: Ponto) -> float:
    """Produto vetorial (B-A) x (P-A). O sinal indica o lado da linha."""
    return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])


def sinal(valor: float) -> int:
    return (valor > 0) - (valor < 0)


def posicao_no_segmento(p: Ponto, a: Ponto, b: Ponto) -> float:
    """Projeção de P sobre A-B: 0 = em A, 1 = em B, fora de [0,1] = além das pontas."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    comp2 = dx * dx + dy * dy
    if comp2 == 0:
        return 0.0
    return ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / comp2


def ponto_de_cruzamento(p_ant: Ponto, p_atual: Ponto, a: Ponto, b: Ponto) -> Ponto:
    """Ponto onde o deslocamento p_ant -> p_atual corta a reta A-B."""
    l_ant = lado_da_linha(p_ant, a, b)
    l_atual = lado_da_linha(p_atual, a, b)
    if l_ant == l_atual:
        return p_atual
    s = l_ant / (l_ant - l_atual)
    return (p_ant[0] + s * (p_atual[0] - p_ant[0]), p_ant[1] + s * (p_atual[1] - p_ant[1]))


def sentido_do_movimento(p_ant: Ponto, p_atual: Ponto, a: Ponto, b: Ponto) -> str:
    """Rótulo legível do sentido do cruzamento.

    Se a linha é mais "em pé" (rua horizontal na imagem), o sentido é
    'para_direita'/'para_esquerda'; se é mais "deitada", 'para_baixo'/'para_cima'.
    """
    dx, dy = b[0] - a[0], b[1] - a[1]
    mx, my = p_atual[0] - p_ant[0], p_atual[1] - p_ant[1]
    if abs(dy) >= abs(dx):  # linha mais vertical
        return "para_direita" if mx > 0 else "para_esquerda"
    return "para_baixo" if my > 0 else "para_cima"


def ponto_base(caixa: tuple[float, float, float, float]) -> Ponto:
    """Ponto de referência do objeto: centro da base da caixa (onde toca o chão)."""
    x1, y1, x2, y2 = caixa
    return ((x1 + x2) / 2.0, y2)


def fracao_dentro(caixa_a, caixa_b) -> float:
    """Fração da área da caixa A que está dentro da caixa B (0 a 1)."""
    ax1, ay1, ax2, ay2 = caixa_a
    bx1, by1, bx2, by2 = caixa_b
    ix = max(0.0, min(ax2, bx2) - max(ax1, bx1))
    iy = max(0.0, min(ay2, by2) - max(ay1, by1))
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    return (ix * iy) / area_a if area_a > 0 else 0.0


def iou(caixa_a, caixa_b) -> float:
    """Interseção sobre união (0 = separadas, 1 = idênticas)."""
    ax1, ay1, ax2, ay2 = caixa_a
    bx1, by1, bx2, by2 = caixa_b
    ix = max(0.0, min(ax2, bx2) - max(ax1, bx1))
    iy = max(0.0, min(ay2, by2) - max(ay1, by1))
    inter = ix * iy
    uniao = (ax2 - ax1) * (ay2 - ay1) + (bx2 - bx1) * (by2 - by1) - inter
    return inter / uniao if uniao > 0 else 0.0
