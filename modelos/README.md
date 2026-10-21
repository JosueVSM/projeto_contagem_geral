# modelos/

Pesos pré-treinados (COCO) dos modelos YOLO usados na comparação:

| Arquivo | Modelo | Tamanho |
|---|---|---|
| `yolo26n.pt` | YOLO26 nano | ≈ 5 MB |
| `yolo26l.pt` | YOLO26 large | ≈ 53 MB |

Os arquivos `.pt` **não vão para o GitHub** (ver `.gitignore`). Eles são **baixados automaticamente** da Ultralytics na primeira execução de `scripts/02_contar_yolo.py` e guardados aqui. Não há treinamento neste projeto: os modelos são usados como vêm.
