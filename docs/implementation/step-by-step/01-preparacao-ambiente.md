# 01 — Preparar o ambiente e instalar o pacote Python

> **Situação:** a documentação registra uma execução anterior dos pipelines no Windows com PyTorch CPU-only. A branch atual usa um **pacote `src/meshcomparison/` e uma GUI opcional**; a execução completa da nova estrutura não é comprovada apenas pelo registro antigo.

![Esquema da etapa](../images/pipeline.svg)

## Passo 1 — Requisitos e organização

Instale Conda/Miniconda, abra um terminal na **raiz do repositório** (onde fica `pyproject.toml`) e confirme que você está na branch de trabalho correta. Python **3.12** é a versão indicada em `environments/environment.yml`; a versão observada no snapshot Windows de 17/10/2026 foi **3.12.15**, não requisito de toda instalação.

Arquivos relevantes:

- [`environments/environment.yml`](../../../environments/environment.yml): ambiente geral para os pipelines, GUI e ferramentas de desenvolvimento.
- [`environments/environment-lock.yml`](../../../environments/environment-lock.yml): snapshot Windows CPU mais antigo; **não fixa as dependências da GUI**.
- [`environments/requirements-windows-cu128.txt`](../../../environments/requirements-windows-cu128.txt): snapshot pip separado para Windows, com pins da GUI e PyTorch CUDA 12.8; veja o [README principal](../../../README.md#installation) para instalá-lo num ambiente virtual novo.
- [`pyproject.toml`](../../../pyproject.toml): pacote Python, pontos de entrada e extras.

## Passo 2 — Criar e ativar o ambiente

Escolha **uma** opção. Para a branch atual, prefira a configuração geral:

```bat
conda env create -f environments/environment.yml
conda activate meshEval
python --version
```

Caso o ambiente `meshEval` já exista, **não** repita a criação; ative-o. Se quiser restaurar o registro histórico em um Windows compatível, pode utilizar `conda env create -f environments/environment-lock.yml` em um **novo ambiente** após ajustar o nome ou remover com segurança uma instalação antiga. Essa alternativa reproduz versões da época, não valida automaticamente o projeto refatorado, não é portátil para Linux/macOS e não traz PySide6/PyVista/PyVistaQt.

## Passo 3 — Instalar o próprio projeto (obrigatório)

Com `meshEval` ativo e na raiz:

```bat
python -m pip install -e . --no-deps
```

O modo editável disponibiliza os módulos `meshcomparison.*` e o comando `mesh-gui` (a interface). **Instalar só bibliotecas NumPy/Trimesh/Open3D via pip não instala o pacote local.** `--no-deps` pressupõe que as dependências necessárias já vieram do arquivo de ambiente.

Se você restaurou o snapshot antigo `environment-lock.yml` e pretende abrir a interface, instale separadamente:

```bat
python -m pip install PySide6 pyvista pyvistaqt
```

Na configuração geral essas três bibliotecas já estão declaradas. Sua disponibilidade e a abertura da janela ainda precisam ser testadas no computador.

## Passo 4 — Verificar importações e testes

```bat
python -c "import meshcomparison, trimesh, open3d, pyrender, numpy, pandas; print('Pacote e dependências principais importados')"
python -c "import meshcomparison.geometry.pipeline, meshcomparison.perceptual.pipeline, meshcomparison.gui.worker"
ruff check .
pytest -q
```

O último comando requer a suíte de testes do repositório. Se houver falha, anote o traceback e o ambiente; **não marque como concluído apenas porque o comando está documentado**.

## Passo 5 — Executar uma avaliação pequena

Abra a interface (`python -m meshcomparison.gui`), escolha `data/samples/gt.stl` (GT) e `data/samples/mod.stl` (RM), defina uma **pasta de saída nova** (por exemplo `output/check`) e clique em **Run evaluation**. Para uma execução rápida em código Python, sem a janela:

```python
from meshcomparison.perceptual.pipeline import run_pipeline

run_pipeline("data/samples/gt.stl", "data/samples/mod.stl", "output/perceptual-check", num_views=3, save_views=(1, 2, 3))
```

A avaliação perceptual pode demorar, baixar pesos do modelo LPIPS (quando ainda não estiverem em cache) e exigir suporte à renderização OpenGL offscreen. Uma execução com três vistas é **smoke test**, não reproduz os resultados históricos de 100 vistas (a interface usa sempre 100). Os diretórios em `output/` são locais e descartáveis; os exemplos versionados ficam em [`examples/output/`](../../../examples/output/).

## Passo 6 — Verificar a GUI e o dispositivo

```bat
python -m meshcomparison.gui
```

Isso requer sessão gráfica e PySide6, PyVista e PyVistaQt instalados. Para conferir **CUDA apenas para LPIPS**, rode:

```bat
python -c "import torch; print('torch:', torch.__version__, 'CUDA build:', torch.version.cuda, 'disponível:', torch.cuda.is_available())"
```

Se CUDA estiver indisponível, LPIPS pode rodar em CPU. Para instalar uma build de PyTorch compatível, selecione comando atualizado no [site oficial](https://pytorch.org/get-started/locally/), de acordo com sistema, Python e driver; não assuma que `pip install torch` sempre instala versão CPU-only. Consulte o [guia da GUI](../../gui/README.md).

## Estado e checklist de verificação

- [x] Arquivos de ambiente e `pyproject.toml` disponíveis no repositório.
- [x] Pipelines modularizados (executados pela interface) e testes configurados no CI.
- [x] Resultado histórico de execução CPU documentado em [resultados](../../results/README.md).
- [ ] Registrar execução limpa da **branch atual** com `pip install -e . --no-deps` e resultados de Ruff/pytest.
- [ ] Validar abertura e interação da GUI com modelos reais.
- [ ] Verificar execução perceptual em CUDA, se for objetivo, sem presumir suporte por haver GPU NVIDIA.
- [ ] Registrar informações de SO, commit e versões instaladas; atualizar o snapshot apenas depois de testes.

**Próximo passo:** [02 — Arquitetura modular e interface](02-arquitetura-implementacao.md). Também consulte o [guia de Harness](../../harness/README.md) para critérios de revisão e integração.
