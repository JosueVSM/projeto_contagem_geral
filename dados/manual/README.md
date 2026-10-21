# dados/manual/

Contagem manual **ao vivo** (da ficha de papel), digitada no computador.

## Arquivos desta pasta
- `VideoNN.txt`: contagem **ao vivo** (original, como foi entregue).
- `VideoNN_Gabarito.txt`: **gabarito** (contagem minuciosa assistindo ao vídeo; original).
- `<id>.csv`: contagem ao vivo convertida por `scripts/03b_importar_txt.py` (o gabarito convertido vai para `dados/gabarito/`).

## Formatos aceitos (coluna `minuto`)
- **por minuto**: `1`, `2`, … `10`
- **por blocos**: `1-3`, `4-7`, `8-10` (sem sobreposição)
- **só o total**: uma única linha `total` (= a janela inteira de contagem)

Quanto mais detalhado, mais análises ficam possíveis (ver `docs/protocolo_experimento.md`, seção 6). Uma planilha copiada do modelo e ainda **toda vazia** é ignorada com um aviso.

```
minuto;carro;moto;bicicleta;pessoa;cachorro;onibus;caminhao;observacoes
total;198;61;7;12;1;4;3;
```
(números ilustrativos, não são dados)

## Como preencher
1. Copie `MODELO_contagem_manual.csv` e renomeie para o id do vídeo, por exemplo `v1_meio_dia.csv`.
2. Abra no Excel ou no bloco de notas e preencha **um número por célula**. Use `0` quando não passou nenhum objeto daquela classe no minuto. Célula vazia dá erro, de propósito, para não confundir "zero" com "esqueci".
3. A coluna `observacoes` é opcional (ex.: `ônibus parado tapando a visão`).
4. Salve como **CSV** (separado por `;`). Se o Excel perguntar, mantenha o formato CSV.

```
minuto;carro;moto;bicicleta;pessoa;cachorro;onibus;caminhao;observacoes
1;23;9;2;5;0;1;0;
2;19;11;1;3;1;0;1;caminhão de lixo
```

> Os números acima são só um exemplo de formato, não são dados.

Quem lê esses arquivos é `src/dados.py`, usado por `scripts/04_comparar.py`. Arquivos começando com `MODELO_` são ignorados.
