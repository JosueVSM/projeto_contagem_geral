"""Regra de contagem: cada objeto rastreado é contado UMA vez ao cruzar a linha.

Este módulo não depende do YOLO: recebe, quadro a quadro, a lista de
detecções já rastreadas (com id de trilha) e decide o que contar. Por isso
ele pode ser testado com trajetórias artificiais (ver testes/).

Regras (justificativa no README principal):
  1. Ponto de referência = centro da base da caixa.
  2. Conta quando esse ponto troca de lado da linha, dentro do segmento.
  3. Cada id de trilha conta no máximo uma vez (o 1º cruzamento vale).
  4. A classe final da trilha é decidida por voto ponderado pela confiança
     em TODOS os quadros (evita "carro" virar "caminhão" num quadro só).
  5. Pessoa sobre moto/bicicleta na maior parte da trilha = condutor ou
     passageiro -> não conta como pessoa (a moto/bicicleta já foi contada).
  6. Pessoa inteiramente dentro da caixa de carro/ônibus/caminhão na maior
     parte da trilha = motorista/passageiro visto pela janela -> não conta.
  7. Duas trilhas com caixas quase iguais (IoU alto) cruzando juntas são o
     MESMO veículo detectado duas vezes -> conta uma só.
  8. Trilhas muito curtas (< min_quadros_trilha) são descartadas.
  9. Trilha que quase não se desloca na direção que atravessa a linha
     (< min_deslocamento_px) não conta: é veículo ESTACIONADO em cima da linha
     cuja caixa "pulou" de lado por oclusão (alguém passou na frente).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from geometria import (
    fracao_dentro,
    iou,
    lado_da_linha,
    ponto_base,
    ponto_de_cruzamento,
    posicao_no_segmento,
    sentido_do_movimento,
    sinal,
)

CLASSES_DUAS_RODAS = ("moto", "bicicleta")
CLASSES_FECHADAS = ("carro", "onibus", "caminhao")  # veículos onde a pessoa vai DENTRO


@dataclass
class Deteccao:
    id_trilha: int
    classe: str
    conf: float
    caixa: tuple[float, float, float, float]  # x1, y1, x2, y2 em pixels


@dataclass
class Trilha:
    id_trilha: int
    votos: Counter = field(default_factory=Counter)  # classe -> soma das confianças
    n_quadros: int = 0
    n_montado: int = 0  # quadros em que (sendo pessoa) estava sobre moto/bicicleta
    n_em_veiculo: int = 0  # quadros em que (sendo pessoa) estava dentro de carro/ônibus/caminhão
    duplicada_de: int | None = None  # id da trilha "original", se esta for caixa duplicada
    soma_conf: float = 0.0
    primeiro_t: float | None = None
    primeiro_ponto: tuple[float, float] | None = None
    ultimo_t: float | None = None
    ultimo_ponto: tuple[float, float] | None = None
    ultimo_lado: int = 0  # lado da linha no último quadro em que não estava em cima dela
    ponto_antes_do_lado: tuple[float, float] | None = None
    # Dados do cruzamento (preenchidos uma única vez)
    t_cruzamento: float | None = None
    quadro_cruzamento: int | None = None
    sentido: str | None = None

    @property
    def classe_votada(self) -> str | None:
        return self.votos.most_common(1)[0][0] if self.votos else None


class ContadorLinha:
    def __init__(self, p1, p2, cfg_contagem: dict):
        self.a = tuple(map(float, p1))
        self.b = tuple(map(float, p2))
        self.min_quadros = int(cfg_contagem.get("min_quadros_trilha", 3))
        self.lim_sobreposicao = float(cfg_contagem.get("sobreposicao_montado", 0.3))
        self.frac_montado_min = float(cfg_contagem.get("frac_montado_min", 0.5))
        self.margem = float(cfg_contagem.get("margem_segmento", 0.05))
        self.lim_em_veiculo = float(cfg_contagem.get("sobreposicao_em_veiculo", 0.9))
        self.iou_duplicada = float(cfg_contagem.get("iou_duplicada", 0.7))
        self.min_deslocamento = float(cfg_contagem.get("min_deslocamento_px", 0))
        # Vetor unitário perpendicular à linha: mede o quanto o objeto andou "atravessando" a linha.
        dx, dy = self.b[0] - self.a[0], self.b[1] - self.a[1]
        comp = (dx * dx + dy * dy) ** 0.5 or 1.0
        self.normal = (-dy / comp, dx / comp)
        self.trilhas: dict[int, Trilha] = {}

    # ------------------------------------------------------------------
    def atualizar(self, quadro: int, t_s: float, deteccoes: list[Deteccao]) -> list[int]:
        """Processa as detecções de um quadro. Devolve ids que cruzaram AGORA."""
        caixas_2rodas = [d.caixa for d in deteccoes if d.classe in CLASSES_DUAS_RODAS]
        caixas_fechadas = [d.caixa for d in deteccoes if d.classe in CLASSES_FECHADAS]
        cruzaram_agora = []

        for d in deteccoes:
            tr = self.trilhas.get(d.id_trilha)
            if tr is None:
                tr = self.trilhas[d.id_trilha] = Trilha(d.id_trilha)
                tr.primeiro_t = t_s

            tr.votos[d.classe] += d.conf
            tr.n_quadros += 1
            tr.soma_conf += d.conf
            tr.ultimo_t = t_s
            if d.classe == "pessoa" and any(
                fracao_dentro(d.caixa, c) >= self.lim_sobreposicao for c in caixas_2rodas
            ):
                tr.n_montado += 1
            if d.classe == "pessoa" and any(
                fracao_dentro(d.caixa, c) >= self.lim_em_veiculo for c in caixas_fechadas
            ):
                tr.n_em_veiculo += 1

            p = ponto_base(d.caixa)
            if tr.primeiro_ponto is None:
                tr.primeiro_ponto = p
            lado = sinal(lado_da_linha(p, self.a, self.b))

            if lado != 0:
                if (
                    tr.ultimo_lado != 0
                    and lado != tr.ultimo_lado
                    and tr.t_cruzamento is None
                    and self._dentro_do_segmento(tr.ponto_antes_do_lado, p)
                ):
                    tr.t_cruzamento = t_s
                    tr.quadro_cruzamento = quadro
                    tr.sentido = sentido_do_movimento(tr.ponto_antes_do_lado, p, self.a, self.b)
                    cruzaram_agora.append(d.id_trilha)
                tr.ultimo_lado = lado
                tr.ponto_antes_do_lado = p
            tr.ultimo_ponto = p

        self._marcar_duplicadas(cruzaram_agora, deteccoes)
        return cruzaram_agora

    def _marcar_duplicadas(self, cruzaram_agora: list[int], deteccoes: list[Deteccao]) -> None:
        """Caixa duplicada: o detector às vezes põe 2 caixas quase iguais no mesmo
        veículo, e o rastreador cria 2 trilhas. Se, no quadro em que uma trilha
        cruza, existe outra trilha JÁ CONTADA com caixa quase igual (IoU alto),
        a nova é marcada como duplicada. Pessoas ficam de fora (têm regra própria)."""
        por_id = {d.id_trilha: d for d in deteccoes}
        for novo in cruzaram_agora:
            d_novo = por_id[novo]
            if d_novo.classe == "pessoa":
                continue
            for d in deteccoes:
                outra = self.trilhas[d.id_trilha]
                if (
                    d.id_trilha != novo
                    and d.classe != "pessoa"
                    and outra.t_cruzamento is not None
                    and outra.duplicada_de is None
                    and iou(d_novo.caixa, d.caixa) >= self.iou_duplicada
                ):
                    self.trilhas[novo].duplicada_de = d.id_trilha
                    break

    def deslocamento(self, tr: Trilha) -> float:
        """Quanto a trilha andou (px) na direção perpendicular à linha, do 1º ao último quadro."""
        if tr.primeiro_ponto is None or tr.ultimo_ponto is None:
            return 0.0
        mx = tr.ultimo_ponto[0] - tr.primeiro_ponto[0]
        my = tr.ultimo_ponto[1] - tr.primeiro_ponto[1]
        return abs(mx * self.normal[0] + my * self.normal[1])

    def _dentro_do_segmento(self, p_ant, p_atual) -> bool:
        cruz = ponto_de_cruzamento(p_ant, p_atual, self.a, self.b)
        t = posicao_no_segmento(cruz, self.a, self.b)
        return -self.margem <= t <= 1 + self.margem

    # ------------------------------------------------------------------
    def motivo_descarte(self, tr: Trilha) -> str | None:
        """None se a trilha conta; senão o motivo de não contar."""
        if tr.t_cruzamento is None:
            return "nao_cruzou"
        if tr.n_quadros < self.min_quadros:
            return "trilha_curta"
        if self.deslocamento(tr) < self.min_deslocamento:
            return "quase_parado"
        if tr.duplicada_de is not None:
            return "caixa_duplicada"
        if tr.classe_votada == "pessoa":
            if tr.n_montado / tr.n_quadros >= self.frac_montado_min:
                return "pessoa_montada"
            if tr.n_em_veiculo / tr.n_quadros >= self.frac_montado_min:
                return "pessoa_em_veiculo"
        return None

    def contagem_parcial(self) -> Counter:
        """Contagem até o momento (usada no vídeo anotado)."""
        c = Counter()
        for tr in self.trilhas.values():
            if self.motivo_descarte(tr) is None:
                c[tr.classe_votada] += 1
        return c

    def resumo_trilhas(self) -> list[dict]:
        """Uma linha por trilha (inclusive as descartadas), para diagnóstico."""
        linhas = []
        for tr in self.trilhas.values():
            total_votos = sum(tr.votos.values())
            linhas.append(
                {
                    "id_trilha": tr.id_trilha,
                    "classe": tr.classe_votada,
                    "fracao_voto_classe": round(tr.votos[tr.classe_votada] / total_votos, 3) if total_votos else None,
                    "votos": ", ".join(f"{k}:{v:.2f}" for k, v in tr.votos.most_common()),
                    "n_quadros": tr.n_quadros,
                    "conf_media": round(tr.soma_conf / tr.n_quadros, 3) if tr.n_quadros else None,
                    "frac_montado": round(tr.n_montado / tr.n_quadros, 3) if tr.n_quadros else None,
                    "frac_em_veiculo": round(tr.n_em_veiculo / tr.n_quadros, 3) if tr.n_quadros else None,
                    "duplicada_de": tr.duplicada_de,
                    "deslocamento_px": round(self.deslocamento(tr), 1),
                    "primeiro_t_s": tr.primeiro_t,
                    "ultimo_t_s": tr.ultimo_t,
                    "t_cruzamento_s": tr.t_cruzamento,
                    "sentido": tr.sentido,
                    "contada": self.motivo_descarte(tr) is None,
                    "motivo_descarte": self.motivo_descarte(tr) or "",
                }
            )
        return linhas

    def eventos(self) -> list[dict]:
        """Lista final de objetos contados (um por trilha), ordenada no tempo."""
        evs = [
            {
                "id_trilha": r["id_trilha"],
                "t_video_s": r["t_cruzamento_s"],
                "classe": r["classe"],
                "sentido": r["sentido"],
                "conf_media": r["conf_media"],
                "n_quadros": r["n_quadros"],
            }
            for r in self.resumo_trilhas()
            if r["contada"]
        ]
        return sorted(evs, key=lambda e: e["t_video_s"])
