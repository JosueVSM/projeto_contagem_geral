# dados/gabarito/

Contagem de **referência** (gabarito), usada para medir o erro tanto do YOLO quanto da contagem manual.

Dois formatos (o código detecta sozinho):

**a) Só contagens** (vídeos do experimento): gerado por `scripts/03b_importar_txt.py` a partir de `dados/manual/VideoNN_Gabarito.txt`. Mesmo formato da contagem manual (linha `total`). Permite medir o erro de contagem de cada método, mas **não** precisão/revocação por evento.

**b) Por evento**, gerado pela ferramenta `scripts/03_gabarito.py`, uma linha por objeto marcado:

```
t_video_s;classe
12.433;carro
13.100;moto
```

- `t_video_s`: instante, em segundos desde o começo do **arquivo de vídeo**, em que o meio do objeto passou pela linha.
- `classe`: carro, moto, bicicleta, pessoa, cachorro, onibus ou caminhao.

> **`teste.csv`** (vídeo de calibração) foi feito pelo Claude, revisando o vídeo em recortes a cada 0,5 s e quadro a quadro nos casos de dúvida, e registrado **com a própria ferramenta** (teclas simuladas). Serve só para testar o pipeline; não é resultado do experimento.

Só são revisados os minutos indicados em `config/videos.csv` (padrão 1–3 e 8–10). A ferramenta salva a cada tecla; se fechar no meio, ela retoma de onde parou. Evite editar à mão; se precisar, mantenha o formato.
