# scripts/

Os passos do experimento, **em ordem**. Rode sempre a partir da raiz do projeto, com o ambiente virtual ativado:

```bash
<pasta do ambiente virtual>\Scripts\activate    (ex.: C:\Users\<voce>\venvs\visao_contagem)
python scripts/00_verificar_ambiente.py
```

Todo script aceita `--help`, que mostra as opções.

| Script | O que faz | Entrada | Saída |
|---|---|---|---|
| `00_verificar_ambiente.py` | Confere GPU, versões das bibliotecas e quais vídeos já existem e têm linha definida | — | texto na tela |
| `01_definir_linha.py` | Abre um quadro do vídeo; você clica 2 pontos para a linha de contagem. `--copiar-de` reaproveita a linha de outro vídeo | vídeo | `config/linhas.json` e imagem de conferência (fora do repositório) |
| `02_contar_yolo.py` | Detecta, rastreia e conta com cada modelo. `--salvar-video` grava o vídeo anotado; `--max-segundos 60` processa só o começo (teste rápido); `--mostrar` exibe na tela | vídeo + linha | `resultados/yolo/<video>/<modelo>/` |
| `03_gabarito.py` | Ferramenta de teclado para a contagem de referência (teclas no topo do arquivo) | vídeo + linha | `dados/gabarito/<video>.csv` |
| `03b_importar_txt.py` | Importa contagens **totais** escritas em `.txt` (`Video01.txt` = ao vivo, `Video01_Gabarito.txt` = gabarito) e gera os CSVs. Usa a coluna `contagem_txt` de `config/videos.csv`. Não altera os `.txt` | `dados/manual/*.txt` | `dados/manual/<id>.csv`, `dados/gabarito/<id>.csv` |
| `04_comparar.py` | Cruza YOLO, manual e gabarito e gera as tabelas de **erro por classe** (T01, T02, T03, T03b, T03c), de velocidade (T07) e, só na calibração, precisão/revocação (T05, T06) + `RESUMO.md`. `--teste` processa só os vídeos de teste | tudo acima | `resultados/tabelas/` |
| `05_graficos.py` | Gráficos de erro por classe e de velocidade em PNG 300 dpi | tabelas | `resultados/graficos/` |
| `06_videos_demo.py` | Clipes de **30 s no início e 30 s no fim** de cada vídeo com os dois modelos **lado a lado** contando (caixas, ids, linha, contador acumulado desde 00:00, vindo da contagem oficial do passo 2). H.264, para apresentação e para o painel | vídeo + linha | `~/dados_visao/videos_demo/<id>_inicio.mp4` e `_fim.mp4` (fora do repositório) |
| `_caminhos.py` | Auxiliar: permite que os scripts importem `src/` | — | — |

## Observações
- **Medição de velocidade:** a comparação de tempo deve usar a rodada **sem** `--salvar-video` e sem `--mostrar`, porque desenhar e gravar o vídeo também gasta tempo. O `desempenho.json` registra se o vídeo anotado foi gravado.
- Se o resultado de um vídeo/modelo já existe, o passo 2 pula esse vídeo. Use `--refazer` para processar de novo, por exemplo depois de mudar a linha ou o `config.yaml`.
- Os passos 4 e 5 podem ser rodados quantas vezes quiser: só leem o que existe e nunca inventam valores para dados faltantes.
