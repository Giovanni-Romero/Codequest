# Aulas — material de estudo

Oito aulas em HTML, uma por fase concluída do projeto. Cada uma pega o que foi construído naquela
fase e ensina o conceito de AI Engineering que ele carrega: analogia primeiro, teoria
depois, o **código real que shippou** anotado, e um exercício com a resposta escondida
atrás de um `<details>`.

A regra que as governa está no `CLAUDE.md` §9.2. Uma fase não fecha sem a sua aula.

## Duas coisas para saber antes de clicar

**Estão em português (pt-BR).** É a única exceção deliberada à regra do `CLAUDE.md` §0 de
que todo arquivo deste repositório é escrito em inglês. A exceção existe porque estas são
material de estudo, e traduzir custaria exatamente a clareza que justifica escrevê-las.

**O GitHub não renderiza HTML** — clicar num arquivo aqui mostra o código-fonte, não a
página. Para ler formatado:

- baixe o arquivo e abra com duplo clique (cada aula é autocontida: CSS inline, SVG
  inline, sem CDN, sem fonte remota — funciona offline), ou
- use um proxy de preview, colando a URL do arquivo em `htmlpreview.github.io`.

Estes arquivos são **cópias**. A fonte de verdade continua em
`D:\Projetos\2026\_AI_Eng_Aulas\`, e é lá que uma aula nova é escrita antes de ser
espelhada para cá.

## As aulas

| # | Aula | Sobre o quê | Bookmarks que cobre |
|---|---|---|---|
| 1 | [Motor de Execução](Fase1-Motor-de-Execucao.html) | Rodar código não confiável num processo que se pode matar | `sandboxing`, `resource-limits`, `blocklist-vs-allowlist`, `channel-separation`, `failure-taxonomy`, `protocol-abstraction` |
| 2 | [Persistência e Progressão](Fase2-Persistencia-e-Progressao.html) | SQLite, transações, e por que um retry não pode cobrar duas vezes | `sql-injection`, `idempotency` |
| 3 | [Currículo e Conteúdo como Dado](Fase3-Curriculo-e-Conteudo-como-Dado.html) | YAML declarativo validado antes do uso, igual a structured output de LLM | `schema-validation`, `failure-taxonomy` |
| 4 | [Interface e Estado Reativo](Fase4-Interface-e-Estado-Reativo.html) | A UI numa thread, o trabalho em outra, e o que isso quebra | `shared-state` |
| 5 | [Integração com LLM](Fase5-Integracao-com-LLM.html) | Prompt desloca probabilidade, filtro decide | `guardrails`, `context-assembly`, `graceful-degradation` |
| 6 | [Arquivos no Sandbox](Fase6-Arquivos-no-Sandbox.html) | Path traversal, e por que rejeitar ganha de sanear | `path-traversal`, `schema-validation`, `sandboxing`, `blocklist-vs-allowlist` |
| 7 | [Currículo como Eval Design](Fase7-Curriculo-como-Eval-Design.html) | Projetar missões é projetar um eval harness | `deferred-results`, `debugging-methodology`, `concurrency-cost`, `failure-taxonomy` |
| 8 | [Engenharia de IA de Ponta a Ponta](Fase8-Engenharia-de-IA-de-Ponta-a-Ponta.html) | Certificar um sistema por contratos, evidências e gates | `orchestration-gates`, `schema-validation`, `failure-taxonomy`, `guardrails`, `graceful-degradation`, `idempotency` |

O índice completo dos bookmarks, com `arquivo:linha` verificado por teste, está em
[`../curriculum/ai-engineering/bookmarks.md`](../curriculum/ai-engineering/bookmarks.md).

## O que as aulas ainda não cobrem

Levantado ao montar este índice, e registrado aqui em vez de ficar implícito. Quatro dos
21 bookmarks não aparecem em aula nenhuma:

- `frozen-paths` — "de onde estou rodando" e "de onde fui importado" param de ser a mesma
  pergunta assim que o código sai do repositório. Veio da Fase 5.2, o build portátil, que
  não teve aula própria.
- `static-analysis` — inspecionar a árvore antes de executar. Está no guard, e a Fase 1
  cobriu o guard pelo lado da blocklist, não pelo da AST.
- `untrusted-parsing` — `safe_load` recusa construir objetos arbitrários.
- `orchestration-gates` — uma cadeia onde cada etapa pode parar com um motivo tipado.

Não é dívida urgente: os quatro têm a ponte escrita no índice de bookmarks, que é onde a
explicação curta mora. É uma lacuna de *aula*, não de registro, e o lugar natural para
fechá-la é a próxima fase que tocar nesses arquivos.
