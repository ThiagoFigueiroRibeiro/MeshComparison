# 07 — Modelo reutilizável para começar outros projetos com Harness

> **Modelo de referência, não implantação automática.** Copie e adapte este procedimento ao criar um repositório novo. Os itens ✅ na documentação do Mesh Comparison **não** equivalem à conclusão destes passos em um projeto futuro.

## Bootstrap recomendado (ordem de implantação)

| Momento | Ação | Evidência de sucesso |
| --- | --- | --- |
| **Antes do código** | Definir escopo, invariantes, riscos, permissões e critérios de aceite | Especificação curta e revisável |
| **Primeiro commit** | README, documentação de arquitetura, AGENTS.md, dependências/lock e projeto mínimo | Agente consegue localizar os comandos e explicar os limites |
| **Primeira funcionalidade** | Teste unitário + integração e um ponto de entrada mínimo (CLI, GUI ou API) + resultado de referência | Execução local determinística |
| **Primeiro PR** | CI, lint, testes, template de PR e revisão humana | Check obrigatório detecta falha introduzida |
| **Primeira tarefa de agente** | Branch isolada, limites reais, plano, diff, testes e handoff | PR com evidências e aprovação |
| **Primeiro marco** | Suite de avaliação de tarefas e relatórios de regressão | Indicadores e pendências rastreáveis |
| **Evolução** | ADRs, documentação, testes e limites atualizados a cada mudança | Sem divergência entre código, docs e regras |

## Estrutura recomendada (adaptar à linguagem e à plataforma)

```text
project/
├── README.md
├── AGENTS.md
├── docs/
│   ├── architecture.md
│   ├── adr/
│   │   └── 0001-decisoes-iniciais.md
│   └── harness/
│       ├── README.md                 # Política e status
│       └── step-by-step/             # Manual de desenvolvimento
├── src/                               # Ou pacote, app/, lib/, etc.
├── tests/
│   ├── unit/
│   └── integration/
├── .github/
│   ├── workflows/ci.yml
│   └── pull_request_template.md
└── <manifesto e lock de dependências>
```

A proteção de branch é configurada nas **settings/rulesets do repositório**, não em um arquivo dessa árvore.

## Modelo de especificação inicial

```md
# Nova funcionalidade / tarefa

## Problema e motivação
O que precisamos resolver e por quê?

## Entradas, saídas e invariantes
Quais formatos, contratos, condições de erro e regras são obrigatórios?

## Critérios verificáveis de aceite
- [ ] Caso válido funciona
- [ ] Caso inválido falha de forma explícita
- [ ] Teste de regressão existente continua válido
- [ ] README/ADR atualizados quando houver decisão relevante

## Execução do agente
Escopo de arquivos:
Ferramentas e permissões:
Limite de tentativas/custo:
Ações que exigem revisão:

## Evidências de entrega
Comandos executados e resultados:
Artefatos/links dos testes:
Riscos e limitações:
Link do PR e revisão:
```

## Como reutilizar em qualquer projeto

1. Inicie pelo [00 — planejamento](00-planejamento-e-arquitetura.md); personalize os invariantes para o domínio.
2. Faça [01 — ambiente](01-auditoria-e-linha-de-base.md) e [02 — instruções](02-instrucoes-e-contexto.md) no primeiro commit.
3. Implemente [03 — testes](03-testes-e-regressoes.md) e [04 — CI](04-ci-e-protecao.md) antes de aceitar mudanças extensas produzidas por agentes.
4. Faça [05 — ciclo supervisionado](05-ciclo-assistido-e-seguranca.md) com mudanças reversíveis e verificáveis.
5. Meça e melhore com [06 — avaliação](06-evidencias-e-aceite.md).

### Duas formas de utilizar o mesmo guia

| Cenário | Como aplicar |
| --- | --- |
| **Projeto novo** | Seguir 00 → 06 desde a primeira versão; cada fase gera artefatos reais e evidências |
| **Projeto existente, como Mesh Comparison** | Auditar e **reaproveitar** as partes já implantadas; executar apenas lacunas, sem reescrever pipelines que funcionam |

## Limites importantes

- A estrutura proposta é uma **prática de engenharia**, não uma norma universal nem certificação.
- CI e documentação são pré-requisitos úteis; sozinhos não provam que um agente executa ciclos de desenvolvimento com segurança.
- Não é necessário criar um harness “do zero” se já se usa o runtime de Codex ou Claude Code.
- Recursos de GPU, renderização, modelos locais e integração devem ser decididos **por necessidades reais** da aplicação.
- Testes e aprovação devem existir fora da influência do agente que escreveu o código.

Retorne ao [índice](README.md), à [visão geral do Harness](../README.md) ou às [referências](../REFERENCIAS.md).
