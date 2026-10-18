# 10 — Planejar a validação e a evolução

> **Status: pendente de validação sistemática.** Esta etapa organiza testes que ainda precisam ser executados e melhorias propostas; não é uma funcionalidade já concluída.

![Esquema da etapa](../images/pipeline.svg)

## Passo 1 — Planejar os testes que faltam

Ainda falta executar e registrar casos controlados para: malhas idênticas, deslocadas, escaladas, com vértices extras, buracos e densidades diferentes. A reorganização do código em `common/`, `geometry/` e `perceptual/` já foi concluída; agora execute os testes do pacote e registre os resultados esperados para cada métrica.

## Passo 2 — Caso mínimo de referência

```python
# Verifica um caso mínimo de consistência das métricas geométricas
import numpy as np

points = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.]])
result = compute_metrics(points, points.copy())
assert np.isclose(result['chamfer_mean'], 0.0)
assert np.isclose(result['hausdorff'], 0.0)
assert np.isclose(result['rmse'], 0.0)
```

## Passo 3 — Separar validações pendentes de melhorias futuras

A validação sistemática ainda está pendente: os testes unitários existentes cobrem funções selecionadas, mas não substituem testes de ponta a ponta com malhas controladas. Como melhorias futuras, considere amostragem uniforme de superfícies, inspeção de topologia, opção de ICP sem escala e PSNR RGB convencional. Essas mudanças alteram a metodologia; documente-as antes de comparar resultados novos com CSVs antigos.

## Passo 4 — Próxima etapa

Depois de executar e documentar os testes, atualize o status desta etapa e a revisão do roteiro em [docs/README.md](../README.md).

**Código de referência:** [testes compartilhados](../../../tests/test_common.py), [testes geométricos](../../../tests/test_geometry.py), [testes perceptuais](../../../tests/test_perceptual.py), [pipeline geométrico](../../../src/meshcomparison/geometry/pipeline.py) e [pipeline perceptual](../../../src/meshcomparison/perceptual/pipeline.py).
