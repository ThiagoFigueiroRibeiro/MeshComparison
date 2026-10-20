# 06 — Conferir Chamfer e Hausdorff

> **Status: concluída.** Chamfer e Hausdorff simétricos já estão implementados no pipeline geométrico.

![Esquema da etapa](../images/distancias.svg)

## Passo 1 — Conferir as métricas existentes

O código já reaproveita as duas listas de distâncias calculadas na etapa 05. Chamfer resume o erro médio; Hausdorff registra o pior desvio encontrado.

## Passo 2 — Trecho da implementação atual

```python
# Calcula distância Chamfer média e Hausdorff simétrica entre vértices
import numpy as np

def compute_metrics(gt_vertices, rm_vertices):
    a, b = symmetric_vertex_errors(gt_vertices, rm_vertices)
    return {
        'd_gt2rm': a,
        'd_rm2gt': b,
        'chamfer_mean': 0.5 * (np.mean(a) + np.mean(b)),
        'hausdorff': max(np.max(a), np.max(b)),
        'rmse': np.sqrt(0.5 * (np.mean(a**2) + np.mean(b**2))),
    }
```

## Passo 3 — Interpretar e validar

Teste uma RM com um único vértice distante: Hausdorff deverá reagir fortemente, enquanto Chamfer pode aumentar pouco. Estas implementações usam **vértices**, não a distância exata à superfície triangular; a densidade da malha influencia os resultados.

## Passo 4 — Próxima etapa

Continue para [07 — Conferir câmera, renders e heatmap](07-renderizacao-heatmaps.md).

**Código de referência:** [métricas geométricas](../../../src/meshcomparison/geometry/metrics.py).
