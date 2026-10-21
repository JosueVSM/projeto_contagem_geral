# Resumo dos resultados

## Erro contra o gabarito por classe (soma dos vídeos)

| classe | gabarito | yolo26n | yolo26l | manual | WAPE_yolo26n | WAPE_yolo26l | WAPE_manual |
|---|---|---|---|---|---|---|---|
| carro | 328 | 324 | 317 | 323 | 1,8 | 4,0 | 1,5 |
| moto | 152 | 149 | 145 | 154 | 8,6 | 7,2 | 2,6 |
| bicicleta | 24 | 22 | 27 | 24 | 16,7 | 20,8 | 0 |
| pessoa | 77 | 53 | 78 | 81 | 31,2 | 16,9 | 5,2 |
| cachorro | 2 | 0 | 1 | 2 | 100,0 | 50,0 | 0 |
| caminhao_onibus | 5 | 5 | 12 | 5 | 0 | 140,0 | 0 |

Colunas sem prefixo = total contado; WAPE_ = erro percentual contra o gabarito.

## Erro de cada contagem por classe — v1_meio_dia (12h10)

| classe | gabarito | manual | erro_manual | erro_pct_manual | yolo26n | erro_yolo26n | erro_pct_yolo26n | yolo26l | erro_yolo26l | erro_pct_yolo26l |
|---|---|---|---|---|---|---|---|---|---|---|
| carro | 76 | 74 | -2 | -2,6 | 77 | 1 | 1,3 | 75 | -1 | -1,3 |
| moto | 25 | 25 | 0 | 0 | 22 | -3 | -12,0 | 23 | -2 | -8,0 |
| bicicleta | 3 | 3 | 0 | 0 | 3 | 0 | 0 | 4 | 1 | 33,3 |
| pessoa | 19 | 20 | 1 | 5,3 | 19 | 0 | 0 | 24 | 5 | 26,3 |
| cachorro | 0 | 0 | 0 | — | 0 | 0 | — | 0 | 0 | — |
| caminhao_onibus | 3 | 3 | 0 | 0 | 3 | 0 | 0 | 6 | 3 | 100,0 |
| total | 126 | 125 | -1 | -0,8 | 124 | -2 | -1,6 | 132 | 6 | 4,8 |

## Erro de cada contagem por classe — v2_tarde_1 (15h07)

| classe | gabarito | manual | erro_manual | erro_pct_manual | yolo26n | erro_yolo26n | erro_pct_yolo26n | yolo26l | erro_yolo26l | erro_pct_yolo26l |
|---|---|---|---|---|---|---|---|---|---|---|
| carro | 61 | 61 | 0 | 0 | 60 | -1 | -1,6 | 57 | -4 | -6,6 |
| moto | 49 | 48 | -1 | -2,0 | 44 | -5 | -10,2 | 44 | -5 | -10,2 |
| bicicleta | 4 | 4 | 0 | 0 | 3 | -1 | -25,0 | 6 | 2 | 50,0 |
| pessoa | 11 | 11 | 0 | 0 | 2 | -9 | -81,8 | 7 | -4 | -36,4 |
| cachorro | 0 | 0 | 0 | — | 0 | 0 | — | 0 | 0 | — |
| caminhao_onibus | 0 | 0 | 0 | — | 0 | 0 | — | 2 | 2 | — |
| total | 125 | 124 | -1 | -0,8 | 109 | -16 | -12,8 | 116 | -9 | -7,2 |

## Erro de cada contagem por classe — v3_tarde_2 (17h12)

