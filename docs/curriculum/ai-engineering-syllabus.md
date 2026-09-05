# AI Engineering Syllabus

The concept map for the AI Engineering track. Missions are written from this document,
never the other way around.

The player is expected to know intermediate Python: functions, collections, exceptions,
files, classes, and automated tests. The track teaches AI systems, not Python syntax.

## Design rules

- Islands 1 to 8 teach durable concepts without requiring a model, network, or framework.
- Islands 9 to 15 apply those concepts through real frameworks installed as optional extras.
- Graded missions are deterministic and run offline. Model-backed labs are optional and do
  not gate progression.
- One mission introduces at most one concept. Every concept is reinforced at least twice.
- Framework versions are selected and tested when their island is authored, not guessed now.
- Only shipped islands appear in `track.yaml`; this syllabus is the longer roadmap.

For Islands 2 to 15, concepts are introduced in missions 1 to 4 in the order listed.
Mission 5 reinforces concepts 1 and 2, mission 6 reinforces 2 and 3, mission 7 reinforces
3 and 4, and mission 8 combines all four. This gives every concept at least two later uses
and creates a sawtooth curve with consolidation after each introduction.

## Track map

| # | Island | Band | Outcome |
|---:|---|---|---|
| 1 | Documents into Context | moderate | Turn raw text into traceable, bounded chunks |
| 2 | Prompt Contracts | moderate | Build explicit prompts with controlled context and trust boundaries |
| 3 | Retrieval | moderate | Rank useful context with transparent relevance rules |
| 4 | RAG | moderate | Assemble answers from retrieved evidence and cite their sources |
| 5 | Structured Outputs | moderate | Turn model-shaped text into validated application data |
| 6 | Evals | moderate | Measure capabilities and diagnose failure classes |
| 7 | Tools and Agents | moderate | Orchestrate tools without duplicating effects or losing state |
| 8 | Production AI | moderate | Operate AI features under latency, cost, safety, and outage constraints |
| 9 | PyTorch Foundations | challenging | Build and train a small neural network on CPU |
| 10 | Hugging Face Transformers | challenging | Tokenize and run transformer inference with local assets |
| 11 | LangChain | expert | Compose prompts, retrievers, tools, and agent loops |
| 12 | LangGraph | expert | Build durable stateful workflows with explicit transitions |
| 13 | LlamaIndex | expert | Build data ingestion and query workflows over documents |
| 14 | PydanticAI | expert | Build typed, testable, provider-independent agents |
| 15 | DSPy | expert | Optimize LM programs against explicit metrics |

The dependency spine is:

`chunking -> context assembly -> retrieval -> RAG -> structured output -> evals -> agents -> production`

The framework block applies the spine rather than replacing it.

---

## Island 1 — Documents into Context

**Theme:** preparing evidence before a model sees it

**Band:** moderate

**Planned missions:** 8

### Mission map

| # | Slug | Introduces | Reinforces | Note |
|---:|---|---|---|---|
| 1 | `chunk-by-words` | `fixed-window-chunking` | — | Deterministic first slice |
| 2 | `nothing-lost` | `chunk-invariants` | `fixed-window-chunking` | Prove coverage and order |
| 3 | `overlap-the-boundary` | `chunk-overlap` | `fixed-window-chunking`, `chunk-invariants` | Preserve boundary context |
| 4 | `trace-the-source` | `chunk-metadata` | `chunk-invariants` | Carry source identity with text |
| 5 | `keep-the-paragraph` | `semantic-boundaries` | `fixed-window-chunking`, `chunk-metadata` | Prefer natural boundaries |
| 6 | `budget-the-context` | `context-budget` | `chunk-overlap`, `chunk-metadata` | Select within a hard budget |
| 7 | `inspect-the-chunks` | `chunk-quality` | all previous concepts | **Relief:** diagnose, do not invent |
| 8 | `prepare-the-corpus` | — | all seven concepts | Closing pipeline |

