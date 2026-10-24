# Protocolo do experimento

Este documento descreve **como** os vídeos são gravados e **como** as contagens são feitas, para que o experimento seja repetível e justo entre os métodos. Tudo o que estiver marcado como *(a confirmar)* ainda depende de teste prático.

## 1. Preparação da câmera

| Item | Configuração | Por quê |
|---|---|---|
| Resolução | **1080p** (não 4K) | Suficiente para o YOLO, que reduz a imagem para 640 px; arquivo menor e processamento mais rápido |
| Taxa de quadros | **30 quadros/s** | 60 quadros/s dobraria o processamento sem ganho para contagem |
| Taxa de quadros automática / modo noturno | **Desligar** (iPhone: Ajustes › Câmera › Gravar Vídeo › desmarcar "Taxa de Quadros Automática") | No escuro o celular reduz os quadros/s sozinho, e as 4 gravações devem ser comparáveis |
| Formato | "Mais compatível" (H.264), se houver a opção | Abre em qualquer programa; HEVC também funciona |
| Apoio | Celular **preso** (tripé ou suporte), sem encostar a mão durante a gravação | Câmera parada = mesma linha de contagem o vídeo todo |
| Bateria e espaço | Carregador ligado; pelo menos 3 GB livres | 10 min a 1080p ocupam de 0,5 a 1 GB |
| Enquadramento | Celular **mais alto, acima da grade** da varanda, com os dois lados da rua visíveis | No vídeo de teste a grade cobriu a ciclofaixa (ciclistas visíveis só da cintura para cima) e a calçada próxima não apareceu. Se o humano vê algo que a câmera não vê, a diferença vira um erro "falso" do YOLO |

Mantenha o **mesmo lugar e enquadramento** nas 4 gravações. Se o celular sair do lugar, a linha de contagem precisa ser redefinida para aquele vídeo.

## 2. Linha de contagem (referência física)

- Escolha uma referência que você enxerga **da janela** e que aparece **no vídeo**. Sugestão pela foto da cena: **a quina onde termina o muro azul da escola**, que fica longe da faixa de pedestres, do poste da direita e dos carros estacionados.
- A linha imaginária vai **dessa quina, em linha reta, até a calçada do outro lado**, atravessando as duas faixas e a ciclofaixa.
- No computador, a mesma linha é desenhada com `scripts/01_definir_linha.py`.

## 3. O que conta

| Classe | Conta | Não conta / observação |
|---|---|---|
| Carro | carros de passeio, SUVs, **picapes** e **vans** | carros estacionados (não cruzam a linha); carro manobrando para estacionar cujo meio não passa a linha |
| Moto | motos, motonetas, scooters | o condutor e o garupa **não** contam como pessoa |
| Bicicleta | bicicletas, inclusive empurradas | o ciclista não conta como pessoa |
| Pessoa | pedestres que cruzam a linha **ao longo da calçada ou da rua** | quem atravessa a rua **na faixa de pedestres**, sem cruzar a linha, não conta |
| Cachorro | qualquer cachorro (com ou sem dono) | gatos e outros animais não contam |
| Ônibus | ônibus e micro-ônibus | |
| Caminhão | caminhões, caminhões-baú, VUCs, betoneiras | picapes e vans são carro |
| (reboque) | **não conta**: faz parte do veículo que o puxa | o YOLO costuma contar a carretinha como um 2º veículo (visto no vídeo de teste) |

> **Por que picape é carro?** É como uma pessoa naturalmente classificaria. O YOLO, porém, costuma chamar picape de *truck* (caminhão). Essa confusão é justamente um dos erros que o trabalho quer medir ("objetos parecidos").

A rua é de **mão única** (veículos motorizados num só sentido); **bicicletas andam nos dois sentidos** (ciclofaixa). Contam-se os dois sentidos.

Regras gerais:
- Cada objeto conta **uma vez**, no momento em que **o meio dele** passa pela linha.
- Contam os **dois sentidos**.
- Se um objeto cruza, volta e cruza de novo, conta **uma vez**.

## 4. Gravação + contagem manual (ao vivo)

