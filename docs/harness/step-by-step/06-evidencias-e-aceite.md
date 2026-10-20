# 06 — Avaliar, medir e manter o harness desde o início

> **Projeto novo:** definir indicadores antes de escalar o trabalho; reavaliar a cada marco. **Mesh Comparison: ✅ resultados e documentação de execução existem; ❓ desempenho e segurança de agentes ainda não foram avaliados sistematicamente.**

## Finalidade

Um harness útil precisa continuar confiável após novos commits, mudanças de modelos/agentes e integração de colaboradores. “Completo” é um **critério operacional definido pelo projeto**, não certificação universal.

## Do zero — roteiro

1. Escolher uma **suite de tarefas de avaliação do agente** (ex.: adicionar teste, corrigir bug, refatorar sem mudar comportamento, atualizar documentação, reconhecer tarefa que exige aprovação).
2. Definir métricas: sucesso no critério de aceite, % de testes executados, regressões, número de iterações, tempo/custo, escalonamentos corretos e percentual de PRs com evidências.
3. Registrar por tarefa: commit inicial, instrução, ferramentas e permissões, mudanças, resultados observados dos comandos, decisões e resultado da revisão. Evitar segredos, dados pessoais e logs desnecessários.
4. Tratar falhas como sinal para atualizar testes, documentação e guardrails. Não depender exclusivamente de melhorar prompt; consertar a infraestrutura.
5. Adicionar revisões periódicas de instruções e políticas, porque ferramentas e modelos evoluem. Verificar links, comandos, versões e decisões desatualizadas.
6. Manter uma definição concreta de **pronto para uso supervisionado** e uma lista separada de autonomia futura; não considerar “agente trabalhou sozinho” prova de confiabilidade.
7. Criar um rito de aceite: PR com evidências, critérios atendidos, decisão humana, rollback e atualização do histórico técnico.
8. Para projeto novo, executar esse processo desde o **primeiro PR**, revisando a complexidade conforme o projeto cresce.

## Definição operacional de pronto

| Área | Evidência exigida |
| --- | --- |
| Contexto | Instruções e arquitetura versionadas, lidas em nova sessão |
| Reprodutibilidade | Ambiente instalável, entradas e comandos repetíveis |
| Verificação | Testes unitários, integração e end-to-end relevantes |
| Integração | CI confiável, proteção da branch e revisão obrigatória |
| Segurança | Permissões mínimas, isolamento, logs sem segredos, escalonamento |
| Feedback | Agente demonstrou detectar erro, corrigir e revalidar |
| Rastreabilidade | Tarefa → commit → testes → PR → revisão |
| Manutenção | Dono, frequência de revisão e decisões registradas |

## Exemplo Mesh Comparison

| Evidência | Estado | Observação |
| --- | :---: | --- |
| Resultado de métricas e saídas exemplares | ✅ | [README e resultados](../../../README.md) |
| Histórico de escolhas/etapas de desenvolvimento | ✅ | [Documentação de implementação](../../implementation/step-by-step/) |
| Testes e lint declarados no CI | ✅ | [Workflow](../../../.github/workflows/ci.yml) |
| Regressão científica sistemática | 🟡 | Ainda há cenários pendentes na [etapa 10](../../implementation/step-by-step/10-limitacoes-evolucao.md) |
| Avaliação documentada de sessões de agente | ❓ | Evidências não confirmadas no repositório auditado |
| Proteção de branch e aprovação obrigatória | ❓ | Precisa verificar configurações e um PR real |
| Harness operacional supervisionado | ❓ | Só classificar assim após cumprir os critérios nesta série |

## Critérios de aceite

- [ ] Pelo menos três tarefas representativas foram avaliadas com registros reproduzíveis.
- [ ] Há uma falha provocada que foi detectada e tratada corretamente.
- [ ] O agente respeita pontos de aprovação e permissões nos testes.
- [ ] PRs e logs comprovam resultados, não apenas declarações.
- [ ] Uma pessoa responsável revisou a definição de pronto e as pendências.

**Depois:** use o [modelo para próximos projetos](07-modelo-reutilizavel.md), atualize a [tabela de maturidade](../README.md) e consulte as [referências](../REFERENCIAS.md).