### fixed-window-chunking
- **prereqs:** intermediate Python strings, lists, loops, and slicing
- **objective:** split an ordered sequence into bounded consecutive groups
- **misconceptions:** chunking is summarization; a character limit and a word limit are interchangeable
- **mastery:** produces complete ordered chunks for empty, exact, and remainder cases
- **reinforced in:** missions 2, 3, 5, and 8

### chunk-invariants
- **prereqs:** fixed-window-chunking
- **objective:** verify that chunking loses, duplicates, and reorders nothing
- **misconceptions:** checking chunk sizes proves correctness; overlap is always duplication
- **mastery:** writes checks for coverage, order, empties, and bounds
- **reinforced in:** missions 3, 7, and 8

### chunk-overlap
- **prereqs:** fixed-window-chunking, chunk-invariants
- **objective:** add controlled overlap without breaking termination or order
- **misconceptions:** more overlap is always better; overlap may equal or exceed chunk size
- **mastery:** predicts chunk count and shared boundaries for a given stride
- **reinforced in:** missions 6, 7, and 8

### chunk-metadata
- **prereqs:** chunk-invariants
- **objective:** attach stable source and position metadata to every chunk
- **misconceptions:** text alone is enough for citations; list position is a durable identifier
- **mastery:** traces every returned chunk back to its source and ordinal
- **reinforced in:** missions 5, 6, 7, and 8

### semantic-boundaries
- **prereqs:** fixed-window-chunking, chunk-metadata
- **objective:** prefer paragraph boundaries while respecting a hard maximum
- **misconceptions:** semantic chunking removes the need for limits; every paragraph fits
- **mastery:** handles normal and oversized paragraphs without losing provenance
- **reinforced in:** missions 7 and 8, and Island 4

### context-budget
- **prereqs:** chunk-overlap, chunk-metadata
- **objective:** select chunks without exceeding a declared context budget
- **misconceptions:** model context is unlimited; filling every token improves the answer
- **mastery:** chooses an ordered subset whose total cost stays within budget
- **reinforced in:** missions 7 and 8, and Island 2

### chunk-quality
- **prereqs:** all earlier Island 1 concepts
- **objective:** detect empty, oversized, duplicated, or untraceable chunks
- **misconceptions:** successful execution means useful chunks; one example represents a corpus
- **mastery:** classifies deliberately flawed chunk sets by failure type
- **reinforced in:** mission 8 and Islands 4 and 6

---

## Island 2 — Prompt Contracts

### instruction-hierarchy
- **prereqs:** context-budget
- **objective:** separate system rules, task instructions, examples, and user data
- **misconceptions:** every text segment has equal authority; ordering alone creates security
- **mastery:** assigns prompt content to the correct authority layer

### prompt-templates
- **prereqs:** instruction-hierarchy
- **objective:** render declared variables without accidental interpolation or omission
- **misconceptions:** string concatenation is a contract; braces in user data are instructions
- **mastery:** renders a template and rejects missing variables predictably

### context-assembly
- **prereqs:** prompt-templates, context-budget
- **objective:** include only context that earns its place in the request
- **misconceptions:** more context is always better; filtering after generation is equivalent
- **mastery:** assembles sections in a stable order under a budget

### trust-boundaries
- **prereqs:** instruction-hierarchy, context-assembly
- **objective:** mark retrieved and user-controlled text as untrusted data
- **misconceptions:** delimiters guarantee safety; retrieved documents are trusted instructions
- **mastery:** preserves data while preventing it from becoming an application rule

---

## Island 3 — Retrieval

### sparse-representation
- **prereqs:** fixed-window-chunking
- **objective:** represent text with deterministic term features
- **misconceptions:** embeddings are required for all retrieval; counts and presence are identical
- **mastery:** builds a reproducible feature vector from text

### similarity-scoring
- **prereqs:** sparse-representation
- **objective:** compute and interpret similarity between query and document vectors
- **misconceptions:** similarity is probability; larger documents are automatically more relevant
- **mastery:** ranks hand-checkable vectors and explains ties

