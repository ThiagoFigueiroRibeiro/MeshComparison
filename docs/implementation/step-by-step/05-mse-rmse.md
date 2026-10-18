# 05 — Conferir MSE e RMSE simétricos

> **Status: concluída.** O cálculo simétrico de MSE e RMSE já está implementado no pipeline geométrico.

![Esquema da etapa](../images/distancias.svg)

## Passo 1 — Conferir o cálculo existente

A partir de `nn_distances`, já implementada na etapa 04, o código obtém distâncias GT→RM e RM→GT. Use ambas as direções para evitar que uma malha incompleta pareça perfeita apenas por estar contida na outra.

## Passo 2 — Trecho da implementação atual

```python
# Mede erro quadrático simétrico e sua raiz usando distâncias entre vértices
import numpy as np

def symmetric_vertex_errors(gt_vertices, rm_vertices):
    a, _ = nn_distances(gt_vertices, rm_vertices)
    b, _ = nn_distances(rm_vertices, gt_vertices)
    return a, b

def symmetric_mse(gt_vertices, rm_vertices):
    a, b = symmetric_vertex_errors(gt_vertices, rm_vertices)
    return 0.5 * (np.mean(a ** 2) + np.mean(b ** 2))

def symmetric_rmse(gt_vertices, rm_vertices):
    return np.sqrt(symmetric_mse(gt_vertices, rm_vertices))
```

## Passo 3 — Interpretar e validar

A fórmula é `MSE = (média(d_GT→RM²) + média(d_RM→GT²))/2` e `RMSE = √MSE`. Em malhas idênticas, espere valores próximos de zero. A unidade de MSE é quadrática; a de RMSE é linear. Registre valores pré e pós-alinhamento.

## Passo 4 — Próxima etapa

Continue para [06 — Conferir Chamfer e Hausdorff](06-chamfer-hausdorff.md).

**Código de referência:** [distâncias simétricas](../../../src/meshcomparison/common/distances.py), [métricas geométricas](../../../src/meshcomparison/geometry/metrics.py) e [pipeline geométrico](../../../src/meshcomparison/geometry/pipeline.py).
