# Resumo dos resultados

> **ATENÇÃO: vídeos de TESTE/CALIBRAÇÃO. Estes números NÃO são resultados do experimento.**

## Observações sobre os dados

- teste: sem contagem manual (dados/manual/teste.csv)

## Totais nos minutos do gabarito

| video | periodo | minutos | classe | gabarito | yolo26n | yolo26l |
|---|---|---|---|---|---|---|
| teste | teste | 1-4 | carro | 30 | 30 | 26 |
| teste | teste | 1-4 | moto | 10 | 10 | 10 |
| teste | teste | 1-4 | bicicleta | 2 | 2 | 2 |
| teste | teste | 1-4 | pessoa | 1 | 1 | 1 |
| teste | teste | 1-4 | cachorro | 0 | 0 | 0 |
| teste | teste | 1-4 | caminhao_onibus | 0 | 1 | 4 |
| teste | teste | 1-4 | total | 43 | 44 | 43 |

## Erro contra o gabarito por classe (soma dos vídeos)

| classe | gabarito | yolo26n | yolo26l | WAPE_yolo26n | WAPE_yolo26l |
|---|---|---|---|---|---|
| carro | 30 | 30 | 26 | 0 | 13,3 |
| moto | 10 | 10 | 10 | 0 | 0 |
| bicicleta | 2 | 2 | 2 | 0 | 0 |
| pessoa | 1 | 1 | 1 | 0 | 0 |
| cachorro | 0 | 0 | 0 | — | — |
| caminhao_onibus | 0 | 1 | 4 | — | — |

Colunas sem prefixo = total contado; WAPE_ = erro percentual contra o gabarito.

## Precisão / revocação (todas as classes)

| video | periodo | modelo | classe | vp | fp | fn | precisao | revocacao | f1 |
|---|---|---|---|---|---|---|---|---|---|
| teste | teste | yolo26n | todas | 43 | 1 | 0 | 0,977 | 1,0 | 0,989 |
| teste | teste | yolo26l | todas | 39 | 4 | 4 | 0,907 | 0,907 | 0,907 |
| todos | todos | yolo26n | todas | 43 | 1 | 0 | 0,977 | 1,0 | 0,989 |
| todos | todos | yolo26l | todas | 39 | 4 | 4 | 0,907 | 0,907 | 0,907 |

## Matriz de confusão — yolo26n

| gabarito | carro | moto | bicicleta | pessoa | cachorro | caminhao_onibus | nao_detectado |
|---|---|---|---|---|---|---|---|
| carro | 30 | 0 | 0 | 0 | 0 | 0 | 0 |
| moto | 0 | 10 | 0 | 0 | 0 | 0 | 0 |
| bicicleta | 0 | 0 | 2 | 0 | 0 | 0 | 0 |
| pessoa | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| cachorro | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| caminhao_onibus | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| nao_existe | 0 | 0 | 0 | 0 | 0 | 1 | 0 |

## Matriz de confusão — yolo26l

| gabarito | carro | moto | bicicleta | pessoa | cachorro | caminhao_onibus | nao_detectado |
|---|---|---|---|---|---|---|---|
| carro | 26 | 0 | 0 | 0 | 0 | 4 | 0 |
| moto | 0 | 10 | 0 | 0 | 0 | 0 | 0 |
| bicicleta | 0 | 0 | 2 | 0 | 0 | 0 | 0 |
| pessoa | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| cachorro | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| caminhao_onibus | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| nao_existe | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## Desempenho (velocidade)

| video | periodo | modelo | quadros_processados | tempo_total_s | quadros_por_segundo | ms_por_quadro_deteccao_rastreamento_mediana | ms_inferencia_mediana | tempo_real_x | memoria_gpu_pico_mb | gpu |
|---|---|---|---|---|---|---|---|---|---|---|
| média |  | yolo26n | 5856,0 | 79,4 | 73,7 | 11,8 | 7,8 | 2,5 | 48,3 | — |
| média |  | yolo26l | 5856,0 | 118,7 | 49,3 | 17,2 | 13,3 | 1,6 | 182,3 | — |