| classe | gabarito | manual | erro_manual | erro_pct_manual | yolo26n | erro_yolo26n | erro_pct_yolo26n | yolo26l | erro_yolo26l | erro_pct_yolo26l |
|---|---|---|---|---|---|---|---|---|---|---|
| carro | 110 | 110 | 0 | 0 | 106 | -4 | -3,6 | 103 | -7 | -6,4 |
| moto | 41 | 41 | 0 | 0 | 41 | 0 | 0 | 39 | -2 | -4,9 |
| bicicleta | 9 | 9 | 0 | 0 | 10 | 1 | 11,1 | 8 | -1 | -11,1 |
| pessoa | 27 | 27 | 0 | 0 | 17 | -10 | -37,0 | 25 | -2 | -7,4 |
| cachorro | 0 | 0 | 0 | — | 0 | 0 | — | 0 | 0 | — |
| caminhao_onibus | 2 | 2 | 0 | 0 | 2 | 0 | 0 | 4 | 2 | 100,0 |
| total | 189 | 189 | 0 | 0 | 176 | -13 | -6,9 | 179 | -10 | -5,3 |

## Erro de cada contagem por classe — v4_18h (18h04)

| classe | gabarito | manual | erro_manual | erro_pct_manual | yolo26n | erro_yolo26n | erro_pct_yolo26n | yolo26l | erro_yolo26l | erro_pct_yolo26l |
|---|---|---|---|---|---|---|---|---|---|---|
| carro | 81 | 78 | -3 | -3,7 | 81 | 0 | 0 | 82 | 1 | 1,2 |
| moto | 37 | 40 | 3 | 8,1 | 42 | 5 | 13,5 | 39 | 2 | 5,4 |
| bicicleta | 8 | 8 | 0 | 0 | 6 | -2 | -25,0 | 9 | 1 | 12,5 |
| pessoa | 20 | 23 | 3 | 15,0 | 15 | -5 | -25,0 | 22 | 2 | 10,0 |
| cachorro | 2 | 2 | 0 | 0 | 0 | -2 | -100,0 | 1 | -1 | -50,0 |
| caminhao_onibus | 0 | 0 | 0 | — | 0 | 0 | — | 0 | 0 | — |
| total | 148 | 151 | 3 | 2,0 | 144 | -4 | -2,7 | 153 | 5 | 3,4 |

## Erro de cada contagem por classe — Soma dos 4 vídeos

| classe | gabarito | manual | erro_manual | erro_pct_manual | yolo26n | erro_yolo26n | erro_pct_yolo26n | yolo26l | erro_yolo26l | erro_pct_yolo26l |
|---|---|---|---|---|---|---|---|---|---|---|
| carro | 328 | 323 | -5 | -1,5 | 324 | -4 | -1,2 | 317 | -11 | -3,4 |
| moto | 152 | 154 | 2 | 1,3 | 149 | -3 | -2,0 | 145 | -7 | -4,6 |
| bicicleta | 24 | 24 | 0 | 0 | 22 | -2 | -8,3 | 27 | 3 | 12,5 |
| pessoa | 77 | 81 | 4 | 5,2 | 53 | -24 | -31,2 | 78 | 1 | 1,3 |
| cachorro | 2 | 2 | 0 | 0 | 0 | -2 | -100,0 | 1 | -1 | -50,0 |
| caminhao_onibus | 5 | 5 | 0 | 0 | 5 | 0 | 0 | 12 | 7 | 140,0 |
| total | 588 | 589 | 1 | 0,2 | 553 | -35 | -6,0 | 580 | -8 | -1,4 |

erro = contagem − gabarito (negativo = contou a menos); erro_pct = erro ÷ gabarito.

## Desempenho (velocidade)

| video | periodo | modelo | quadros_processados | tempo_total_s | quadros_por_segundo | ms_por_quadro_deteccao_rastreamento_mediana | ms_inferencia_mediana | tempo_real_x | memoria_gpu_pico_mb | gpu |
|---|---|---|---|---|---|---|---|---|---|---|
| média |  | yolo26n | 18375,2 | 244,6 | 75,1 | 11,6 | 7,9 | 2,5 | 95,8 | — |
| média |  | yolo26l | 18375,2 | 335,7 | 54,8 | 16,4 | 12,9 | 1,8 | 193,7 | — |
