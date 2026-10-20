# 03 — Importar e normalizar duas malhas

> **Status: concluída.** O carregamento e a normalização compartilhada pela GT já estão implementados nos dois pipelines.

![Esquema da etapa](../images/pipeline.svg)

## Passo 1 — Conferir o carregamento existente

Confira `load_mesh(path)`, implementada usando `trimesh.load(path, force='scene', process=False, maintain_order=True)`. Se o retorno for uma cena, percorra as instâncias e aplique as transformações do grafo antes de concatenar as geometrias. Remova vértices não referenciados e rejeite `.fbx` explicitamente.

## Passo 2 — Trecho da implementação atual

```python
# Demonstra a normalização compartilhada usando as malhas de exemplo do repositório
import numpy as np
from meshcomparison.common.io import load_mesh

gt = load_mesh('data/samples/gt.stl')
rm = load_mesh('data/samples/mod.stl')
diagonal_gt = np.linalg.norm(gt.bounds[1] - gt.bounds[0])
if diagonal_gt < 1e-12:
    raise ValueError('Malha GT degenerada')
internal_scale = 1.0 / diagonal_gt
gt.apply_scale(internal_scale)
rm.apply_scale(internal_scale)
```

O trecho acima ilustra a lógica do [pipeline real](../../../src/meshcomparison/geometry/pipeline.py). Ele pressupõe que o pacote foi instalado (`python -m pip install -e . --no-deps`) e que o terminal está na raiz do repositório. A exportação da malha alinhada recupera posteriormente a escala original da GT.

## Passo 3 — Validar o comportamento

Valide com duas cópias idênticas de um STL: após normalizar, as coordenadas devem continuar coincidentes. Não normalize cada malha por sua própria diagonal: isso apagaria diferenças de tamanho antes da avaliação.

## Passo 4 — Próxima etapa

Continue para [04 — Conferir a correspondência e o ICP](04-alinhamento-icp.md).
