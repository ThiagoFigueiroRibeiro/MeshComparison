# 10 — Validação sistemática e plano de evolução

> **Estado: parcialmente coberto por testes unitários; validação end-to-end sistemática pendente.** A branch possui testes automatizados em `tests/`, mas eles não cobrem todas as classes de deformações e condições de renderização.

![Esquema da etapa](../images/pipeline.svg)

## 1. O que já está testado

Os testes abaixo **existem no repositório**; isso não equivale a afirmar que foram executados nesta revisão nem que têm cobertura completa.

| Componente | Evidência existente | Limite |
| --- | --- | --- |
| Erros geométricos entre pontos | [`tests/test_geometry.py`](../../../tests/test_geometry.py): nuvens idênticas e deslocamento de um ponto | Não exercita pipeline de malhas completo nem superfície contínua |
| MSE, amostragem e transformação de caixa | [`tests/test_common.py`](../../../tests/test_common.py) | Não comprova convergência robusta de ICP em todas as situações |
| Device CPU/CUDA e avisos | [`tests/test_device.py`](../../../tests/test_device.py) com simulações (*mocks*) | Não confirma GPU real nem execução de LPIPS em CUDA |
| PSNR e máscaras | [`tests/test_perceptual.py`](../../../tests/test_perceptual.py) | Não confirma renderização/LPIPS/SSIM em cenário multivista completo |
| Preparo comum e exportação alinhada | [`tests/test_prepare.py`](../../../tests/test_prepare.py) | Não cobre todas as condições geométricas nem a convergência robusta de ICP |
| Configuração e worker da GUI | [`tests/test_gui_config.py`](../../../tests/test_gui_config.py), [`tests/test_worker.py`](../../../tests/test_worker.py) | Worker exercitado em subprocesso para geometria; não abre janela nem valida Qt/PyVistaQt |
| Leitura de resultados para o viewer | [`tests/test_outputs.py`](../../../tests/test_outputs.py) | Não valida a interação real com o viewer 3D |

O [workflow de CI](../../../.github/workflows/ci.yml) chama Ruff, pytest e uma verificação de importação dos pipelines, mas **não executa os pipelines completos com renderização**, nem faz teste gráfico da GUI.

## 2. O que ainda precisa ser implementado e comprovado

| Caso de teste | Resultado esperado / objetivo | Prioridade |
| --- | --- | --- |
| Malhas 3D idênticas | Métricas geométricas próximas de zero, sem alinhamento desnecessário | Alta |
| Translação e rotação controladas | MSE pré/pós-ICP e transformação coerentes | Alta |
| Escala uniforme | Distinguibilidade entre diferenças dimensionais e alinhamento com escala | Alta |
| Diferenças de densidade de vértices | Compreender viés das métricas por vizinhos entre vértices | Alta |
| Buracos e superfícies incompletas | Avaliar robustez, correspondências e localização dos erros | Alta |
| Deformação localizada | Heatmap e métricas coerentes com regiões modificadas | Alta |
| Renderização offscreen | Gerar PNGs consistentes com câmeras e parâmetros documentados | Alta |
| LPIPS/PSNR/SSIM em múltiplas vistas | Validar contratos, máscaras, valores-limite e estabilidade | Alta |
| Abertura, execução e cancelamento via GUI | Teste manual documentado ou teste Qt automatizado em ambiente compatível | Média |
| CUDA disponível vs CPU-only | Verificar device real, avisos, metadados e equivalência metodológica | Média |

Separe testes unitários rápidos dos testes de integração pesados. Controle SO, resolução, driver/renderizador, tolerâncias numéricas, parâmetros de câmera e versões de modelo. Um teste sintético que passa **não** demonstra equivalência de resultados entre GPU/CPU ou entre sistemas operacionais.

## 3. Exemplo reproduzível já possível

O código seguinte usa a **função real** `compute_metrics` do pacote, após instalação editável:

```python
# Verifica que nuvens de pontos idênticas têm distância geométrica nula
import numpy as np
from meshcomparison.geometry.metrics import compute_metrics

points = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.]])
result = compute_metrics(points, points.copy())

assert np.isclose(result["chamfer_mean"], 0.0)
assert np.isclose(result["hausdorff"], 0.0)
assert np.isclose(result["rmse"], 0.0)
```

Isso verifica uma propriedade básica de **distâncias entre vértices**; não valida ICP nem avaliação de malhas tridimensionais inteiras.

## 4. Melhoria de arquitetura: fazer depois de proteger as métricas

Potenciais evoluções: amostragem uniforme de superfície, análise topológica, escolha de ICP com/sem escala, PSNR RGB convencional e validação de renderização. A **separação em módulos já foi implementada** em `src/meshcomparison/`, portanto não deve continuar como uma tarefa pendente genérica. Alterações nas definições científicas exigem testes de regressão e documentação (ADR) antes de comparar novos CSVs com o histórico.

## 5. Ajustes recentes da implementação

O preparo compartilhado dos pipelines agora está em [`common/prepare.py`](../../../src/meshcomparison/common/prepare.py); a camada GUI foi separada em painéis, supervisor, worker de processo filho e carregador de saídas. A mensagem de progresso do pipeline perceptual também usa agora o número real de vistas (`num_views`). Esses testes cobrem partes isoladas do contrato; não substituem a validação end-to-end e a inspeção da janela em um ambiente gráfico real.

## Critérios para concluir esta etapa

- [ ] Casos geométricos controlados (identidade, transformação, deformação, incompletude e densidade) automatizados.
- [ ] Teste integrado de pelo menos uma execução completa dos pipelines com saídas verificadas.
- [ ] GPU/GUI, se declaradas suportadas, testadas em ambiente real e documentadas.
- [ ] Metodologia, parâmetros, tolerâncias e comandos de reprodução registrados.
- [ ] Resultados comparáveis e exceções conhecidos sem mascarar falhas.

Retorne ao [índice de implementação](../README.md), ao [guia de Harness](../../harness/README.md) ou à [visão geral da documentação](../../README.md).
