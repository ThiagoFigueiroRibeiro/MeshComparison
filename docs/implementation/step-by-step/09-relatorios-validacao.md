# 09 — Conferir os resultados exportados

> **Status: concluída.** Os pipelines do pacote já exportam métricas, metadados, renders e a malha alinhada.

![Esquema da etapa](../images/pipeline.svg)

## Passo 1 — Conferir os resultados exportados

Depois de calcular as métricas, o pipeline geométrico grava `output/metrics/metrics_geometry.csv`. O fluxo perceptual grava uma linha por vista em `output/metrics/per_view_metrics.csv` e estatísticas de mínimo, máximo, percentis 25/75, mediana e média em `output/metrics/metrics_perceptual.csv`. Ele também gera `output/metrics/run_metadata.csv`.

## Passo 2 — Exemplo de estrutura dos resultados

```python
# Exporta métricas e devolve a malha alinhada à unidade de entrada
import pandas as pd

pd.DataFrame([{
    'chamfer_mean_normalized': metrics['chamfer_mean'],
    'hausdorff_normalized': metrics['hausdorff'],
    'rmse_normalized': metrics['rmse'],
}]).to_csv('output/metrics/metrics_geometry.csv', index=False)
rm_export = rm_aligned.copy()
rm_export.apply_scale(diagonal_gt)
rm_export.export('output/aligned/rm_aligned.ply')
```

## Passo 3 — Executar e conferir

Os pipelines usam `common/io.py` para criar os diretórios, incluem os campos de métricas e convertem distâncias normalizadas para as unidades da GT; MSE é convertido com `diagonal_gt²`. Execute os dois módulos e confira os CSVs, PNGs e PLYs. Atenção: ambos gravam `rm_aligned.ply` no mesmo caminho e podem sobrescrevê-lo.

## Passo 4 — Próxima etapa

Continue para [10 — Planejar a validação e a evolução](10-limitacoes-evolucao.md).

**Código de referência:** [I/O e criação de diretórios](../../../src/meshcomparison/common/io.py), [exportação geométrica](../../../src/meshcomparison/geometry/pipeline.py) e [exportação perceptual](../../../src/meshcomparison/perceptual/pipeline.py).