### top-k-ranking
- **prereqs:** similarity-scoring
- **objective:** return the best `k` results with stable tie-breaking
- **misconceptions:** sorting direction does not matter; `k` always fits the corpus
- **mastery:** handles empty corpora, ties, zero, and oversized `k`

### relevance-thresholds
- **prereqs:** top-k-ranking
- **objective:** refuse results below an explicit relevance floor
- **misconceptions:** top result means relevant result; one threshold works for every task
- **mastery:** separates ranking from acceptance and reports no-match cases

---

## Island 4 — RAG

### ingestion-pipeline
- **prereqs:** chunk-metadata, top-k-ranking
- **objective:** transform source documents into retrievable records through explicit stages
- **misconceptions:** ingestion happens once without failure; transformed data needs no provenance
- **mastery:** reports which stage produced or rejected each record

### retrieval-generation-separation
- **prereqs:** ingestion-pipeline, context-assembly
- **objective:** keep evidence selection separate from answer generation
- **misconceptions:** generation can repair bad retrieval; one combined function is easier to debug
- **mastery:** attributes a failure to retrieval or generation using intermediate data

### citation-provenance
- **prereqs:** retrieval-generation-separation, chunk-metadata
- **objective:** connect answer claims to stable source identifiers
- **misconceptions:** a URL anywhere in the answer is a citation; generated citations are evidence
- **mastery:** rejects citations not backed by retrieved records

### abstention-policy
- **prereqs:** relevance-thresholds, citation-provenance
- **objective:** return a defined no-answer result when evidence is insufficient
- **misconceptions:** an answer is always more useful than abstention; confidence can be inferred from tone
- **mastery:** abstains on empty, conflicting, and below-threshold evidence

---

## Island 5 — Structured Outputs

### output-schema
- **prereqs:** prompt-templates
- **objective:** express required output fields, types, and allowed values explicitly
- **misconceptions:** JSON syntax proves semantic validity; optional and nullable are identical
- **mastery:** distinguishes valid structure from valid business data

### safe-output-parsing
- **prereqs:** output-schema, trust-boundaries
- **objective:** parse model-shaped text without executing it
- **misconceptions:** `eval` is acceptable for trusted models; extracting the first braces is robust
- **mastery:** rejects malformed input without side effects

### validation-retry
- **prereqs:** safe-output-parsing
- **objective:** retry only repairable validation failures under a fixed limit
- **misconceptions:** every failure deserves a retry; retries erase side effects
- **mastery:** stops on permanent failures and reports exhausted attempts

### failure-taxonomy
- **prereqs:** validation-retry
- **objective:** classify parse, schema, policy, provider, and timeout failures separately
- **misconceptions:** all failures are exceptions; one error message is enough for diagnosis
- **mastery:** maps representative failures to stable typed reasons

---

## Island 6 — Evals

### eval-datasets
- **prereqs:** failure-taxonomy
- **objective:** build representative cases with explicit inputs and expected properties
- **misconceptions:** production logs are automatically a balanced dataset; more rows mean more coverage
- **mastery:** identifies duplicated, missing, and overrepresented capability slices

### capability-metrics
- **prereqs:** eval-datasets
- **objective:** choose a metric that matches the capability being tested
- **misconceptions:** one aggregate score describes quality; exact match fits every task
- **mastery:** computes per-capability results and explains what each metric cannot measure

### adversarial-cases
- **prereqs:** capability-metrics, trust-boundaries
- **objective:** add cases that target shortcuts, malformed input, and hostile instructions
- **misconceptions:** edge cases are rare noise; safety can be inferred from happy paths
- **mastery:** writes a case that fails a shortcut while preserving legitimate behavior

### evaluation-leakage
- **prereqs:** eval-datasets, adversarial-cases
- **objective:** keep answers and test-only evidence out of the system being evaluated
- **misconceptions:** seeing the expected answer does not change the measurement; hidden cases are secrecy theater
- **mastery:** detects direct and indirect leakage in an evaluation pipeline

---

## Island 7 — Tools and Agents

