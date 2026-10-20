# 01 — Construir ambiente reproduzível e primeira linha de base

> **Projeto novo:** implementar antes da primeira funcionalidade relevante. **Mesh Comparison: ✅ infraestrutura presente; 🟡 baseline científica e validação multiplataforma ainda incompletas.**

## Finalidade

Um agente deve poder instalar, executar, testar e reproduzir o projeto sem depender de informações que só estejam em um chat ou na máquina de quem o iniciou.

## Do zero — roteiro reutilizável

1. Criar repositório Git e decidir branches, política de PR e convenções de commits; nunca editar a branch protegida diretamente por padrão.
2. Selecionar um sistema de dependências adequado: `pyproject.toml`/uv/pip/Conda (Python), `package.json` com lock (Node), ou equivalente. Definir versão de linguagem, ferramenta de execução, plataformas suportadas e regras de atualização.
3. Criar um comando **único e documentado** para instalar e pelo menos um para executar teste rápido. Se houver configuração de GPU, torná-la opcional e detectável.
4. Criar `README.md` com objetivo, requisitos, instalação, exemplos mínimos, entradas, saídas, limitações e comandos exatos.
5. Versionar **pequena entrada de teste** e saída esperada (ou gerador determinístico). Registrar seed, parâmetros, unidade de medida, versão de algoritmo e formatos utilizados.
6. Incluir `.gitignore` para ambientes virtuais, credenciais, cache, arquivos grandes e artefatos descartáveis; fornecer `.env.example` sem segredo se necessário.
7. Executar um *smoke test* (ex.: `--help` ou teste trivial) **antes** da primeira grande implementação; documentar diferenças entre desenvolvimento local e runner de CI.
8. Criar registro de baseline com commit, comando, SO, runtime, dependências e resultado observado; atualizar apenas mediante mudança intencional de contrato.

### Exemplo concreto em Python/Conda (não genérico a outras stacks)

```bash
conda env create -f environments/environment.yml
conda activate meshEval
python -m pip install -e . --no-deps
ruff check .
pytest -q
```

Para conferir os pontos de entrada por importação, use o comando indicado no [guia de preparação do ambiente](../../implementation/step-by-step/01-preparacao-ambiente.md).

Para um **novo** repositório, substitua nomes e comandos pelo seu próprio ambiente e ponto de entrada. O `environments/environment-lock.yml` é um snapshot Windows CPU **anterior à GUI**; `environments/requirements-windows-cu128.txt` é um snapshot pip distinto, com pins da GUI e PyTorch CUDA 12.8. Nenhum deles é um lock universal para Linux/macOS.

## O que já está implantado no Mesh Comparison

| Item | Estado | Referência |
| --- | :---: | --- |
| Gerenciamento de ambiente Conda | ✅ | [environment.yml](../../../environments/environment.yml) |
| Dependências com versões registradas | 🟡 | [environment-lock.yml](../../../environments/environment-lock.yml) registra o snapshot Windows CPU antigo; [requirements-windows-cu128.txt](../../../environments/requirements-windows-cu128.txt) registra o snapshot pip com GUI e CUDA 12.8 |
| Entradas e pipelines documentados | ✅ | [README](../../../README.md), `data/samples/gt.stl`, `data/samples/mod.stl` e pipelines |
| Saídas de avaliação e métricas de exemplo | ✅ | [README principal](../../../README.md) e [`examples/output/`](../../../examples/output/); `output/` é pasta local ignorada pelo Git |
| Baseline sistemática com hashes e comparação de cenários | 🟡 | Exemplos existem; validação ampla documentada como pendente |
| Reprodutibilidade de toda a renderização entre plataformas | ❓ | Não comprovada; requer validação específica |
| Interface gráfica PySide6/PyVistaQt | ✅ | [Código](../../../src/meshcomparison/gui/) e [guia desktop](../../gui/README.md); funcionamento precisa ser testado em SO real |

### Verificação prática deste projeto

Em branch isolada, rode os comandos acima. Para uma verificação curta em Python, use pastas distintas porque os dois pipelines exportam `aligned/rm_aligned.ply`:

```python
from meshcomparison.geometry.pipeline import run_pipeline as run_geometry
from meshcomparison.perceptual.pipeline import run_pipeline as run_perceptual

run_geometry("data/samples/gt.stl", "data/samples/mod.stl", "output/harness-baseline/geometry",
             width=320, height=240)
run_perceptual("data/samples/gt.stl", "data/samples/mod.stl", "output/harness-baseline/perceptual",
               num_views=10, save_views=(1, 5, 10), width=320, height=240, device="cpu")
```

Também é possível executar o mesmo fluxo pela interface (`python -m meshcomparison.gui`), que usa os parâmetros fixos descritos no [guia desktop](../../gui/README.md).

Separar essas saídas das anteriores. Não comparar a mediana de 10 vistas com resultados anteriores de 100 vistas como se os experimentos fossem equivalentes. Executar e registrar resultados reais antes de afirmar que tudo passou.

## Critérios de aceite

- [ ] Uma instalação limpa reproduz os comandos documentados.
- [ ] Pelo menos um teste automatizado e um smoke test têm resultado registrado.
- [ ] Inputs, parâmetros e outputs de referência estão identificados.
- [ ] Ambientes suportados e limitações (GPU, renderização, SO) estão descritos.
- [ ] Artefatos temporários e segredos não entram em commits.

**Próxima etapa:** [02 — Instruções e arquitetura](02-instrucoes-e-contexto.md).
