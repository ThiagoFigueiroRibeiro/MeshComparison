# 02 — Entender a arquitetura do pacote e as interfaces de linha de comando

> **Status: concluída.** Os dois pipelines, suas interfaces de linha de comando e a criação das pastas de saída já estão implementados.

![Esquema da etapa](../images/pipeline.svg)

## Passo 1 — Conferir a arquitetura existente

O projeto usa a estrutura `src/` e é configurado em `pyproject.toml`. A lógica está dividida por responsabilidade:

```text
src/meshcomparison/
├── common/       # I/O de malhas, transformações, distâncias, alinhamento e renderização
├── geometry/     # CLI, pipeline, métricas geométricas, renders e heatmap
└── perceptual/   # CLI, pipeline, câmeras, figuras e métricas de imagem
```

Cada fluxo tem um `cli.py` para argumentos e um `pipeline.py` para orquestração. `common/` concentra operações compartilhadas. `geometry/__main__.py` e `perceptual/__main__.py` permitem executar com `python -m`; os comandos `mesh-eval` e `percept-eval` são registrados como entry points no `pyproject.toml`. Os lançadores de `scripts/` apenas encaminham os argumentos para os módulos do pacote.

## Passo 2 — Como o fluxo é conectado

```python
# A CLI interpreta argumentos e delega a execução ao pipeline do pacote.
from .cli import main

main()
```

O código executável correspondente está em [`geometry/__main__.py`](../../../src/meshcomparison/geometry/__main__.py) e [`geometry/cli.py`](../../../src/meshcomparison/geometry/cli.py). A preparação das pastas compartilhada está em [`common/io.py`](../../../src/meshcomparison/common/io.py); o pipeline define quais subpastas cada fluxo usa.

## Passo 3 — Executar e conferir

Instale o pacote conforme a [etapa 01](01-preparacao-ambiente.md) e execute `python -m meshcomparison.geometry --gt data/samples/gt.stl --rm data/samples/mod.stl --out output`. Para a interface de console, use `mesh-eval --gt ... --rm ... --out ...`; o perceptual disponibiliza `python -m meshcomparison.perceptual` ou `percept-eval`. Confira os argumentos com `--help`.

## Passo 4 — Próxima etapa

Continue para [03 — Conferir o carregamento e a normalização das malhas](03-malhas-normalizacao.md).

**Código de referência:** [configuração e entry points](../../../pyproject.toml), [CLI geométrica](../../../src/meshcomparison/geometry/cli.py), [pipeline geométrico](../../../src/meshcomparison/geometry/pipeline.py), [CLI perceptual](../../../src/meshcomparison/perceptual/cli.py), [pipeline perceptual](../../../src/meshcomparison/perceptual/pipeline.py) e [utilitários compartilhados](../../../src/meshcomparison/common/).