### tool-contracts
- **prereqs:** output-schema, failure-taxonomy
- **objective:** define tool inputs, outputs, errors, and side effects as a contract
- **misconceptions:** a docstring is enough validation; every callable is safe to expose
- **mastery:** rejects malformed calls before a side effect occurs

### tool-routing
- **prereqs:** tool-contracts
- **objective:** select an allowed tool from task state and declared capabilities
- **misconceptions:** tool names explain all constraints; the model should see every tool
- **mastery:** routes valid cases and refuses ambiguous or unauthorized ones

### orchestration-gates
- **prereqs:** tool-routing, validation-retry
- **objective:** stop a workflow at typed validation, policy, execution, and persistence gates
- **misconceptions:** guardrails are one prompt; later validation compensates for earlier side effects
- **mastery:** identifies the earliest gate that must reject each failure

### idempotent-effects
- **prereqs:** orchestration-gates
- **objective:** make retried tool operations apply an external effect at most once
- **misconceptions:** retrying a request is harmless; timestamps are reliable idempotency keys
- **mastery:** deduplicates repeated calls while preserving distinct operations

---

## Island 8 — Production AI

### layered-guardrails
- **prereqs:** trust-boundaries, orchestration-gates
- **objective:** combine prompt guidance with deterministic input and output controls
- **misconceptions:** system prompts guarantee behavior; filters can recover leaked secrets
- **mastery:** assigns each guarantee to enforceable code rather than preference text

### observability-traces
- **prereqs:** failure-taxonomy, orchestration-gates
- **objective:** record stage, timing, inputs metadata, outputs metadata, and failure reason safely
- **misconceptions:** logs need full prompts; a final error is enough to reconstruct a run
- **mastery:** reconstructs a failed pipeline without exposing sensitive payloads

### latency-cost-budget
- **prereqs:** context-budget, observability-traces
- **objective:** enforce request, token, concurrency, and wall-clock budgets
- **misconceptions:** parallel calls are free; average latency describes tail behavior
- **mastery:** chooses a bounded execution plan and accounts for every call

### graceful-degradation
- **prereqs:** layered-guardrails, latency-cost-budget
- **objective:** define useful behavior for unavailable, slow, or rejected model calls
- **misconceptions:** provider failure is exceptional; fallback must imitate the full feature
- **mastery:** returns explicit offline, timeout, and degraded states without breaking core use

---

## Island 9 — PyTorch Foundations

### tensors-and-shapes
- **prereqs:** intermediate Python numeric operations
- **objective:** create tensors and predict operation shapes and dtypes
- **misconceptions:** tensors are plain nested lists; broadcasting always copies data
- **mastery:** diagnoses shape and dtype mismatches before training

### datasets-and-batches
- **prereqs:** tensors-and-shapes
- **objective:** expose examples through a dataset and assemble deterministic batches
- **misconceptions:** shuffling changes only speed; batch dimension is optional
- **mastery:** maps dataset examples to batch shapes without losing labels

### modules-and-forward
- **prereqs:** tensors-and-shapes, datasets-and-batches
- **objective:** compose `nn.Module` layers into a forward computation
- **misconceptions:** defining layers inside `forward` registers parameters; output values are probabilities
- **mastery:** builds a small model with stable registered parameters

### autograd-training-loop
- **prereqs:** modules-and-forward
- **objective:** run forward, loss, backward, optimizer, and gradient reset in order
- **misconceptions:** gradients reset automatically; lower training loss proves generalization
- **mastery:** trains a tiny CPU model and explains every state-changing step

---

## Island 10 — Hugging Face Transformers

### tokenizer-boundaries
- **prereqs:** tensors-and-shapes, fixed-window-chunking
- **objective:** map text to model tokens and back while respecting special tokens and limits
- **misconceptions:** tokens are words; character counts predict context usage
- **mastery:** explains truncation, padding, and attention masks for local examples

