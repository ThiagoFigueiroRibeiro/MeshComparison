# 03 — Importar e normalizar duas malhas

> **Status: concluída.** O carregamento e a normalização compartilhada pela GT já estão implementados nos dois pipelines.

![Esquema da etapa](../images/pipeline.svg)

## Passo 1 — Conferir o carregamento existente

Confira `load_mesh(path)`, implementada usando `trimesh.load(path, force='scene', process=False, maintain_order=True)`. Se o retorno for uma cena, percorra as instâncias e aplique as transformações do grafo antes de concatenar as geometrias. Remova vértices não referenciados e rejeite `.fbx` explicitamente.

## Passo 2 — Trecho da implementação atual

```python
# Normaliza as duas malhas usando a mesma escala derivada da referência
import numpy as np

gt = load_mesh(gt_path)
rm = load_mesh(rm_path)
diagonal_gt = np.linalg.norm(gt.bounds[1] - gt.bounds[0])
if diagonal_gt < 1e-12:
    raise ValueError('Malha GT degenerada')
scale = 1.0 / diagonal_gt
gt.apply_scale(scale)
rm.apply_scale(scale)
```

## Passo 3 — Validar o comportamento

Valide com duas cópias idênticas de um STL: após normalizar, as coordenadas devem continuar coincidentes. Não normalize cada malha por sua própria diagonal: isso apagaria diferenças de tamanho antes da avaliação.

## Passo 4 — Próxima etapa

Continue para [04 — Conferir a correspondência e o ICP](04-alinhamento-icp.md).

**Código de referência:** carregamento em [`common/io.py`](../../../src/meshcomparison/common/io.py), transformação em [`common/transforms.py`](../../../src/meshcomparison/common/transforms.py), normalização no [pipeline geométrico](../../../src/meshcomparison/geometry/pipeline.py) e no [pipeline perceptual](../../../src/meshcomparison/perceptual/pipeline.py).