1. Posicione o celular e comece a **gravar**.
2. Espere uns 3 s. Dispare o **cronômetro** (outro celular ou relógio) e, **no mesmo instante**, diga em voz alta **"começou!"**. Esse som fica no vídeo e permite sincronizar depois.
3. Conte no papel (ficha em [`ficha_contagem_papel.md`](ficha_contagem_papel.md)) com um tracinho (|||| ) por objeto, em cada classe. **Só o total dos 10 minutos** é registrado (decisão do experimento, ver seção 6).
4. Conte por **10 minutos completos**. Depois diga **"fim"** e deixe o vídeo rodar mais uns 10 s antes de parar.
5. Some os tracinhos e anote o total de cada classe. Anote também data, hora de início, tempo (sol, nublado, chuva) e qualquer acontecimento (ex.: "lá pelo min 6: caminhão parou na frente por 30 s").
6. Mais tarde, no vídeo, encontre o segundo exato do "começou!" e anote em `config/videos.csv`, coluna `inicio_contagem_s`. Use vírgula ou ponto, tanto faz.

**Durante a contagem:** não pause, não volte e não use o celular para outra coisa. As distrações naturais fazem parte do que está sendo medido. Mas anote se algo atrapalhar (alguém falou com você, por exemplo).

## 5. Horários

| Vídeo | Horário | Observação |
|---|---|---|
| `v1_meio_dia` | 12h10–12h20 | sol a pino, sombras curtas |
| `v2_tarde_1` | 15h07–15h17 | tarde |
| `v3_tarde_2` | 17h12–17h22 | fim de tarde |
| `v4_18h` | 18h04–18h14 | já escuro: avaliação com pouca luz |

Gravações feitas em **20/10/2026 (terça-feira)**, todas no mesmo dia útil.

## 6. Formato da contagem manual e digitação

**Decisão do experimento (2026-10-20): a contagem manual registra só o TOTAL de cada classe nos 10 minutos.**
É mais simples de fazer ao vivo. Em troca:
- o erro humano é medido no vídeo inteiro, então o **gabarito cobre os 10 minutos** (seção 7);
- **não há análise de cansaço do humano**, porque não se sabe em que momento ele errou;
- o gabarito também foi registrado só como total, então a comparação é **por classe nos 10 minutos**
  (sem análise por minuto). Entre horários, só a comparação **dia × noite** (12h10 × 18h04, pessoa e moto).

O código aceita três formatos (coluna `minuto` do CSV), caso alguém queira repetir o experimento com mais detalhe:

| Formato | Exemplo de linhas | Erro humano contra o gabarito | Análise de cansaço |
|---|---|---|---|
| Por minuto | `1`, `2`, …, `10` | nos minutos do gabarito | sim, minuto a minuto |
| Por blocos | `1-3`, `4-7`, `8-10` | nos blocos 1-3 e 8-10 (que o gabarito cobre) | sim: começo (1-3) × fim (8-10) |
| Só o total | `total` | **só se o gabarito cobrir o vídeo inteiro** | **não** |

Passe a ficha para `dados/manual/<id_do_video>.csv`, copiando o `MODELO_contagem_manual.csv` (já vem com a linha `total`). Sempre números (0 se não passou nenhum):

```
minuto;carro;moto;bicicleta;pessoa;cachorro;onibus;caminhao;observacoes
total;198;61;7;12;1;4;3;
```
(números ilustrativos)

## 7. Gabarito

Com o vídeo já no computador e a linha definida:

```
python scripts/03_gabarito.py --video v1_meio_dia
```

- Revise com calma os **10 minutos inteiros** (a ferramenta começa no "começou!" e para no fim da janela). Dá para parar e continuar depois: ela salva a cada tecla e retoma de onde parou.
- Use velocidade 0,5× e **pause** quando houver muitos objetos juntos. Volte (`a`) sempre que tiver dúvida.
- Aperte a tecla da classe quando **o meio do objeto** passar pela linha amarela. Errou? `z` desfaz.
- **Faça o gabarito alguns dias depois** da contagem ao vivo, se possível, para não "lembrar" da contagem do papel.
- **Quem fez:** o gabarito dos 4 vídeos foi feito por **Gabriela Passos**, que não participou da filmagem nem da contagem ao vivo.
  Uma recontagem anterior do autor da contagem ao vivo chegou aos mesmos totais por classe.

## 8. Vídeo de teste (calibração)

Antes dos 4 vídeos, grave **2 a 3 minutos** (`teste.mp4`) da mesma janela e conte à mão. Ele serve para:
- conferir enquadramento, grade, luz e se a linha está num bom lugar;
- ajustar os limiares (`config/config.yaml`), por exemplo o filtro de pessoa montada;
- medir o tempo real de processamento.

O vídeo de teste está marcado como `usar_na_analise = nao` e **nunca** entra nos resultados.