### model-config-and-weights
- **prereqs:** modules-and-forward, tokenizer-boundaries
- **objective:** distinguish architecture configuration from learned parameters
- **misconceptions:** loading a config loads a trained model; model name alone pins reproducibility
- **mastery:** constructs a tiny local model and reports config and parameter shapes

### inference-pipelines
- **prereqs:** model-config-and-weights
- **objective:** preprocess, infer, and postprocess through an explicit task pipeline
- **misconceptions:** pipeline output is raw model output; inference mode is only a speed option
- **mastery:** traces a local input through each inference stage

### fine-tuning-boundaries
- **prereqs:** inference-pipelines, autograd-training-loop
- **objective:** decide when prompting, retrieval, adapters, or weight updates fit the problem
- **misconceptions:** every domain problem needs fine-tuning; training data volume fixes bad labels
- **mastery:** selects an adaptation strategy and names its data and evaluation requirements

---

## Island 11 — LangChain

### langchain-runnables
- **prereqs:** retrieval-generation-separation, graceful-degradation
- **objective:** compose typed pipeline steps with explicit inputs and outputs
- **misconceptions:** chaining removes failure boundaries; framework composition replaces design
- **mastery:** traces values and errors through a deterministic runnable chain

### langchain-prompt-templates
- **prereqs:** langchain-runnables, prompt-templates
- **objective:** render framework prompt templates with declared variables
- **misconceptions:** framework templates make user data trusted; missing variables fail late
- **mastery:** validates and renders a template without a model call

### langchain-retrievers
- **prereqs:** langchain-runnables, top-k-ranking, citation-provenance
- **objective:** expose retrieval behind LangChain's retriever contract
- **misconceptions:** a vector store and a retriever are the same responsibility; top-k guarantees relevance
- **mastery:** swaps deterministic retrievers without changing the consuming chain

### langchain-tools-agents
- **prereqs:** langchain-runnables, tool-routing, idempotent-effects
- **objective:** expose safe tools and bound an agent loop with stop conditions
- **misconceptions:** agent reasoning authorizes side effects; framework defaults fit every risk level
- **mastery:** runs an offline fake-model agent and proves unauthorized tools never execute

---

## Island 12 — LangGraph

### langgraph-state
- **prereqs:** orchestration-gates, langchain-tools-agents
- **objective:** define explicit workflow state and controlled state updates
- **misconceptions:** message history is all state; nodes may mutate shared state arbitrarily
- **mastery:** predicts state after each deterministic graph step

### langgraph-nodes-edges
- **prereqs:** langgraph-state
- **objective:** model work as nodes connected by unconditional and conditional edges
- **misconceptions:** graph structure guarantees termination; every branch needs an LLM
- **mastery:** builds and terminates a deterministic conditional workflow

### langgraph-checkpoints
- **prereqs:** langgraph-nodes-edges, idempotent-effects
- **objective:** persist and resume workflow state without repeating completed effects
- **misconceptions:** checkpointing is logging; resume may safely replay every node
- **mastery:** resumes after interruption from the correct boundary

### langgraph-human-loop
- **prereqs:** langgraph-checkpoints, layered-guardrails
- **objective:** pause before sensitive work and resume from an explicit human decision
- **misconceptions:** approval is a chat message; rejection and cancellation are the same state
- **mastery:** models approve, reject, edit, and timeout paths deterministically

---

## Island 13 — LlamaIndex

### llamaindex-documents-nodes
- **prereqs:** ingestion-pipeline, chunk-metadata
- **objective:** map source documents into traceable LlamaIndex nodes
- **misconceptions:** nodes are arbitrary chunks; metadata survives without deliberate propagation
- **mastery:** traces every node back to its source document

### llamaindex-indexes
- **prereqs:** llamaindex-documents-nodes, similarity-scoring
- **objective:** build an in-memory index from deterministic local nodes
- **misconceptions:** an index is the source of truth; indexing guarantees good retrieval
- **mastery:** rebuilds the same local index and explains its stored representation

