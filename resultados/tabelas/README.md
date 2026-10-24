# resultados/tabelas/

Gerado por `scripts/04_comparar.py`. Os CSVs usam `;` e vírgula decimal, então abrem direto no Excel em português. O `RESUMO.md` traz as principais tabelas prontas em Markdown.

Por decisão do trabalho, as tabelas tratam do **erro por classe** nos 10 minutos de cada vídeo (sem análise por minuto). Entre horários, só a comparação **dia × noite** (`T04`), pedida pelo professor.

| Tabela | Pergunta que responde |
|---|---|
| `T01_totais_janela_completa.csv` | Quanto cada contagem (gabarito, manual, YOLO-n, YOLO-l) somou por classe em cada vídeo? |
| `T02_yolo_vs_manual.csv` | Qual a **diferença** entre YOLO e manual, por classe? (manual como referência) |
| `T03_erro_vs_gabarito.csv` | Erro de cada método contra o gabarito, por classe e vídeo: viés, viés % e WAPE |
| `T03b_erro_por_classe_todos.csv` | Soma dos vídeos: contagens e WAPE por classe |
| `T03c_erro_por_classe_por_video.csv` | **Erro de cada contagem**: para cada vídeo e classe, contagem, erro (contagem − gabarito) e erro % de cada método (+ linhas `todos`) |
| `T04_dia_x_noite.csv` | **Dia × noite**: 12h10 × 18h04, só pessoa e moto (config `analise.comparar_horarios`): erro de cada contagem e confiança média que o YOLO deu aos objetos que contou |
| `T07_desempenho_modelos.csv` | Velocidade de cada modelo (quadros/s, ms/quadro, memória de GPU) |
| `T05_precisao_revocacao.csv`, `T06_confusao_<modelo>.csv` | Só na calibração (`resultados/calibracao/`), onde o gabarito é por evento |

Linhas com `video = todos` juntam todos os vídeos.
