# 02 — Criar contexto e instruções do agente no primeiro dia

> **Projeto novo:** definir antes da geração extensa de código. **Mesh Comparison: ✅ documentação de domínio; ❌ instruções específicas para agentes na raiz auditada.**

## Finalidade

Fazer o agente entender **onde procurar**, **como trabalhar**, **o que nunca alterar sem aprovação** e **como provar que concluiu**. Contexto de projeto e memória de conversa não são a mesma coisa.

## Do zero — procedimento recomendado

1. Escrever um **`AGENTS.md` pequeno na raiz** com: propósito; mapa dos principais arquivos; sequência de leitura; comandos de instalação, lint e testes; regras de segurança; convenções de alterações e formato do relatório de resultados.
2. Manter a documentação detalhada em arquivos próprios (arquitetura, API, contratos, decisões). Em `AGENTS.md`, **linkar** para eles; instruções longas e conflitantes tornam a manutenção difícil.
3. Criar `docs/architecture.md` com módulos, dependências, fluxo de dados, entradas, saídas, integrações e decisões reversíveis ou não. Acrescentar diagramas se forem úteis.
4. Criar `docs/adr/` e escrever ADR para decisões importantes: contexto, alternativas, decisão, consequências e critérios para reavaliar.
5. Definir `docs/working-agreements.md` ou equivalente: padrão de issue, tarefas pequenas, “definition of done”, review e atualização simultânea de código, testes e documentação.
6. Para Claude Code, documentar `CLAUDE.md` ou importação apropriada conforme suporte da versão; manter **uma única fonte de regras canônicas**. Consultar [documentação](https://code.claude.com/docs/en/memory) antes de assumir comportamento.
7. Para tarefas complexas, criar plano **por tarefa** com estado, dependências, decisões e checkpoint de retomada. Não transformar o `AGENTS.md` em registro de execução.
8. Testar **sem modificar arquivos**: pedir ao agente para localizar código, explicar como testar e enumerar restrições. Corrigir instruções que provoquem respostas inventadas.

### Modelo mínimo reutilizável de AGENTS.md

```md
# Agent instructions — <nome-do-projeto>

Before editing: read README.md, docs/architecture.md and the relevant ADRs.
Work in an isolated branch and keep changes scoped to the task.
Do not modify public contracts, data formats, security rules or scientific
methodology without explicit review.
Run the project-specific lint, tests and smoke checks documented in README.md.
Never claim tests passed unless you observed their actual output.
Report: summary, files changed, checks run/results, assumptions, limitations.
Open a pull request for human review; do not merge automatically.
```

Os comandos exatos devem ser definidos para a stack real. Texto de prompt **não substitui** proteção de arquivos, credenciais e branches.

## Já existe no Mesh Comparison?

| Item | Estado | Evidência |
| --- | :---: | --- |
| README com utilização e limitações | ✅ | [README](../../../README.md) |
| Passo a passo técnico de implementação | ✅ | [docs/implementation/step-by-step](../../implementation/step-by-step/) |
| Documentação de evolução de harness | ✅ | [docs/harness](../README.md) |
| Instruções de agente `AGENTS.md`/`CLAUDE.md` | ❌ | Não encontrados na raiz na auditoria registrada em 18/10/2026 |
| ADRs e políticas de domínio especializadas para o agente | ❓ | Necessitam inventário e validação |

### Adaptar o que existe sem jogar fora o código

Criar o `AGENTS.md` apontando para [pipeline geométrico](../../../src/meshcomparison/geometry/pipeline.py) e [perceptual](../../../src/meshcomparison/perceptual/pipeline.py). Declarar que mudanças em ICP, escala, unidades, definições de distância, câmeras e LPIPS/PSNR/SSIM exigem revisão metodológica, novos testes e registro de comparação com resultados anteriores.

## Critérios de aceite

- [ ] O agente localiza as fontes de verdade em sessão nova, sem memória da conversa.
- [ ] Instruções são curtas, versionadas e não contradizem arquitetura ou CI.
- [ ] Mudanças em contratos e domínios críticos têm regra de revisão explícita.
- [ ] Um template de tarefa/PR define critérios de aceite e evidências.
- [ ] Uma tarefa só de leitura confirma que arquivos e comandos citados existem.

**Próxima etapa:** [03 — Testes desde a primeira funcionalidade](03-testes-e-regressoes.md).
