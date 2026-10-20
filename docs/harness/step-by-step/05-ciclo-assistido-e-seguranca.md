# 05 — Operar agentes com ferramentas, limites e feedback

> **Projeto novo:** estabelecer o ciclo supervisionado já na primeira tarefa; aumentar autonomia **só após** validar ambiente, testes e gates. **Mesh Comparison: ❓ ciclo de agente não demonstrado no repositório auditado.**

## Finalidade

O harness combina **agente + instruções + ferramentas + permissões + feedback + checkpoints**. Codex e Claude Code já oferecem formas de executar agentes; não é obrigatório criar um framework próprio.

## Do zero — processo recomendável

1. Escolher runtime de agente (Codex, Claude Code ou outro) e documentar versão, configuração, fontes de contexto e comandos permitidos.
2. Preparar ambiente isolado (diretório/branch, credenciais mínimas, rede restrita conforme necessidade). Definir explicitamente quais caminhos o agente pode editar.
3. Criar tarefa pequena com especificação e **critérios verificáveis**, acompanhada de referência a `AGENTS.md` e documentação do domínio.
4. Antes de editar, solicitar plano curto e identificação das restrições. Para tarefas longas, persistir plano com decisões e estado de execução.
5. Permitir implementação somente no escopo combinado. Registrar mudanças de dependências, contratos, arquiteturas e dados para revisão.
6. **Ciclo de validação:** executar lint, testes, smoke, ler erros efetivos, corrigir, reexecutar e produzir relatório de resultados. Limitar tentativas, custo e tempo; interromper e escalar quando falhas persistirem.
7. Abrir PR com diff, evidências, testes e limitações. Exigir revisão humana e gates de CI; não conceder permissões que contornem essas barreiras.
8. Testar em ambiente de avaliação uma falha proposital para conferir se o agente diagnostica o problema e **não** burla os testes.
9. Definir regras de parada e escalonamento: vulnerabilidade, vazamento de credenciais, dado irreversível, decisão de produto, alteração científica, ambiente quebrado e resultados contraditórios.
10. Criar rotina de handoff: tarefa atual, concluído, próximo passo, decisões, logs resumidos e commit/PR. Isso evita depender de uma sessão de chat longa.

### Contrato de tarefa reutilizável

```md
# Task
Objective:
Allowed files:
Acceptance criteria:
Relevant architecture / ADR:
Commands to run:
Sensitive actions requiring approval:
Expected evidence:
Escalation conditions:
```

**Regras textuais não são sandbox nem política de acesso.** Para controles críticos, usar permissões, isolamento, revisões de PR e restrições reais das ferramentas. Hooks podem tornar checagens mais convenientes, mas não devem ser o único mecanismo de bloqueio.

## Aplicação ao Mesh Comparison

| Componente | Estado | Uso prático |
| --- | :---: | --- |
| Entradas, saídas e comandos dos pipelines | ✅ | Oferecem ferramentas e tarefas testáveis |
| CI automatizada | ✅ | Feedback para alterações em PR |
| Documentação de domínio | ✅ | Contexto para ler antes de editar |
| `AGENTS.md` versionado | ❌ | Criar na [etapa 02](02-instrucoes-e-contexto.md) |
| Loop de agente com falha → correção → revalidação registrada | ❓ | Demonstrar em PR de teste, não apenas afirmar que ocorre |
| Permissões/escopo/limites do agente documentados | ❓ | Configurar e testar sob supervisão |

Para o projeto atual, escolher tarefa não destrutiva, manter `data/samples/gt.stl`/`data/samples/mod.stl` e resultados de referência intactos, e tornar toda mudança metodológica sujeita a revisão e testes de regressão.

## Critérios de aceite

- [ ] O agente concluiu duas tarefas controladas, com arquivos e testes documentados.
- [ ] Ao menos um erro foi diagnosticado, corrigido e revalidado com evidência.
- [ ] Limites de acesso, tentativas, custo e ações de aprovação estão claros.
- [ ] O agente fornece relatório com resultados observados e incertezas reais.
- [ ] Revisão humana e proteção de branch não podem ser burladas pelo agente.

**Próxima etapa:** [06 — Evidências e maturidade](06-evidencias-e-aceite.md).
