# resultados/graficos/

Gerado por `scripts/05_graficos.py`: PNG em 300 dpi, pronto para o trabalho. As cores são as mesmas em todos os gráficos: **gabarito = cinza escuro, manual = azul, YOLO26-n = laranja, YOLO26-l = verde-água**.

| Gráfico | Mostra |
|---|---|
| `G01_totais_por_classe.png` | Total por classe em cada vídeo (gabarito × manual × YOLO-n × YOLO-l) |
| `G02_erro_por_classe_por_video.png` | **Erro de cada contagem** por classe, em cada vídeo (contagem − gabarito) |
| `G03_wape_por_classe_vs_gabarito.png` | Erro percentual (WAPE) por classe, somando os vídeos, com o tamanho da amostra (n) |
| `G04_vies_por_classe_vs_gabarito.png` | Se cada método conta a mais ou a menos, por classe (soma dos vídeos) |
| `G03_/G04_..._vs_manual.png` | O mesmo, mas como **diferença** em relação à contagem manual |
| `G08_velocidade_modelos.png` | Quadros por segundo de cada modelo |
| `G09_tempo_por_quadro.png` | Distribuição do tempo por quadro |

Os valores exatos estão em `resultados/tabelas/`.
