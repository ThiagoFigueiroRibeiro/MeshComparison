# 00 — Planejar um projeto agent-ready antes do primeiro commit

> **Etapa de implantação inicial** · Aplicável a qualquer projeto novo · **Mesh Comparison: 🟡 parte do desenho pode ser inferida da documentação, mas não há baseline de decisões de harness desde a criação.**

## Por que esta etapa vem primeiro?

Um harness não é simplesmente um `AGENTS.md` nem uma pipeline de CI. Antes de pedir código à LLM, defina como o agente recebe contexto, quais ferramentas pode executar, como uma saída será julgada correta, quais ações exigem aprovação e como o trabalho será retomado. **A infraestrutura de confiança deve nascer junto com o repositório, não depois do produto.**

### No projeto novo — passo a passo

1. **Defina a finalidade e o tipo do projeto:** aplicação, biblioteca, pesquisa científica, web, mobile, dados ou automação. Declare explicitamente o que será produzido e o que está fora do escopo.
2. **Escreva o contrato de sucesso:** funcionalidades iniciais, entradas/saídas, critérios de aceite, comportamento esperado em falhas e exemplos mínimos executáveis. Não use “parece funcionar” como critério.
3. **Identifique invariantes de domínio:** regras que qualquer implementação por LLM precisa preservar (ex.: não alterar definição de métrica, contratos de API, modelo de dados ou políticas de segurança sem revisão).
4. **Escolha o nível de autonomia:** somente sugestões, edição local supervisionada, PR automatizado, ou automação maior. Defina desde já ações proibidas (merge sem aprovação, apagar dados, expor segredos, operações irreversíveis).
5. **Desenhe o fluxo de engenharia:** issue/especificação → plano → branch isolada → alteração → testes locais → CI → PR → revisão → integração. Para tarefa longa, registrar checkpoints e decisões.
6. **Defina arquitetura mínima:** módulos e interfaces, fronteiras entre processamento e visualização, linguagens, versões, configuração, gerenciamento de dependências e estratégia de testes.
7. **Escolha fontes de verdade:** `README.md` para uso, `AGENTS.md` para orientações do agente, `docs/architecture.md` para arquitetura, `docs/adr/` para decisões e `docs/harness/` para regras e roteiros do harness. Evite orientações duplicadas.
8. **Defina riscos e guardrails:** dados pessoais, propriedade intelectual, acesso à rede, permissões, custos da execução, limite de iterações, retenção de logs e estratégia de rollback.
9. **Crie uma tarefa vertical mínima** (uma entrada → processamento → saída → teste) para demonstrar o fluxo inteiro, em vez de escrever o projeto todo antes de criar verificações.

### Entregáveis recomendados no primeiro commit

```text
project/
├── README.md                   # Objetivo, comandos e limites
├── AGENTS.md                   # Regras e roteiro de leitura para agentes
├── docs/
│   ├── architecture.md         # Módulos e contratos
│   ├── adr/                    # Decisões arquiteturais
│   └── harness/                # Critérios e processo de execução
├── src/                        # Código inicial (nome ajustado à stack)
├── tests/                      # Primeiro teste executável
├── .github/workflows/ci.yml    # Primeiro gate automático
└── <manifesto-dependencias>    # environment.yml, pyproject.toml, package.json etc.
```

A estrutura é **sugestão**, não obrigação universal. Ajuste linguagem, SO, ferramenta e plataforma; use um runtime de agentes existente antes de cogitar construir um orquestrador.

## Exemplo real: Mesh Comparison

| Elemento | Estado | Evidência e interpretação |
| --- | :---: | --- |
| Objetivo e arquitetura funcional descritos | ✅ | [README principal](../../../README.md), pipelines geométrico e perceptual |
| Pipelines de domínio separados | ✅ | [Geometria](../../../src/meshcomparison/geometry/pipeline.py) e [percepção](../../../src/meshcomparison/perceptual/pipeline.py) |
| Documentação de implementação | ✅ | [Documentação preexistente](../../implementation/step-by-step/) |
| Contrato de métricas e regressões sistemáticas | 🟡 | [Plano de validação](../../implementation/step-by-step/10-limitacoes-evolucao.md) ainda declara lacunas |
| Autonomia, permissões e decisões do agente versionadas | ❌ | `AGENTS.md` ausente na `main` auditada |
| ADRs e aprovações documentadas para alterações científicas | ❓ | Não comprovados na auditoria de 18/10/2026 |

**Para este projeto existente:** reconstruir o contrato a partir dos pipelines e resultados atuais, registrando decisões e seus limites antes de permitir novas modificações por agentes.

## Critérios de conclusão no projeto novo

- [ ] Existe uma especificação curta com pelo menos um teste de aceitação verificável.
- [ ] Invariantes, riscos, permissões e revisão humana estão documentados.
- [ ] A estrutura inicial e a fonte de verdade de cada informação estão decididas.
- [ ] Há um fluxo claro para o primeiro PR e um plano de rollback.

**Próxima etapa:** [01 — Ambiente e baseline](01-auditoria-e-linha-de-base.md) · [Bibliografia](../REFERENCIAS.md).
