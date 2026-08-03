# AI Engineering bookmarks

Os pontos deste codigo que ensinam alguma coisa que se transfere direto para AI
Engineering. Cada um existe como comentario `# [AI-ENG:<slug>]` na linha exata onde a
decisao acontece — este arquivo e so o indice.

A regra que os governa esta no `CLAUDE.md` secao 9: o comentario diz **a ponte**, nao o
que a linha faz. "Faz parse de YAML" nao vale nada; "dado declarativo externo precisa ser
validado, igual a structured output de LLM" e o ponto.

Ao final de cada fase sai tambem uma aula em HTML em `D:\Projetos6\_AI_Eng_Aulas`
cobrindo estes mesmos conceitos com teoria, diagrama e exercicio.

**12 bookmarks.** Ordenados por arquivo.

| Slug | Onde | Conceito | A ponte com AI Engineering |
|---|---|---|---|
| `blocklist-vs-allowlist` | [src/codequest/engine/guard.py:62](src/codequest/engine/guard.py#L62) | Blocklist x allowlist | Enumerar o proibido perde para quem escolhe de um conjunto infinito. Allowlist inverte a assimetria. Vale igual para prompt injection. |
| `static-analysis` | [src/codequest/engine/guard.py:101](src/codequest/engine/guard.py#L101) | Analise estatica | Inspecionar a arvore antes de executar. E o que voce faz ao validar a tool call proposta pelo modelo antes de despachar. |
| `resource-limits` | [src/codequest/engine/harness.py:39](src/codequest/engine/harness.py#L39) | Limites de recurso | Teto de CPU e memoria imposto pelo proprio executor. Equivale a orcamento de token e wall-clock de um agente: so vale o limite que o executor aplica em si mesmo. |
| `untrusted-parsing` | [src/codequest/engine/loader.py:60](src/codequest/engine/loader.py#L60) | Desserializacao segura | safe_load recusa construir objetos arbitrarios. Nunca entregue saida de modelo a um desserializador que pode instanciar classes. |
| `schema-validation` | [src/codequest/engine/loader.py:94](src/codequest/engine/loader.py#L94) | Validacao de schema | Dado declarativo externo parece o contrato e silenciosamente nao e. Mesma coisa que structured output de LLM. |
| `protocol-abstraction` | [src/codequest/engine/runners/base.py:79](src/codequest/engine/runners/base.py#L79) | Abstracao por protocolo | Depender de uma forma e nao de uma classe. E a alavanca que evita soldar a aplicacao a um unico provider de LLM. |
| `sandboxing` | [src/codequest/engine/runners/python.py:64](src/codequest/engine/runners/python.py#L64) | Sandbox de execucao | Executar codigo nao confiavel num processo matavel e o mesmo problema que isolar tool calls de um agente ou uma sessao de code interpreter. |
| `channel-separation` | [src/codequest/engine/runners/python.py:222](src/codequest/engine/runners/python.py#L222) | Separacao de canal | O resultado viaja num canal que o codigo do jogador nao alcanca. Mesmo problema de extrair JSON de uma resposta que tambem tem prosa do modelo. |
| `failure-taxonomy` | [src/codequest/models/verdict.py:16](src/codequest/models/verdict.py#L16) | Taxonomia de falha | Um eval que so diz certo/errado nao distingue recusa de alucinacao de tool call malformada, entao nao diz o que corrigir. |
| `orchestration-gates` | [src/codequest/services/game_session.py:65](src/codequest/services/game_session.py#L65) | Portoes de orquestracao | Cadeia onde cada etapa pode parar com um motivo tipado. E a forma de uma cadeia de guardrails em volta de um modelo. |
| `idempotency` | [src/codequest/services/progress_service.py:107](src/codequest/services/progress_service.py#L107) | Idempotencia | Efeito aplicado uma vez so, decidido por estado persistido. Um passo de agente que faz retry nao pode cobrar o cartao duas vezes. |
| `sql-injection` | [src/codequest/storage/repositories.py:10](src/codequest/storage/repositories.py#L10) | Injecao de SQL | Todo valor entra como placeholder. Mesma classe de bug de documento recuperado virando parte do prompt ou argumento virando parte de um shell command. |

## Por onde comecar

Se for ler so tres, leia nesta ordem:

1. **`sandboxing`** e **`resource-limits`** — juntos formam o assunto mais valioso do
   repositorio para quem vai construir agentes que executam codigo.
2. **`failure-taxonomy`** — e literalmente design de eval harness, so que aplicado a
   codigo de jogador em vez de saida de modelo.
3. **`idempotency`** — o problema que aparece na primeira vez que um pipeline de agente
   faz retry de um passo com efeito colateral.

## Manutencao

Os numeros de linha envelhecem. Quando um bookmark se mover, regenere este indice —
uma linha errada e pior que nenhuma, porque manda o leitor para o lugar errado com
confianca. O teste `tests/unit/test_bookmarks.py` falha quando o indice e o codigo
divergem.