### llamaindex-query-engines
- **prereqs:** llamaindex-indexes, abstention-policy
- **objective:** query indexed evidence through a bounded retrieval interface
- **misconceptions:** query engines guarantee grounded answers; response text is enough without source nodes
- **mastery:** returns selected nodes and refuses below-threshold evidence

### llamaindex-workflows
- **prereqs:** llamaindex-query-engines, orchestration-gates
- **objective:** connect ingestion, retrieval, and response stages as explicit events
- **misconceptions:** event-driven means concurrent; workflow events need no schema
- **mastery:** diagnoses a failed stage from deterministic workflow events

---

## Island 14 — PydanticAI

### pydanticai-agent-contracts
- **prereqs:** tool-contracts, output-schema
- **objective:** declare an agent whose dependencies and result type are explicit
- **misconceptions:** type hints validate remote output by themselves; an agent is only a prompt
- **mastery:** builds a provider-independent agent contract with a fake model

### pydanticai-dependencies
- **prereqs:** pydanticai-agent-contracts
- **objective:** inject services and state without global variables
- **misconceptions:** dependency injection requires a web framework; test doubles belong in production code
- **mastery:** swaps deterministic dependencies in a test without changing agent logic

### pydanticai-tools
- **prereqs:** pydanticai-dependencies, tool-routing
- **objective:** expose context-aware tools with validated arguments
- **misconceptions:** dependency access authorizes every operation; validation handles business permissions
- **mastery:** rejects invalid and unauthorized calls before executing the tool body

### pydanticai-typed-output
- **prereqs:** pydanticai-tools, safe-output-parsing
- **objective:** validate agent results into an application type and surface typed failures
- **misconceptions:** valid JSON is valid output; retries should hide every validation failure
- **mastery:** handles success, repairable output, and exhausted validation distinctly

---

## Island 15 — DSPy

### dspy-signatures
- **prereqs:** prompt-templates, output-schema
- **objective:** express an LM task through named input and output fields
- **misconceptions:** a signature is only a prompt template; descriptions replace examples
- **mastery:** converts a prose task into an explicit deterministic signature contract

### dspy-modules
- **prereqs:** dspy-signatures, langchain-runnables
- **objective:** compose signature-driven modules with ordinary Python control flow
- **misconceptions:** modules remove the need for orchestration; every step should share all context
- **mastery:** traces inputs and outputs through a multi-stage fake-model program

### dspy-metrics
- **prereqs:** dspy-modules, capability-metrics
- **objective:** encode task quality as a metric aligned with the desired capability
- **misconceptions:** exact match measures every output; the optimizer can repair a bad metric
- **mastery:** distinguishes two programs using a metric with documented limits

### dspy-optimization
- **prereqs:** dspy-metrics, eval-datasets, evaluation-leakage
- **objective:** optimize a program against training examples and verify it on held-out cases
- **misconceptions:** optimization guarantees generalization; evaluation cases may also train the optimizer
- **mastery:** keeps training and held-out cases separate and reports both results

---

## Framework execution policy

When framework islands are authored, dependencies are split into optional extras:

```toml
ai-ml = ["torch", "transformers"]
ai-rag = ["llama-index"]
ai-orchestration = ["langchain", "langgraph", "pydantic-ai", "dspy"]
```

The base game and portable build never install these extras. Graded missions use real
framework APIs but only local fixtures, tiny CPU workloads, fake model providers, and
pre-created local assets. Downloads, GPUs, API keys, Ollama, and provider calls belong
only to clearly labelled optional labs. Each extra receives its own CI job when its first
island ships.

Official API references for future authoring:

- PyTorch: <https://docs.pytorch.org/tutorials/beginner/basics/intro.html>
- Transformers: <https://huggingface.co/docs/transformers/quicktour>
- LangChain: <https://docs.langchain.com/oss/python/langchain/agents>
- LangGraph: <https://docs.langchain.com/oss/python/langgraph/overview>
- LlamaIndex: <https://docs.llamaindex.ai/>
- PydanticAI: <https://ai.pydantic.dev/>
- DSPy: <https://dspy.ai/>
