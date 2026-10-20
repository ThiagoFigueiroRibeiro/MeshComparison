# 04 — Configurar CI, revisão e proteção antes de escalar o projeto

> **Projeto novo:** criar o workflow assim que houver um comando de teste; definir gates de PR antes de trabalho paralelo com agentes. **Mesh Comparison: ✅ CI configurada; ❓ proteções remotas não verificadas; 🟡 testes end-to-end incompletos.**

## Finalidade

Transformar os testes em **regras aplicadas pelo repositório**, e não apenas recomendações em um prompt. CI executa comandos; o harness fornece contexto, permissões e uma forma de usar esse feedback.

## Do zero — ordem recomendada

1. Criar o repositório remoto, os templates de issue/PR e um workflow que rode em pull requests, tão logo exista um teste mínimo.
2. Preparar runner com versões declaradas (Python/Node etc.), dependências, cache quando seguro e privilégios mínimos; não colocar tokens em comandos, logs ou repositório.
3. Fazer CI executar **lint → testes rápidos → smoke → integração aplicável**. Separar testes lentos por job/gatilho e documentar quais verificações o CI *não* faz.
4. Abrir um PR pequeno para verificar que os jobs são encontrados, executados e produzem erro quando um teste falha.
5. Configurar proteção de branch ou ruleset no GitHub: exigir PR, status checks efetivamente produzidos, revisão humana quando apropriado, impedir push direto e garantir que exceções estejam controladas. Depende de permissões/plano.
6. Registrar o nome **real** dos jobs do run antes de defini-los como obrigatórios; revisar permissões de `GITHUB_TOKEN` e eventos de workflow (ex.: execução de código não confiável).
7. Criar processo de rollback e revisão para mudanças estruturais, principalmente dependências, algoritmos, migrações e segurança.
8. Garantir que o agente pode **propor** PR com resultados, mas não aprovar sua própria mudança ou contornar gates.

### Exemplo mínimo de fluxo (Python; adaptar ao stack)

```yaml
# CI mínimo ilustrativo para projetos Python; ajuste dependências e runners.
name: CI
on:
  pull_request:
  push:
    branches: [main]
permissions:
  contents: read
jobs:
  checks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: python -m pip install -e ".[dev]"
      - run: ruff check .
      - run: pytest -q
```

A instalação `.[dev]` só funciona se o projeto tiver pacote Python e extras definidos. Este bloco **não é** substituição pronta do CI Conda já existente, nem garante regras de proteção sem configurá-las no GitHub.

## Estado do Mesh Comparison

| Componente | Estado | Fonte |
| --- | :---: | --- |
| Workflow em `.github/workflows/ci.yml` | ✅ | [Arquivo existente](../../../.github/workflows/ci.yml) |
| Execução de Ruff | ✅ | Etapa `ruff check .` |
| Execução de pytest | ✅ | Etapa `pytest -q` da CI (configurada; checar um run para comprovar êxito) |
| Smoke de importação | ✅ | Pipelines geométrico e perceptual e `meshcomparison.gui.worker` |
| Teste completo com renderização no CI | ❌ | Workflow auditado **não** executa esses pipelines integralmente |
| Proteção obrigatória de PR/revisão | ❓ | É configuração remota, não comprovada pela presença de YAML |

**Neste repositório:** preservar as etapas de CI e a instalação editável `pip install -e . --no-deps` já existentes, acrescentar regressões da etapa 03, testar jobs gráficos separados e configurar/provar regras de branch. Não aplicar `environments/environment-lock.yml` do Windows cegamente ao runner Linux.

## Critérios de aceite

- [ ] PR executa checks relevantes; falha de teste realmente bloqueia a integração.
- [ ] Nome e status dos checks são conferidos em execução real.
- [ ] Regras de proteção e revisão estão configuradas e testadas no GitHub.
- [ ] CI possui permissões mínimas e logs sem segredos.
- [ ] Existe procedimento de rollback e de diagnóstico para falhas.

**Referências:** [GitHub Actions](https://docs.github.com/en/actions/concepts/workflows-and-actions/workflows) e [proteção de branch](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule).

**Próxima etapa:** [05 — Operação de agentes](05-ciclo-assistido-e-seguranca.md).
