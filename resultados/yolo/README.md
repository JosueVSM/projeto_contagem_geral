# resultados/yolo/

Saída de `scripts/02_contar_yolo.py`. As subpastas são criadas automaticamente: `<id_do_video>/<modelo>/`, por exemplo `v1_meio_dia/yolo26n/`.

| Arquivo | Conteúdo |
|---|---|
| `eventos.csv` | **Um objeto contado por linha**: id da trilha, instante do cruzamento (`t_video_s`), minuto da contagem, classe final, sentido, confiança média e número de quadros |
| `contagem_por_minuto.csv` | Tabela minuto (1–10) × classe |
| `trilhas.csv` | **Todas** as trilhas, inclusive as que não contaram, com o motivo (`nao_cruzou`, `trilha_curta`, `pessoa_montada`) e os votos de classe. Serve para investigar erros |
| `desempenho.json` | Tempo total, quadros/s, ms por quadro (mediana), memória de GPU, versões e GPU usadas |
| `ms_por_quadro.csv` | Tempo de cada quadro, usado no gráfico de distribuição do tempo |

Pastas terminadas em `_parcial_<N>s` vêm de rodadas com `--max-segundos` (testes rápidos) e não são usadas pela comparação.
