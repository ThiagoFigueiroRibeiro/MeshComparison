# 02 — Arquitetura atual, interface e diretórios de saída

> **Status: implementado no código.** A branch atual organiza processamento e GUI em um pacote Python, não em scripts independentes na raiz.

![Arquitetura modular da interface, dos processos filhos e dos pipelines](../images/architecture.svg)

## Passo 1 — Identificar os módulos reais

| Local | Função |
| --- | --- |
| [`common/io.py`](../../../src/meshcomparison/common/io.py) | Carrega malhas com Trimesh e cria pastas de saída |
| [`common/prepare.py`](../../../src/meshcomparison/common/prepare.py) | Preparo compartilhado: carrega, normaliza, mede MSE, alinha condicionalmente com ICP e exporta a RM alinhada |
| [`common/alignment.py`](../../../src/meshcomparison/common/alignment.py) | ICP com escala uniforme via Open3D |
| [`common/device.py`](../../../src/meshcomparison/common/device.py) | Detecta e seleciona CPU/CUDA para LPIPS |
| [`geometry/pipeline.py`](../../../src/meshcomparison/geometry/pipeline.py) | Métricas geométricas, renders ortográficos, heatmap e relatórios |
| [`perceptual/pipeline.py`](../../../src/meshcomparison/perceptual/pipeline.py) | Renderização multivista, LPIPS/PSNR/SSIM e relatórios |
| [`gui/config.py`](../../../src/meshcomparison/gui/config.py) | Valida arquivos, mantém `RunConfig` e prepara dados serializados da execução |
| [`gui/panels.py`](../../../src/meshcomparison/gui/panels.py) | Componentes do painel lateral: arquivos, pipelines, parâmetros e dispositivo |
| [`gui/runner.py`](../../../src/meshcomparison/gui/runner.py) e [`gui/worker.py`](../../../src/meshcomparison/gui/worker.py) | Executa cada pipeline sequencialmente em processo filho cancelável; o worker lê a configuração JSON pela entrada padrão |
| [`gui/outputs.py`](../../../src/meshcomparison/gui/outputs.py) | Carrega GT, RM alinhada e heatmap para o viewer 3D |
| [`gui/main_window.py`](../../../src/meshcomparison/gui/main_window.py) | Monta janela, abas, conexão dos painéis, execução e visualização de resultados |

As dependências e os comandos registrados pelo pacote estão em [`pyproject.toml`](../../../pyproject.toml).

## Passo 2 — Entender o código de preparação das saídas

Os módulos chamam a função **`ensure_dirs(base_out, subdirs)`**, compartilhada em `common/io.py`, com conjuntos diferentes de subpastas conforme o pipeline. Este exemplo é didático, mas corresponde à assinatura usada:

```python
# Demonstra como o módulo compartilhado cria diretórios de saída
from meshcomparison.common.io import ensure_dirs

paths = ensure_dirs("output", {
    "renders": ("renders",),
    "metrics": ("metrics",),
    "aligned": ("aligned",),
    "heatmaps": ("heatmaps",),
})
```

O pipeline perceptual também cria `renders/gt`, `renders/rm` e `renders/pairs`. O diretório de saída é o escolhido na interface (parâmetro `out_dir` de `run_pipeline`) e **não é fixo no código**.

## Passo 3 — Instalar o pacote e abrir a interface

```bat
conda activate meshEval
python -m pip install -e . --no-deps
python -m meshcomparison.gui
```

Etapas comuns aos dois pipelines (carregar, normalizar, MSE, ICP e exportar a RM alinhada) ficam em [`common/prepare.py`](../../../src/meshcomparison/common/prepare.py). Consulte o [README principal](../../../README.md) para iniciar a interface ou chamar os pipelines em Python.

## Passo 4 — Distinguir processamento e interface

A GUI usa [`config.py`](../../../src/meshcomparison/gui/config.py) para validar entradas e montar `RunConfig`, [`runner.py`](../../../src/meshcomparison/gui/runner.py) para iniciar e supervisionar processos filhos e [`worker.py`](../../../src/meshcomparison/gui/worker.py) como ponto de entrada interno desses processos. O runner envia a configuração serializada em JSON pela entrada padrão do worker, que despacha a função `run_pipeline` selecionada. Os componentes de interface ficam em [`panels.py`](../../../src/meshcomparison/gui/panels.py); [`outputs.py`](../../../src/meshcomparison/gui/outputs.py) carrega as malhas salvas para o viewer; [`viewer3d.py`](../../../src/meshcomparison/gui/viewer3d.py) mostra a visualização 3D e [`results_view.py`](../../../src/meshcomparison/gui/results_view.py) exibe as tabelas e imagens. Os pipelines compartilham o preparo em `common/prepare.py`, mas mantêm métricas e relatórios específicos em `geometry/` e `perceptual/`.

As malhas de demonstração ficam em `data/samples/`. Os resultados locais padrão ficam em `output/`; os exemplos versionados em `examples/output/` são **um registro histórico**.

**Próximo passo:** [03 — Carregamento e normalização](03-malhas-normalizacao.md) · [Guia desktop](../../gui/README.md).
