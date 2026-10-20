# 07 — Conferir câmera compartilhada, renders e heatmap

> **Status: concluída.** A câmera compartilhada, os renders e a exportação do heatmap já estão implementados no pipeline geométrico.

![Esquema da etapa](../images/distancias.svg)

## Passo 1 — Conferir a câmera compartilhada

As funções `look_at`, `bounds_corners` e `build_shared_camera` já estão implementadas. Elas calculam uma câmera ortográfica a partir da caixa envolvente conjunta GT+RM; o pipeline usa `pyrender.Scene`, `OrthographicCamera` e `OffscreenRenderer` para salvar as duas vistas com o mesmo enquadramento.

## Passo 2 — Trecho da implementação atual

```python
# Associa a cada vértice GT uma cor proporcional à distância até a RM
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

def colorize_gt_heatmap(gt_mesh, d_gt2rm):
    colored = gt_mesh.copy()
    vmax = max(float(np.nanpercentile(d_gt2rm, 95)), 1e-12)
    norm = mpl.colors.Normalize(vmin=0, vmax=vmax)
    cmap = plt.get_cmap('RdYlGn_r')
    colored.visual.vertex_colors = (cmap(norm(d_gt2rm)) * 255).astype(np.uint8)
    return colored, norm, cmap
```

## Passo 3 — Conferir os arquivos gerados

O pipeline já gera `gt_ortho.png`, `rm_aligned_ortho.png`, `gt_heatmap_ortho.png` e `gt_heatmap_colored.ply`, incluindo a barra de cores. Observe que as cores representam somente GT→RM, não a distância simétrica.

## Passo 4 — Próxima etapa

Continue para [08 — Conferir as vistas e métricas perceptuais](08-metricas-perceptuais.md).

**Código de referência:** [renderização](../../../src/meshcomparison/geometry/rendering.py) e [heatmap](../../../src/meshcomparison/geometry/heatmap.py).
