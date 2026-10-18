# Mesh Comparison — arquitetura, implementação e evolução

O projeto é distribuído como pacote Python `meshcomparison`, instalado a partir de `pyproject.toml`. Os pontos de entrada ficam em `src/meshcomparison/geometry/` e `src/meshcomparison/perceptual/`; operações reutilizadas pelos dois fluxos ficam em `src/meshcomparison/common/`. Os lançadores em `scripts/` chamam esses módulos, e não mantêm implementações próprias dos pipelines.

Os pipelines geométrico e perceptual já estão implementados em [`src/meshcomparison/geometry/pipeline.py`](../../src/meshcomparison/geometry/pipeline.py) e [`src/meshcomparison/perceptual/pipeline.py`](../../src/meshcomparison/perceptual/pipeline.py). Use as etapas para entender e executar o código atual, validar seu comportamento e desenvolver melhorias sem duplicar os recursos existentes.

![Visão geral](images/pipeline.svg)

## Status das etapas

1. [x] [Preparar o ambiente](step-by-step/01-preparacao-ambiente.md) — pacote instalado, pipelines executados, versões fixadas em `environments/environment-lock.yml`; ambiente CPU-only, sem CUDA.
2. [x] [Programas, CLI e diretórios](step-by-step/02-arquitetura-implementacao.md)
3. [x] [Carregamento e normalização das malhas](step-by-step/03-malhas-normalizacao.md)
4. [x] [Correspondência e alinhamento ICP](step-by-step/04-alinhamento-icp.md)
5. [x] [MSE e RMSE](step-by-step/05-mse-rmse.md)
6. [x] [Chamfer e Hausdorff](step-by-step/06-chamfer-hausdorff.md)
7. [x] [Câmera, renders e heatmap](step-by-step/07-renderizacao-heatmaps.md)
8. [x] [Renderização multivista, LPIPS, PSNR e SSIM](step-by-step/08-metricas-perceptuais.md)
9. [x] [CSVs, exportação PLY e execução](step-by-step/09-relatorios-validacao.md)
10. [ ] [Validação sistemática e evolução](step-by-step/10-limitacoes-evolucao.md) — plano de testes e melhorias futuras.

**Como ler os passos:** os trechos de código são exemplos didáticos; a implementação de referência está nos módulos indicados em cada etapa. Nas etapas concluídas, confira e execute o código existente; não crie uma segunda cópia dos recursos. A etapa 10 reúne validações sistemáticas pendentes e evoluções propostas.

**Convenção:** GT é a malha de referência; RM é a malha avaliada. As métricas geométricas atuais calculam vizinhos mais próximos entre vértices. O ICP atual pode corrigir escala; leve isso em conta ao interpretar diferenças dimensionais.
