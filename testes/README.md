# testes/

Testes automáticos que provam que o software faz o que a metodologia descreve. **Nenhum precisa dos vídeos do experimento**, e **nenhum número daqui é resultado do trabalho**: os dados são artificiais, criados de propósito.

| Arquivo | O que testa | Como rodar |
|---|---|---|
| `test_contador.py` | Regra de contagem com trajetórias inventadas: objeto que cruza conta 1 vez; parado ou que não cruza não conta; vai e volta conta 1; cruzar fora da linha não conta; voto de classe; pessoa na moto não conta; motorista visto pela janela não conta; pedestre ao lado conta; caixa duplicada conta 1; carros lado a lado contam 2; troca de id após a linha não duplica | `python -m pytest testes` |
| `test_metricas.py` | Contagem por minuto (início e fim da janela), contagem manual por minuto / blocos / total, agregação em blocos, casamento de eventos, precisão/revocação, matriz de confusão (mesma classe primeiro), viés/EAM/WAPE, tendência, leitura e validação do CSV manual | `python -m pytest testes` |
| `test_gabarito.py` | Ferramenta de gabarito **sem janela e sem teclado**: a tela é substituída e as teclas vêm de uma lista programada. Confere marcação no instante certo, desfazer (`z`), pausa + quadro a quadro, salto automático entre blocos de minutos e retomada de um arquivo salvo | `python -m pytest testes` |
| `teste_integracao.py` | Pipeline **completo** (passos 2, 4 e 5) num vídeo **sintético** montado com as imagens de exemplo da Ultralytics, numa pasta temporária apagada no final. Usa a GPU e baixa os pesos na 1ª vez | `python testes/teste_integracao.py` |
| `conftest.py` | Configuração do pytest (permite importar `src/`) | — |

Resultado esperado: `35 passed` no pytest e `OK: pipeline completo rodou sem erros.` na integração.
