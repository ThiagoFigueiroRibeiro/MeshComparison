# Documentação — Mesh Comparison

Esta é a navegação da documentação para a versão atual do projeto, organizado como pacote Python em `src/meshcomparison/`. Os exemplos de resultados são um registro histórico; mudanças na estrutura do projeto não equivalem a uma nova execução validada. A pasta [`archived/`](archived/README-v1.md) guarda READMEs de versões anteriores e não deve ser usada como instrução de instalação ou execução.

| Área | Conteúdo | Quando consultar |
| --- | --- | --- |
| [Avaliação de malhas 3D](avaliacao-geometrica/README.md) | Conceitos, métricas geométricas e perceptuais, aplicações e limitações | Antes de interpretar métricas |
| [Implementação e evolução](implementation/README.md) | Estrutura modular, fluxo dos pipelines e tutoriais passo a passo | Ao estudar ou alterar o código |
| [Interface desktop](gui/README.md) | Instalação, execução e controles da GUI PySide6/PyVistaQt | Para inspecionar GT, RM, heatmap e relatórios |
| [Resultados de exemplo](results/README.md) | Métricas e imagens de uma execução previamente registrada | Para consultar um conjunto específico de resultados |
| [Referências e chamadas](REFERENCES/README.md) | Artigos de pesquisa e chamadas de conferências | Para consultar fontes e oportunidades de publicação |
| [Agent Harness](harness/README.md) | Estado do desenvolvimento assistido por agentes, guardrails e roteiro reutilizável | Para organizar futuras implementações via LLM |
| [Referências sobre Harness](harness/REFERENCIAS.md) | Fontes oficiais e materiais complementares | Para fundamentar decisões e arquitetura |

## Arquitetura atual

```mermaid
flowchart LR
    GT["Malha de referência (GT)"] --> INPUTS["Entradas e configuração"]
    RM["Malha reconstruída (RM)"] --> INPUTS
    GUI["Interface desktop PySide6"] --> RUNNER["QProcess e worker por pipeline"]
    API["API Python: run_pipeline"] --> GEO["Pipeline geométrico"]
    API --> PER["Pipeline perceptual"]
    RUNNER --> GEO
    RUNNER --> PER
    INPUTS --> GEO
    INPUTS --> PER
    GEO --> GEOPREP["Preparação das malhas: normalização e ICP condicional"]
    PER --> PERPREP["Preparação das malhas: normalização e ICP condicional"]
    GEOPREP --> GEOM["Chamfer, Hausdorff, RMSE e mapa de calor"]
    PERPREP --> PERCEPT["Renderizações multivista: LPIPS, PSNR e SSIM"]
    GEOM --> OUT["Resultados: CSV, PLY e PNG"]
    PERCEPT --> OUT
    OUT --> VIEW["GUI: visualizador 3D, galeria e resultados"]
```

Na GUI, os pipelines selecionados são executados em processos filhos sequencialmente; a API Python chama os mesmos módulos diretamente. Consulte o [guia de implementação](implementation/README.md) para detalhes técnicos e o [guia desktop](gui/README.md) para operar a interface.

## Entrada rápida para a versão atual

O pacote em `src/meshcomparison/` está dividido em:

- **`common/`** — carregamento de malhas, preparo compartilhado em `prepare.py` (normalização, MSE, ICP e exportação), transformações, distâncias, renderização e escolha do dispositivo para LPIPS.
- **`geometry/`** — métricas geométricas, heatmap e pipeline.
- **`perceptual/`** — câmeras, imagens, LPIPS/PSNR/SSIM e pipeline multivista.
- **`gui/`** — interface Qt com módulos separados para janela, painéis, configuração, supervisão (`runner.py`), processo filho (`worker.py`), carregamento das saídas e visualizador PyVistaQt.

Depois de preparar `meshEval` e instalar o pacote em modo editável, abra a interface para executar as avaliações:

```bash
python -m meshcomparison.gui
```

O comando inicia uma **janela desktop** e requer PySide6, PyVista, PyVistaQt e um ambiente com interface gráfica. Veja a [instalação detalhada](implementation/step-by-step/01-preparacao-ambiente.md). O CI atual executa `ruff check .`, `pytest -q` e uma verificação de importação dos pipelines e do worker; ele não testa a janela interativa nem executa os pipelines completos com renderização.

**Convenção de status:** “implementado no código” não significa “validado em todos os ambientes”. Recursos de GUI, GPU e renderização gráfica precisam de testes próprios antes de se declarar suporte comprovado.

**Para validar no Windows:** siga a seção [Validate on Windows](../README.md#validate-on-windows) do README inicial para CUDA/PyTorch, `mesh-gui` e comparação dos CSVs dos dois pipelines. Utilize diretórios separados para as saídas de cada pipeline.
