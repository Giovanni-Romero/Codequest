# AI Engineering bookmarks

Os pontos deste codigo que ensinam alguma coisa que se transfere direto para AI
Engineering. Cada um existe como comentario `# [AI-ENG:<slug>]` na linha exata onde a
decisao acontece — este arquivo e so o indice.

A regra que os governa esta no `CLAUDE.md` secao 9: o comentario diz **a ponte**, nao o
que a linha faz. "Faz parse de YAML" nao vale nada; "dado declarativo externo precisa ser
validado, igual a structured output de LLM" e o ponto.

Ao final de cada fase sai tambem uma aula em HTML cobrindo estes mesmos conceitos com
teoria, diagrama e exercicio. Ela e escrita em `D:\Projetos\2026\_AI_Eng_Aulas` e
espelhada em [`aulas/`](aulas/), que tem o indice e diz quais slugs cada aula cobre —
e quais quatro ainda nao aparecem em aula nenhuma.

**21 bookmarks.** Ordenados por arquivo: primeiro o codigo, depois as duas pontes que
vivem numa missao.

Uma ponte mora numa missao quando o argumento e da *missao* e nao de uma linha de motor —
`concurrency-cost` e o que a missao 8 da Ilha 11 defende, nao algo que o `harness.py`
faz. Elas sao verificadas pelo mesmo script e pelo mesmo teste que as de codigo, porque
uma citacao que ninguem confere envelhece calada. Os espelhos `-pt` carregam o mesmo
comentario e nao sao indexados, senao o alvo ficaria pulando de idioma.

