# config/

Configuração do experimento. Todos os scripts leem daqui; **não há parâmetro "escondido" no código**.

| Arquivo | O que é | Quem edita |
|---|---|---|
| `config.yaml` | Parâmetros gerais: pastas, modelos comparados (`yolo26n`, `yolo26l`), opções do detector (tamanho da imagem, confiança, FP16), classes e seus ids no COCO, limiares da regra de contagem e tolerância de tempo da comparação | Você, à mão (registre no trabalho qualquer mudança) |
| `videos.csv` | Uma linha por vídeo: arquivo, se entra na análise, data/hora, período, iluminação, **segundo do "começou!"** (`inicio_contagem_s`), duração da contagem e minutos do gabarito | Você, à mão (Excel ou bloco de notas; separador `;`) |
| `linhas.json` | Os dois pontos da linha de contagem de cada vídeo, em pixels | Gerado por `scripts/01_definir_linha.py` |

## Colunas de `videos.csv`

| Coluna | Exemplo | Significado |
|---|---|---|
| `id` | `v1_meio_dia` | Nome curto, usado em todas as pastas de resultado |
| `arquivo` | `v1_meio_dia.mp4` | Nome do arquivo em `~/dados_visao/videos/` |
| `usar_na_analise` | `sim` / `nao` | `nao` = vídeo de teste, que nunca entra nos resultados |
| `data`, `hora_inicio` | `2026-10-26`, `12:03` | Informativos |
| `periodo` | `meio-dia` | Rótulo que aparece em tabelas e gráficos |
| `iluminacao` | `dia` / `noite` | Informativo |
| `inicio_contagem_s` | `4,2` | Segundo do vídeo em que o cronômetro foi disparado (o minuto 1 começa aqui) |
| `duracao_s` | `600` | Duração da contagem (10 min) |
| `minutos_gabarito` | `1-10` | Minutos revisados no gabarito (todos, porque a contagem manual é só o total) |
| `observacoes` | texto livre (sem `;`) | |
| `contagem_txt` | `Video01` | Nome base dos `.txt` de contagem (usado por `03b_importar_txt.py`) |

## Principais parâmetros de `config.yaml`

- `deteccao.conf: 0.1`: confiança mínima repassada ao **ByteTrack**. O valor é baixo de propósito: o rastreador usa detecções fracas para manter o objeto em oclusões curtas, mas **só cria** trilhas novas a partir de 0,25.
- `contagem.min_quadros_trilha: 3`: trilhas mais curtas são descartadas como ruído.
- `contagem.sobreposicao_montado: 0.3` e `frac_montado_min: 0.5`: filtro de "pessoa em moto/bicicleta" (ver README principal).
- `contagem.sobreposicao_em_veiculo: 0.9`: pessoa ≥ 90% dentro de carro/ônibus/caminhão = motorista visto pela janela.
- `contagem.iou_duplicada: 0.7`: duas caixas quase iguais cruzando juntas = mesmo veículo.
- `contagem.min_deslocamento_px: 60`: trilha que quase não anda atravessando a linha (carro estacionado em cima dela) não conta.
- `analise.agrupar_classes`: classes somadas na comparação. Hoje `caminhao_onibus: [caminhao, onibus]`, porque a contagem manual juntou as duas. O YOLO continua detectando separado.
- `comparacao.tolerancia_s: 1.5`: diferença máxima de tempo para considerar que YOLO e gabarito marcaram o mesmo cruzamento.
