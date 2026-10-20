# Mesh Comparison — implementar, entender e evoluir o projeto

Este guia descreve a arquitetura atual em `src/meshcomparison/`. O fluxo geométrico está em [`geometry/pipeline.py`](../../src/meshcomparison/geometry/pipeline.py) e o perceptual em [`perceptual/pipeline.py`](../../src/meshcomparison/perceptual/pipeline.py). Ambos reutilizam o preparo compartilhado em [`common/prepare.py`](../../src/meshcomparison/common/prepare.py), que carrega as entradas, normaliza as duas malhas usando a diagonal da caixa da GT, calcula o MSE pré-alinhamento e chama ICP de similaridade apenas quando esse MSE excede o limiar. A interface desktop fica em [`gui/`](../../src/meshcomparison/gui/); `gui/runner.py` inicia um processo filho por pipeline via `gui/worker.py`. Se ambos forem selecionados, os processos rodam em sequência. A API Python também pode chamar cada `run_pipeline(...)` diretamente.

![Arquitetura modular](images/architecture.svg)

## Estado das etapas

O marcador **[x]** significa que o componente de código/documentação existe — **não** que os testes estejam completos ou que todos os ambientes tenham sido validados.

1. [x] [Preparação do ambiente e instalação do pacote](step-by-step/01-preparacao-ambiente.md) — comandos documentados; execução histórica CPU registrada, versão atual requer confirmação no seu ambiente.
2. [x] [Arquitetura modular, interface e diretórios](step-by-step/02-arquitetura-implementacao.md) — pacotes `common/`, `geometry/`, `perceptual/` e `gui/`.
3. [x] [Carregamento e normalização das malhas](step-by-step/03-malhas-normalizacao.md).
4. [x] [Correspondência e ICP condicional](step-by-step/04-alinhamento-icp.md).
5. [x] [MSE e RMSE](step-by-step/05-mse-rmse.md).
6. [x] [Chamfer e Hausdorff](step-by-step/06-chamfer-hausdorff.md).
7. [x] [Câmera, renderização e heatmap](step-by-step/07-renderizacao-heatmaps.md).
8. [x] [Multivistas, LPIPS, PSNR e SSIM](step-by-step/08-metricas-perceptuais.md).
9. [x] [CSVs, PLY e resultados](step-by-step/09-relatorios-validacao.md).
10. [ ] [Validação sistemática e evolução](step-by-step/10-limitacoes-evolucao.md) — **parcial:** testes unitários existem, mas faltam regressões integradas e cenários geométricos diversificados.

## Componentes adicionais da branch atual

- **[GUI PySide6/PyVistaQt](../gui/README.md):** visualização 3D, controles de camadas, resumo perceptual, galeria, dispositivos CPU/CUDA para LPIPS e execução/cancelamento dos pipelines em processos filhos sequenciais. A GUI exibe `metrics_perceptual.csv` e as imagens; os CSVs geométricos, por vista e metadados permanecem disponíveis na pasta de saída. A existência no código não implica testes de interface gráfica completos.
- **[Empacotamento](../../pyproject.toml):** o comando `mesh-gui` (ou `python -m meshcomparison.gui`) abre a interface, que executa os pipelines em processos filhos (`meshcomparison.gui.worker`).
- **[Harness](../harness/README.md):** orientações para construir novos projetos já preparados para agentes e para evoluir este sem substituir implementações existentes.

## Prática recomendada

Use [`environments/environment.yml`](../../environments/environment.yml) para criar o ambiente `meshEval` e depois rode `python -m pip install -e . --no-deps` na raiz. O [snapshot Windows](../../environments/environment-lock.yml) não contém PySide6, PyVista ou PyVistaQt; instale esses extras para usar a GUI nesse ambiente.

Os exemplos didáticos nas etapas não necessariamente são módulos completos executáveis isoladamente; compare com o código real em `src/meshcomparison/` antes de reutilizá-los. **GT** é a referência e **RM** é a reconstrução. As métricas geométricas comparam vizinhos mais próximos entre vértices; o ICP pode corrigir escala uniforme. Registre modificações de algoritmo, câmera e métricas antes de comparar resultados históricos.
