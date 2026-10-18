# 01 — Preparar o projeto e instalar as dependências

> **Status: concluída para execução em CPU.** Ambiente local criado, dependências importadas sem erro e os pipelines geométrico e perceptual executados com os arquivos de exemplo. O snapshot `environments/environment-lock.yml` registra as versões instaladas. O PyTorch deste ambiente é CPU-only; CUDA não está disponível.

Este passo prepara o ambiente para executar e validar os pipelines que já existem no repositório.

![Esquema da etapa](../images/pipeline.svg)

## Passo 1 — Preparar o ambiente do projeto existente

No Windows 64 bits, use o Miniconda3 e abra o **Anaconda Prompt** na raiz da cópia local do repositório. O ambiente registrado usa Conda **25.11.1**; essa é a versão observada, não um requisito obrigatório.

Execute cada bloco separadamente. Copie somente os comandos, sem URLs, textos explicativos ou o prefixo do terminal.

```bat
conda create -n meshEval python=3.12.15
```

Quando aparecer `Proceed ([y]/n)?`, digite apenas `y` e pressione Enter. Aguarde a instalação terminar e o prompt retornar antes de executar:

```bat
conda activate meshEval
python --version
```

O início da linha deve mostrar `(meshEval)`. A versão confirmada neste ambiente foi **Python 3.12.15**. Se o ambiente já existe, basta ativá-lo; não é necessário criá-lo novamente.

## Passo 2 — Instalar as dependências

Com o ambiente ativo:

```bat
python -m pip install numpy pandas trimesh pyrender open3d matplotlib imageio scipy scikit-image torch torchvision lpips
```

### Versões registradas em 17/10/2026

| Tecnologia | Versão instalada informada |
| --- | --- |
| Python | 3.12.15 |
| Conda | 25.11.1 |
| NumPy | 2.5.4 |
| pandas | 3.0.6 |
| Trimesh | 5.1.1 |
| pyrender | 0.1.45 |
| Open3D | 0.20.0 |
| Matplotlib | 3.11.2 |
| imageio | 2.38.1 |
| SciPy | 1.18.1 |
| scikit-image | 0.26.0 |
| PyTorch (torch) | 2.14.1+cpu |
| torchvision | 0.29.1 |
| LPIPS | 0.1.4 |
| PyOpenGL | 3.1.0 |
| pyglet | 2.1.19 |
| Pillow | 13.0.0 |
| pytest | 9.1.1 |
| Ruff | 0.17.1 |

O pip informou `Successfully installed`. Os dois pipelines foram executados neste ambiente, confirmando que suas dependências carregaram e que a renderização funcionou nesta máquina. Isso não confirma aceleração CUDA. As versões acima não identificam o ambiente que gerou os resultados já existentes no repositório. O comando acima não fixa versões e poderá instalar versões diferentes no futuro.

Para recriar o ambiente Windows com as versões observadas, use o snapshot exportado:

```bat
conda env create -f environments/environment-lock.yml
```

`environments/environment.yml` continua como uma lista geral de dependências; `environments/environment-lock.yml` fixa as versões Conda e pip observadas neste ambiente Windows em 17/10/2026. O snapshot não inclui o caminho local do ambiente.

## Passo 3 — Instalar o pacote e executar os pipelines

Na raiz do repositório, registre o pacote no ambiente ativo. A instalação editável permite importar `meshcomparison` diretamente do diretório `src/` e disponibiliza os comandos `mesh-eval` e `percept-eval` definidos no `pyproject.toml`:

```bat
python -m pip install -e . --no-deps
```

O arquivo Conda instala as dependências; `--no-deps` evita que o pip tente substituí-las.

Primeiro, confira as importações:

```bat
python -c "import numpy, pandas, trimesh, pyrender, open3d, matplotlib, imageio, scipy, skimage, torch, torchvision, lpips; print('OK: bibliotecas carregadas')"
```

Se o teste terminar sem erro, execute a avaliação geométrica:

```bat
python -m meshcomparison.geometry --gt data/samples/gt.stl --rm data/samples/mod.stl --out output
```

Após verificar esse resultado, execute a avaliação perceptual:

```bat
python -m meshcomparison.perceptual --gt data/samples/gt.stl --rm data/samples/mod.stl --out output
```

O repositório já contém `data/samples/gt.stl` e `data/samples/mod.stl` para execução de exemplo. Os comandos podem substituir arquivos existentes em `output/` (ou no diretório passado em `--out`). Para modelos FBX, converta antes para um formato aceito pelo Trimesh. O renderizador offscreen pode exigir configuração gráfica específica do sistema.

### Validação

- [x] Ambiente Conda criado e ativado, conforme terminal informado.
- [x] Python 3.12.15 confirmado.
- [x] Instalação das dependências concluída, conforme saída do pip.
- [x] Importações necessárias carregadas durante a execução dos pipelines.
- [x] Pipeline geométrico executado; resultados salvos em `examples/output/`.
- [x] Pipeline perceptual executado; métricas e renders salvos em `examples/output/`.
- [x] CUDA verificada: indisponível neste ambiente; PyTorch instalado sem suporte CUDA.
- [x] Dependências gerais registradas em [`environment.yml`](../../../environments/environment.yml) e versões observadas fixadas em [`environment-lock.yml`](../../../environments/environment-lock.yml).

## Passo 4 — Próxima etapa

Continue para [02 — Conferir os programas e a interface de linha de comando](02-arquitetura-implementacao.md).

**Código de referência:** [configuração do pacote e comandos](../../../pyproject.toml), [CLI geométrica](../../../src/meshcomparison/geometry/cli.py) e [CLI perceptual](../../../src/meshcomparison/perceptual/cli.py). Esta etapa registra a preparação e a validação do ambiente local.
