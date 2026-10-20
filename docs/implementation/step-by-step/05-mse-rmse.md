# 05 — Conferir MSE e RMSE simétricos

> **Status: concluída.** O cálculo simétrico de MSE e RMSE já está implementado no pipeline geométrico.

![Esquema da etapa](../images/distancias.svg)

## Passo 1 — Conferir o cálculo existente

A partir de `nn_distances`, já implementada na etapa 04, o código obtém distâncias GT→RM e RM→GT. Use ambas as direções para evitar que uma malha incompleta pareça perfeita apenas por estar contida na outra.

## Passo 2 — Trecho da implementação atual

```python
# Calcula MSE simétrico e RMSE usando as funções reais do pacote
import numpy as np
from meshcomparison.common.distances import symmetric_mse
from meshcomparison.geometry.metrics import compute_metrics

gt_vertices = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.]])
rm_vertices = gt_vertices.copy()
mse = symmetric_mse(gt_vertices, rm_vertices)
rmse = compute_metrics(gt_vertices, rm_vertices)['rmse']
assert np.isclose(mse, 0.0) and np.isclose(rmse, 0.0)
```

O MSE é implementado em [`common/distances.py`](../../../src/meshcomparison/common/distances.py), enquanto o RMSE da saída geométrica é calculado em [`geometry/metrics.py`](../../../src/meshcomparison/geometry/metrics.py). **Não existe uma função pública `symmetric_rmse` separada na branch atual**; o exemplo antigo que a declarava era apenas ilustrativo.

## Passo 3 — Interpretar e validar

A fórmula é `MSE = (média(d_GT→RM²) + média(d_RM→GT²))/2` e `RMSE = √MSE`. Em malhas idênticas, espere valores próximos de zero. A unidade de MSE é quadrática; a de RMSE é linear. Registre valores pré e pós-alinhamento.

## Passo 4 — Próxima etapa

Continue para [06 — Conferir Chamfer e Hausdorff](06-chamfer-hausdorff.md).
