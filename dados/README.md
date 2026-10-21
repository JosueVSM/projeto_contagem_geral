# dados/

Contagens feitas por pessoa (não pelo YOLO). São só números, sem imagens, e por isso podem ir para o GitHub.

| Pasta | Conteúdo |
|---|---|
| `manual/` | Contagem **ao vivo** feita da janela: `.txt` originais + um CSV por vídeo (total por classe) |
| `gabarito/` | Contagem de **referência** (minuciosa, assistindo ao vídeo): um CSV por vídeo, com o total por classe (ou, na calibração, uma linha por objeto marcado na ferramenta `scripts/03_gabarito.py`) |

Os `.txt` originais (`Video01.txt`, `Video01_Gabarito.txt`, ...) ficam em `manual/` e são convertidos para CSV por `scripts/03b_importar_txt.py`.

O nome de cada CSV é o `id` do vídeo em `config/videos.csv` (ex.: `v1_meio_dia.csv`).
