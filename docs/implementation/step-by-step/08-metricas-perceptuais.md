# 08 — Conferir as vistas e métricas LPIPS, PSNR e SSIM

> **Status: concluída.** O pipeline perceptual já renderiza múltiplas vistas e calcula LPIPS, PSNR e SSIM.

![Esquema da etapa](../images/multiview.svg)

## Passo 1 — Conferir o fluxo multivista existente

O pipeline perceptual (`src/meshcomparison/perceptual/`) já reutiliza o carregamento, a normalização e o alinhamento das etapas 03 e 04. Para cada azimute, crie uma câmera ortográfica comum, renderize GT e RM em RGBA, forme máscaras pelo canal alfa e recorte a união das silhuetas. Por padrão, percorra 100 vistas.

## Passo 2 — Trecho da implementação atual

```python
# Resume as mesmas etapas de mascaramento e métricas usadas no pipeline perceptual
import numpy as np
import lpips
from meshcomparison.common.device import get_device_info
from meshcomparison.perceptual.image_metrics import (
    rgba_to_rgb_mask, crop_to_union_mask,
    masked_psnr, masked_ssim, masked_lpips,
)

# gt_rgba e rm_rgba são as imagens RGBA renderizadas anteriormente
# com a mesma câmera; a rede é criada uma vez antes do loop de vistas.
device = get_device_info('auto').device
model = lpips.LPIPS(net='alex').to(device).eval()
gt_img, _, gt_mask = rgba_to_rgb_mask(gt_rgba)
rm_img, _, rm_mask = rgba_to_rgb_mask(rm_rgba)
gt_crop, rm_crop, _, _, union = crop_to_union_mask(
    gt_img, rm_img, gt_mask, rm_mask, pad=12
)
gt_masked = gt_crop * union[..., None].astype(np.float32)
rm_masked = rm_crop * union[..., None].astype(np.float32)
psnr = masked_psnr(gt_crop, rm_crop, union)
ssim = masked_ssim(gt_masked, rm_masked)
lpips_value = masked_lpips(model, gt_masked, rm_masked, device)
```

Este é um **recorte do fluxo**, não um script independente: `gt_rgba` e `rm_rgba` vêm da etapa de renderização. O pipeline completo inicializa o modelo LPIPS uma única vez, antes de iterar pelas vistas. Consulte as funções reais em [`perceptual/image_metrics.py`](../../../src/meshcomparison/perceptual/image_metrics.py) e [`perceptual/pipeline.py`](../../../src/meshcomparison/perceptual/pipeline.py).

## Passo 3 — Entender as métricas e validar

O pipeline implementa PSNR como `10 log10(1/MSE_imagem)` para pixels em `[0,1]`, com tratamento de erro zero. Para reproduzir **exatamente** os resultados atuais, consulte `masked_psnr` do módulo: o denominador conta pixels mascarados, enquanto o numerador soma os três canais, diferente da média RGB convencional. SSIM e LPIPS atuais recebem recortes cujo fundo foi zerado, **não** uma máscara aplicada diretamente à função de SSIM/LPIPS. Por padrão, são salvas imagens das vistas 1, 33 e 66 quando se avaliam 100 vistas. O argumento Python `device="auto"`, `device="cpu"` ou `device="cuda"` controla apenas a inferência de LPIPS, não o renderizador. Para comparar com os CSVs históricos, use o [roteiro de validação no Windows](../../../README.md#validate-on-windows) e mantenha número de vistas, resolução, câmera e demais parâmetros consistentes.

Na interface, os parâmetros ficam somente para leitura e seguem os valores de `RunConfig`. Para testar outro número de vistas, passe `num_views` diretamente à função `run_pipeline` em código Python. O log mostra esse total, e as linhas de `metrics/per_view_metrics.csv` registram uma linha por vista processada.

## Passo 4 — Próxima etapa

Continue para [09 — Conferir os resultados exportados](09-relatorios-validacao.md).
