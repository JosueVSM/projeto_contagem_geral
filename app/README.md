# app/

Painel interativo (Streamlit) para explorar os resultados no navegador.

```bash
<pasta do ambiente virtual>\Scripts\activate    (ex.: C:\Users\<voce>\venvs\visao_contagem)
streamlit run app/painel.py
```

O painel abre em `http://localhost:8501`.

| Arquivo | O que faz |
|---|---|
| `painel.py` | Lê as tabelas de `resultados/tabelas/` (ou de `resultados/calibracao/tabelas/`), as saídas de `resultados/yolo/` e os PNGs de `resultados/graficos/`, e mostra tudo em abas |

## Abas
| Aba | Conteúdo |
|---|---|
| Erro por classe | Para a soma dos 4 vídeos ou para cada vídeo: total e erro de cada contagem (manual, YOLO-n, YOLO-l), tabela por classe com contagem, erro e erro %, gráfico do erro por classe e, na soma, o WAPE (erro sem compensação entre vídeos) |
| Dia × noite | 12h10 × 18h04, só pessoa e moto: erro de cada contagem e confiança média do YOLO (tabela `T04` + gráfico `G05`) |
| Vídeos (demonstração) | Clipes de 30 s (início e fim) de cada vídeo com nano e large contando lado a lado (gerados por `scripts/06_videos_demo.py`) |
| Velocidade dos modelos | Quadros por segundo e ms por quadro de cada modelo |
| Gráficos (PNG) | Galeria dos gráficos gerados pelo passo 5 |

Por decisão do trabalho, o painel mostra o **erro por classe** (sem análise por minuto) e, na aba **Dia × noite**, a comparação 12h × 18h de pessoa e moto.

## Importante
- O painel **só lê** o que os scripts já gravaram; não calcula nem inventa nada. Depois de rodar de novo o passo 4 ou o 5, basta atualizar a página (F5): ele percebe sozinho que as tabelas mudaram.
- O gráfico tem dica ao passar o mouse; os valores exatos estão na tabela logo acima dele.
- Os vídeos originais não aparecem no painel. Os clipes de demonstração são lidos de `~/dados_visao/videos_demo/` (fora do repositório) e só aparecem no seu computador.
