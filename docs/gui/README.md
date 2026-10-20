# Interface desktop — PySide6 + PyVistaQt

> **Estado:** interface implementada nos módulos `src/meshcomparison/gui/`. Este guia descreve o código disponível; **não** representa um teste executado da janela num computador local.

A GUI permite escolher a **malha de referência (GT)** e a **malha reconstruída (RM)**, selecionar os pipelines, visualizar modelos 3D e consultar os resultados CSV/PNG. A aplicação usa **PySide6**, **PyVista + PyVistaQt (VTK)** e executa cada pipeline em um processo filho separado por `QProcess`. A janela inicia maximizada, mantendo visíveis a barra de título do Windows e a barra de tarefas.

## 1. Instalar e abrir

No Windows, abra o **Anaconda Prompt** na pasta do projeto (a pasta que contém `pyproject.toml`). Se ainda não tiver o ambiente, crie-o uma vez:

```bat
conda env create -f environments/environment.yml
```

Ative o ambiente e instale o projeto:

```bat
conda activate meshEval
python -m pip install -e . --no-deps
```

Se aparecer `prefix already exists`, o ambiente já existe: pule a criação e execute os dois comandos acima. O arquivo `environment.yml` inclui os pacotes da interface. Como `--no-deps` não instala dependências, um ambiente antigo pode precisar dos pacotes gráficos:

```bat
python -m pip install PySide6 pyvista pyvistaqt
```

Abra a interface:

```bat
mesh-gui
```

Se `mesh-gui` não for reconhecido, use `python -m meshcomparison.gui`. Se aparecer `No module named 'PySide6'`, instale os pacotes gráficos com o comando acima. A interface precisa de uma sessão desktop; não abre em um terminal sem ambiente gráfico.

## 2. Escolher arquivos e formatos

Na lateral **Meshes**, selecione GT e RM, e escolha a pasta de saída. A interface anuncia **STL, OBJ, PLY, OFF, GLB/GLTF**. O carregamento usa [`trimesh`](../../src/meshcomparison/common/io.py), que aceita formatos conforme a versão e as dependências instaladas; **nem todo arquivo com uma dessas extensões é garantido**. Teste com malhas válidas.

**FBX não é suportado diretamente.** Converta para STL, OBJ ou PLY (ou outro formato testado) antes de executar. A GUI também valida existência dos caminhos, a seleção de pelo menos um pipeline e algumas opções numéricas.

Os arquivos de demonstração são [`data/samples/gt.stl`](../../data/samples/gt.stl) e [`data/samples/mod.stl`](../../data/samples/mod.stl). Escolha **uma pasta de saída nova** ao comparar experimentos; a ferramenta pode sobrescrever arquivos com nomes iguais.

## 3. Executar as análises

| Controle | Função |
| --- | --- |
| **Geometric** | Chamfer, Hausdorff, RMSE, renderizações e heatmap |
| **Perceptual** | LPIPS, PSNR e SSIM em várias vistas |
| **MSE threshold (ICP)** | Limiar normalizado que decide se o alinhamento ICP é acionado (fixo: 1e-4) |
| **Azimuth / Elevation** | Orientação de câmera (azimute para o pipeline geométrico; elevação) (fixos: -135° / 25,264°) |
| **Render width / height** | Resolução das imagens geradas (fixos: 1600 × 1200) |
| **Views (perceptual)** | Número de perspectivas avaliadas (fixo: 100) |
| **Camera margin / radius factor** | Enquadramento da câmera perceptual (fixos: 1,05 / 1,45) |
| **Compute device (LPIPS)** | `auto` prefere CUDA se PyTorch disponibilizar, `cuda` exige CUDA, `cpu` força CPU |

