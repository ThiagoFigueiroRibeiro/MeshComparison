# Referências sobre Agent Harness — Mesh Comparison

> **Catálogo de fontes** para a documentação em [`docs/harness/`](README.md). Atualizado e com URLs conferidas em **18/10/2026**.
>
> **Terminologia:** *harness* é a infraestrutura que conecta agentes, contexto, ferramentas, execução e verificações; *harmless* é um termo distinto, relacionado à segurança do comportamento de modelos. Não devem ser tratados como sinônimos.
>
> Os links abaixo são **referências de estudo e projeto**, não indicam que seus exemplos já tenham sido implementados no Mesh Comparison.

## 1. Fundamentos e arquitetura de Agent Harness

| Fonte | Referência | Aplicação ao Mesh Comparison |
| --- | --- | --- |
| **Anthropic** | [Harness design for long-running application development](https://www.anthropic.com/engineering/harness-design-long-running-apps) — 24/03/2026 | Divisão entre planejamento, implementação e avaliação; critérios de aceite explícitos, ciclos de feedback, handoff de contexto e teste de funcionalidades. Útil para evoluir a [etapa 05](step-by-step/05-ciclo-assistido-e-seguranca.md). |
| **OpenAI** | [Alavancando o Codex em um mundo centrado no agente](https://openai.com/pt-BR/index/harness-engineering/) — 11/02/2026; [versão original em inglês](https://openai.com/index/harness-engineering/) | Documentação como fonte de verdade, legibilidade do repositório para agentes, regras arquiteturais e ciclos de integração; base para [etapa 02](step-by-step/02-instrucoes-e-contexto.md). **As versões em português e inglês são o mesmo artigo, não duas fontes diferentes.** |
| **Visual Studio Code / Microsoft** | [Understand agent harnesses](https://code.visualstudio.com/docs/agents/concepts/agent-harnesses) | Conceitos de harness e distinção entre agente/modelo e o ambiente que fornece contexto, ferramentas e execução. |
| **OpenAI Developers** | [Codex as a platform: build on the open agent harness](https://developers.openai.com/blog/codex-as-a-platform) | Componentes de um harness e integração com fluxos de desenvolvimento baseados em agentes. |

## 2. Instruções persistentes, execução e avaliação

| Fonte | Referência | Aplicação ao Mesh Comparison |
| --- | --- | --- |
| **OpenAI Cookbook** | [Iterating Development Workflows with Codex](https://developers.openai.com/cookbook/examples/codex/iterating-development-workflows-with-codex) | Aprimorar fluxos repetíveis com critérios de validação e feedback. |
| **OpenAI Developers** | [Rethinking skills and prompts for GPT-6 Astra](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra) | Revisar instruções e habilidades de agentes de acordo com a capacidade do modelo, sem aumentar a complexidade desnecessariamente. |
| **OpenAI Cookbook** | [Using PLANS.md for multi-hour problem solving](https://developers.openai.com/cookbook/articles/codex_exec_plans) | Planejamento rastreável de tarefas longas, escopo e execução em etapas. |
| **Claude Code / Anthropic** | [How Claude remembers your project](https://code.claude.com/docs/en/memory) | Organização de instruções persistentes, como `CLAUDE.md` e arquivos de instrução aplicáveis. |
| **Claude Code / Anthropic** | [Hooks reference](https://code.claude.com/docs/en/hooks) | Automatização de verificações em momentos definidos do trabalho do agente; não substitui CI nem permissões do sistema. |

## 3. Integração contínua e segurança de mudanças

| Fonte | Referência | Aplicação ao Mesh Comparison |
| --- | --- | --- |
| **GitHub Docs** | [Workflows](https://docs.github.com/en/actions/concepts/workflows-and-actions/workflows) | Definir jobs de CI, gatilhos, testes automatizados e resultados de execução. |
| **GitHub Docs** | [Managing a branch protection rule](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule) | Configurar status checks, revisão e proteção contra integração de código não validado. |

## 4. Ferramentas complementares para IA local

| Fonte | Referência | Aplicação ao Mesh Comparison |
| --- | --- | --- |
| **CanIRun.ai** | [Can I run AI locally?](https://www.canirun.ai/) | Consultar **estimativas** de compatibilidade entre hardware, memória e modelos de IA executados localmente. Pode ajudar a estudar um agente local, mas **não implementa nem documenta um harness**; compatibilidade estimada não substitui testes reais de desempenho. |

## 5. Como usar este catálogo

- Comece pelos fundamentos (Anthropic, OpenAI e VS Code) para entender responsabilidades e limites de um harness.
- Use Claude Code, Codex e os materiais de planejamento para escrever instruções e processos executáveis.
- Use GitHub Docs para transformar verificações em exigências reais de integração.
- Consulte CanIRun.ai **apenas** se decidir investigar modelos locais e requisitos de hardware.
- Registre no PR ou ADR qual fonte fundamentou decisões que alterem arquitetura, automação, permissões ou metodologia.
- Reavalie estas fontes periodicamente. Artigos descrevem abordagens e experimentos; **não certificam** que o projeto já esteja preparado para execução autônoma.

**Documentação principal:** [Agent Harness — Mesh Comparison](README.md) · **Roteiro de implementação:** [step-by-step](step-by-step/README.md).