| Slug | Onde | Conceito | A ponte com AI Engineering |
|---|---|---|---|
| `frozen-paths` | [src/codequest/__main__.py:324](src/codequest/__main__.py#L324) | Caminhos sob empacotamento | Um build PyInstaller nao tem `__file__` real nem um python.exe separado pra invocar — so `sys.executable`, que dentro do bundle e o proprio app. "De onde estou rodando" e "de onde fui importado" param de ser a mesma pergunta assim que o codigo sai do proprio repositorio, e um agente empacotado pra distribuicao bate na mesma parede. |
| `blocklist-vs-allowlist` | [src/codequest/engine/guard.py:62](src/codequest/engine/guard.py#L62) | Blocklist x allowlist | Enumerar o proibido perde para quem escolhe de um conjunto infinito. Allowlist inverte a assimetria. Vale igual para prompt injection. |
| `static-analysis` | [src/codequest/engine/guard.py:101](src/codequest/engine/guard.py#L101) | Analise estatica | Inspecionar a arvore antes de executar. E o que voce faz ao validar a tool call proposta pelo modelo antes de despachar. |
| `resource-limits` | [src/codequest/engine/harness.py:40](src/codequest/engine/harness.py#L40) | Limites de recurso | Teto de CPU e memoria imposto pelo proprio executor. Equivale a orcamento de token e wall-clock de um agente: so vale o limite que o executor aplica em si mesmo. |
| `deferred-results` | [src/codequest/engine/harness.py:135](src/codequest/engine/harness.py#L135) | Resultado adiado x resultado | O que a funcao devolveu nao e a resposta: e a promessa de uma. Serializar antes de resolver produz `<coroutine object ... at 0x...>`, um endereco novo a cada execucao que *parece* dado. O executor de tool calls de um agente tem a mesma disciplina — aguardar primeiro, serializar depois, reportar por ultimo — e resolver a promessa dentro do mesmo tratamento de erro que cobre a chamada comum e o que impede a excecao de dentro dela de escapar sem rastro. |
| `untrusted-parsing` | [src/codequest/engine/loader.py:89](src/codequest/engine/loader.py#L89) | Desserializacao segura | safe_load recusa construir objetos arbitrarios. Nunca entregue saida de modelo a um desserializador que pode instanciar classes. |
| `path-traversal` | [src/codequest/engine/loader.py:65](src/codequest/engine/loader.py#L65) | Travessia de caminho | Um nome que chega como dado declarativo e vira caminho de escrita e o mesmo bug de um agente que pega o filename direto da tool call do modelo. A defesa e **rejeitar** o nome inteiro quando ele nao e um segmento simples, nunca limpar a string: sanear convida a corrida armamentista (tirar `"../"` de `"....//....//etc"` **produz** `"../../etc"`), rejeitar encerra. |
| `schema-validation` | [src/codequest/engine/loader.py:131](src/codequest/engine/loader.py#L131) | Validacao de schema | Dado declarativo externo parece o contrato e silenciosamente nao e. Mesma coisa que structured output de LLM. |
| `protocol-abstraction` | [src/codequest/engine/runners/base.py:84](src/codequest/engine/runners/base.py#L84) | Abstracao por protocolo | Depender de uma forma e nao de uma classe. E a alavanca que evita soldar a aplicacao a um unico provider de LLM. |
| `sandboxing` | [src/codequest/engine/runners/python.py:65](src/codequest/engine/runners/python.py#L65) | Sandbox de execucao | Executar codigo nao confiavel num processo matavel e o mesmo problema que isolar tool calls de um agente ou uma sessao de code interpreter. |
| `channel-separation` | [src/codequest/engine/runners/python.py:268](src/codequest/engine/runners/python.py#L268) | Separacao de canal | O resultado viaja num canal que o codigo do jogador nao alcanca. Mesmo problema de extrair JSON de uma resposta que tambem tem prosa do modelo. |
| `graceful-degradation` | [src/codequest/mentor/client.py:3](src/codequest/mentor/client.py#L3) | Degradacao graciosa | Falha de LLM e ramo normal, nao excecao. Modelo fora do ar, lento ou ausente sao Terca-feira: decidir o que o usuario ve em cada estado faz parte de desenhar a feature. |
| `guardrails` | [src/codequest/mentor/policy.py:12](src/codequest/mentor/policy.py#L12) | Guardrails em duas camadas | Prompt desloca probabilidade, filtro decide. O que voce precisa garantir exige codigo antes ou depois do modelo; so o que voce prefere pode viver no prompt. |
| `context-assembly` | [src/codequest/mentor/prompts.py:6](src/codequest/mentor/prompts.py#L6) | Montagem de contexto | Mais contexto nao e melhor contexto. Cada campo precisa justificar o lugar, e o que fica de fora e decidido na montagem, nao filtrado depois. |
| `failure-taxonomy` | [src/codequest/models/verdict.py:16](src/codequest/models/verdict.py#L16) | Taxonomia de falha | Um eval que so diz certo/errado nao distingue recusa de alucinacao de tool call malformada, entao nao diz o que corrigir. |
| `orchestration-gates` | [src/codequest/services/game_session.py:74](src/codequest/services/game_session.py#L74) | Portoes de orquestracao | Cadeia onde cada etapa pode parar com um motivo tipado. E a forma de uma cadeia de guardrails em volta de um modelo. |
| `shared-state` | [src/codequest/services/progress_service.py:63](src/codequest/services/progress_service.py#L63) | Estado compartilhado entre threads | A UI roda a tentativa numa worker thread enquanto a principal ainda pode revelar dica. A biblioteca ser thread-safe protege statements isolados, nao a SUA transacao de varios passos. Mesma armadilha na primeira vez que um agente dispara tool calls em paralelo. |
| `idempotency` | [src/codequest/services/progress_service.py:126](src/codequest/services/progress_service.py#L126) | Idempotencia | Efeito aplicado uma vez so, decidido por estado persistido. Um passo de agente que faz retry nao pode cobrar o cartao duas vezes. |
| `sql-injection` | [src/codequest/storage/repositories.py:10](src/codequest/storage/repositories.py#L10) | Injecao de SQL | Todo valor entra como placeholder. Mesma classe de bug de documento recuperado virando parte do prompt ou argumento virando parte de um shell command. |
| `debugging-methodology` | [content/tracks/python/locales/en/islands/06-debugging/missions/04-halve-the-search.yaml:8](content/tracks/python/locales/en/islands/06-debugging/missions/04-halve-the-search.yaml#L8) | Bisseccao e hipotese falseavel | Cortar ao meio o intervalo suspeito antes de mudar qualquer coisa e a mesma disciplina de um agente depurando as proprias tool calls. A pergunta nunca e "o que quebrou" e sim "qual metade ainda e confiavel", e a resposta tem de ser uma sobre a qual voce poderia estar errado. A versao humana vem primeiro. |
| `concurrency-cost` | [content/tracks/python/locales/en/islands/11-async-and-concurrency/missions/08-the-slower-fleet.yaml:16](content/tracks/python/locales/en/islands/11-async-and-concurrency/missions/08-the-slower-fleet.yaml#L16) | O custo da concorrencia | Um agente que dispara dez tool calls em paralelo paga a mesma troca: sobrepoe a espera, nunca o trabalho, e paga um custo fixo por ramo. O reflexo de paralelizar um lote de chamadas de LLM de vinte milissegundos cada e o mesmo reflexo que a missao recusa, em outra escala. |

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
