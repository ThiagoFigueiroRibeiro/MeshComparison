# 09 — Conferir os resultados exportados

> **Status: concluída.** Os pipelines modulares exportam métricas, metadados, renders e a malha alinhada.

![Esquema da etapa](../images/pipeline.svg)

## Passo 1 — Conferir os resultados exportados

Depois de calcular as métricas, o pipeline geométrico grava `metrics/metrics_geometry.csv` dentro da pasta de saída selecionada na interface ou passada como `out_dir` à função Python. Esse CSV também contém os parâmetros geométricos, os valores de MSE antes/depois do alinhamento e os componentes da transformação. O fluxo perceptual grava uma linha por vista em `metrics/per_view_metrics.csv`, estatísticas de mínimo, máximo, percentis 25/75, mediana e média em `metrics/metrics_perceptual.csv`, e os parâmetros da execução em `metrics/run_metadata.csv`. Na GUI, a aba **Results** mostra o resumo perceptual e as imagens; os CSVs geométricos, por vista e de metadados ficam na pasta de saída, sem abas próprias.

## Passo 2 — Ler os resultados gerados pela versão atual

Depois de executar os dois pipelines pela interface, use os caminhos reais dos CSVs na pasta de saída selecionada. O roteiro de [validação no Windows](../../../README.md#validate-on-windows) mostra como gerar e comparar os resultados:

```python
# Lê e mostra os campos efetivamente exportados pelos dois pipelines
from pathlib import Path
import pandas as pd

base = Path('output/windows-validation')
geom = pd.read_csv(base / 'metrics/metrics_geometry.csv')
percep = pd.read_csv(base / 'metrics/metrics_perceptual.csv')
print(geom[['mean_chamfer_gt_units', 'symmetric_hausdorff_gt_units',
            'symmetric_rmse_gt_units']].to_string(index=False))
print(percep[['metric', 'median', 'mean']].to_string(index=False))
```

As colunas geométricas reais são, entre outras, `mean_chamfer_normalized`, `symmetric_hausdorff_normalized`, `symmetric_rmse_normalized` e os equivalentes com sufixo `_gt_units`. Os nomes antigos `chamfer_mean_normalized`, `hausdorff_normalized` e `rmse_normalized` do exemplo anterior **não são colunas emitidas por esta versão**. O alinhamento é exportado em `aligned/rm_aligned.ply`, reescalado para a unidade da GT.

## Passo 3 — Executar e conferir

Os pipelines criam os diretórios dentro da pasta de saída escolhida, incluem os campos de métricas e convertem distâncias normalizadas para as unidades da GT; MSE é convertido com o quadrado da diagonal da GT. Confira CSVs, PNGs e PLYs. **Ambos os pipelines gravam `aligned/rm_aligned.ply` na mesma pasta de saída**; quando os dois são executados na interface, o perceptual roda depois do geométrico e substitui esse arquivo. Use pastas de saída diferentes quando precisar preservar saídas distintas de cada pipeline. Os resultados de exemplo já versionados ficam em [`examples/output/`](../../../examples/output/), e não devem ser substituídos durante a verificação.

## Passo 4 — Próxima etapa

Continue para [10 — Planejar a validação e a evolução](10-limitacoes-evolucao.md).

**Código de referência:** [pipeline geométrico](../../../src/meshcomparison/geometry/pipeline.py) e [pipeline perceptual](../../../src/meshcomparison/perceptual/pipeline.py). As amostras acima mostram etapas de construção; consulte esses módulos e os utilitários compartilhados em `src/meshcomparison/common/` para ver as implementações completas.
