# src/

Código reutilizável, importado pelos scripts de `scripts/` e pelos testes de `testes/`. Nada aqui é executado diretamente.

| Módulo | O que faz |
|---|---|
| `configuracao.py` | Lê `config/config.yaml`, `config/videos.csv` e `config/linhas.json`. Aceita CSV com `;` ou `,` e vírgula decimal, como o Excel em português salva |
| `geometria.py` | Matemática da linha virtual: de que lado da linha um ponto está (sinal do produto vetorial), onde o deslocamento cortou a linha, sentido do movimento e sobreposição entre caixas |
| `contador.py` | **Regra de contagem.** Recebe as detecções rastreadas de cada quadro e decide quem conta: cruzamento da linha, uma vez por trilha, classe por voto ponderado, filtro de pessoa montada e descarte de trilhas curtas. Não depende do YOLO, por isso é testável com trajetórias artificiais |
| `processamento.py` | Laço principal: abre o vídeo, aquece a GPU, roda **YOLO26 + ByteTrack** quadro a quadro, alimenta o contador, mede os tempos e (opcionalmente) grava o vídeo anotado |
| `dados.py` | Lê e **valida** a contagem manual (`dados/manual/`) e o gabarito (`dados/gabarito/`): acusa coluna faltando, minuto repetido ou célula vazia |
| `metricas.py` | Contagem por minuto, viés, EAM, WAPE, casamento de eventos pelo algoritmo húngaro (precisão/revocação/F1), matriz de confusão e tendência do erro ao longo do vídeo |

## Fluxo

```
vídeo ──► processamento.py ──(detecções com id)──► contador.py ──► eventos (tempo, classe)
                                                                        │
manual (papel) ──► dados.py ─┐                                          │
gabarito ────────► dados.py ─┴──────────────► metricas.py ◄─────────────┘
```
