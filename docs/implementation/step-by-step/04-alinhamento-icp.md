# 04 — Conferir a correspondência e o ICP

> **Status: concluída.** A busca de vizinhos e o alinhamento ICP condicional já estão implementados nos dois pipelines.

![Esquema da etapa](../images/icp.svg)

## Passo 1 — Conferir correspondência e alinhamento

A função `nn_distances` já usa `scipy.spatial.cKDTree` para localizar o vértice de destino mais próximo de cada vértice de origem. O pipeline calcula o MSE simétrico pré-alinhamento e aplica ICP à RM quando o valor supera `1e-4`, mantendo GT fixa.

## Passo 2 — Trecho da implementação atual

```python
# Calcula vizinhos mais próximos e configura o estimador ICP com escala uniforme
from scipy.spatial import cKDTree
import open3d as o3d

def nn_distances(src, dst):
    return cKDTree(dst).query(src, k=1)

estimator = o3d.pipelines.registration.TransformationEstimationPointToPoint(with_scaling=True)
```

## Passo 3 — Entender parâmetros e validar

A implementação existente de `similarity_icp_align` converte os vértices em `o3d.geometry.PointCloud`, limita a amostra a 50 mil pontos, estima escala e translação iniciais pelas caixas envolventes e executa `registration_icp` em duas passagens (limiares 0,25 e 0,05, até 100 iterações cada). Depois, aplica a matriz 4×4 resultante à RM. Valide com uma malha deslocada e verifique a queda do MSE. A etapa 10 organiza essa validação junto a outros casos controlados. O ICP atual também pode corrigir escala: documente essa decisão antes de interpretar diferenças dimensionais.

## Passo 4 — Próxima etapa

Continue para [05 — Conferir MSE e RMSE simétricos](05-mse-rmse.md).

**Código de referência:** [alinhamento ICP](../../../src/meshcomparison/common/alignment.py) e [preparo compartilhado](../../../src/meshcomparison/common/prepare.py).