Os parâmetros acima são **somente leitura** na interface e usam os valores configurados em [`RunConfig`](../../src/meshcomparison/gui/config.py). Para usar outros valores, chame `run_pipeline` dos módulos `geometry` e `perceptual` em código Python (veja o [README](../../README.md#parameters)).

Clique em **Run evaluation**. A aba *Log* mostra a saída dos processos e a interface apresenta a estimativa de progresso. Ao terminar com sucesso, a interface abre a aba **3D view** com o heatmap selecionado quando disponível; use os controles de camadas para alternar GT e RM alinhada. Tabelas e imagens ficam na aba **Results**. **Cancel** encerra a execução em andamento; podem permanecer arquivos parciais na pasta de saída. Selecionar ambos os pipelines significa duas execuções sequenciais, não avaliação distribuída/paralela.

### GPU e CUDA

Somente a parte de inferência de **LPIPS** escolhe CPU/CUDA. A GPU **não** acelera automaticamente o pipeline geométrico nem transforma o renderer OpenGL em um pipeline CUDA. A interface detecta a configuração de PyTorch ao abrir e exibe avisos; se houver GPU NVIDIA com PyTorch só de CPU, aparece o botão **Copy CUDA install command**, que copia os comandos de reinstalação. Testes com *mock* de GPU não comprovam execução CUDA num notebook real.

Para conferir a instalação:

```bat
python -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available())"
```

Consulte o [seletor oficial do PyTorch](https://pytorch.org/get-started/locally/) para a instalação compatível com o driver; evite copiar um índice de CUDA sem verificar suporte.

## 4. Visualizar os modelos e resultados

Na aba **3D view**, o [`MeshViewer`](../../src/meshcomparison/gui/viewer3d.py) disponibiliza:

- Um cubo maciço de referência, pequeno e centralizado sobre o plano, enquanto GT e RM ainda não foram carregadas.
- Camadas independentes para **GT**, **RM alinhada** e **heatmap de desvio** (quando disponível).
- Rotação, pan e zoom da câmera, com opção **Reset view**. A vista inicial usa a mesma direção dos renders da avaliação (eixo Z para cima, azimute -135°, elevação 25,264°); a elevação interativa fica limitada a 8°–78° para manter o plano abaixo do objeto e evitar que a câmera vire.
- **Legenda de distância** à direita quando o heatmap está visível: escala de 0 até o percentil 95 das distâncias GT→RM, em unidades da malha GT (calculada pela janela a partir da GT e da RM alinhada salvas; os pipelines não gravam esse valor). Distâncias acima desse valor aparecem no vermelho máximo.
- Heatmap com o mesmo aspecto do PNG do pipeline (cores mais claras, tons rosa/ciano causados pela iluminação forte do renderizador). Como esses tons **não** existem na paleta `RdYlGn_r` da legenda, a caixa **Exact palette** mostra as cores fiéis à legenda.
- Controle da opacidade da RM e alternância de linhas das arestas (**Edges**).
- **Save image…** para salvar uma captura PNG do viewer.
- Sobreposição de camadas no mesmo viewer. **Não há, no código atual, três viewports independentes com câmeras sincronizadas**; não confundir com visualização lado a lado.

A aba **Results** usa [`ResultsView`](../../src/meshcomparison/gui/results_view.py) para mostrar, em abas, o **resumo perceptual** (`metrics_perceptual.csv`) e a galeria de PNGs. Os demais CSVs (`metrics_geometry.csv`, `per_view_metrics.csv` e `run_metadata.csv`) continuam sendo gravados na pasta de saída, mas não têm aba própria. Na aba **Images** as imagens aparecem **em pares**, GT à esquerda e RM alinhada à direita, fotografadas no mesmo ângulo: a vista geométrica, o heatmap (imagem única) e cada vista perceptual salva. O seletor **All**, padrão, mostra todos os pares um abaixo do outro (com rolagem); escolher uma entrada mostra só aquele par. O botão **Open output folder** abre a pasta de saída. A aba **Log** mostra a execução. O tema é restaurado das configurações do aplicativo e usa o escuro por padrão; a interface atual não tem um menu para alterná-lo.

### Saídas esperadas

```text
output/
├── aligned/rm_aligned.ply
├── heatmaps/gt_heatmap_colored.ply
├── heatmaps/gt_heatmap_ortho.png
├── metrics/metrics_geometry.csv
├── metrics/metrics_perceptual.csv
├── metrics/per_view_metrics.csv
├── metrics/run_metadata.csv
└── renders/
    ├── gt_ortho.png
    ├── rm_aligned_ortho.png
    ├── gt/
    ├── rm/
    └── pairs/
```

Algumas pastas só aparecem quando o respectivo pipeline é executado. Ambos os pipelines podem gravar `aligned/rm_aligned.ply` no **mesmo diretório**; use pastas separadas quando precisar preservar resultados distintos. Os exemplos commitados estão em [`examples/output/`](../../examples/output/), e não são atualizados pela GUI automaticamente.

## 5. Limites e testes

O projeto já tem [testes de lógica Qt-free](../../tests/test_gui_config.py) para validação, construção de comandos e progresso, mas **ainda é necessário comprovar manualmente ou automatizar** a inicialização da janela, interação 3D, cancelamento, carregamento real de arquivos e aplicação do tema escuro padrão em sistemas suportados.

Checklist de validação:

- [ ] A interface abre e carrega GT/RM de exemplo num sistema com Qt/VTK.
- [ ] Preview 3D, opacidade, arestas, câmera e screenshot funcionam.
- [ ] Cada pipeline executa e permite visualizar suas saídas.
- [ ] Um cancelamento intencional não corrompe entradas nem resultados de referência.
- [ ] Erros de entrada e de renderização são reportados sem sucesso falso.
- [ ] O status da GPU/CPU observado bate com `torch.cuda.is_available()`.

Consulte a [instalação](../implementation/step-by-step/01-preparacao-ambiente.md), o [roteiro completo de validação no Windows](../../README.md#validate-on-windows) (incluindo CUDA e comparação com os CSVs de exemplo), os [testes pendentes](../implementation/step-by-step/10-limitacoes-evolucao.md) e o [README do projeto](../../README.md).
