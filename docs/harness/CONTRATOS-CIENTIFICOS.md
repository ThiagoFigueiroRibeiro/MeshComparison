# Contratos científicos — Mesh Comparison (GT × RM)

> **Estado:** especificação documental proposta e rastreável, derivada de inspeção estática; **não** é certificação de equivalência numérica, nem teste executado, nem alteração dos algoritmos.
>
> **Referência de origem:** [ThiagoFigueiroRibeiro/MeshComparison](https://github.com/ThiagoFigueiroRibeiro/MeshComparison), `main` em `86d0959f943735ba058ed16b82b3c2836034aad9`; arquivos [mesh_eval_pipeline.py](https://github.com/ThiagoFigueiroRibeiro/MeshComparison/blob/86d0959f943735ba058ed16b82b3c2836034aad9/mesh_eval_pipeline.py) e [percept_eval_pipeline.py](https://github.com/ThiagoFigueiroRibeiro/MeshComparison/blob/86d0959f943735ba058ed16b82b3c2836034aad9/percept_eval_pipeline.py).
>
> **Adaptação inspecionada:** `lianeheidemann/mesh-comparison`, branch `single-view-3d-reconstruction`, commit `d600f68dae3d083803fc5c53842051856a8c32f8` (19/10/2026). Reavaliar o documento quando o código mudar.
>
> **Convenção:** **ORIGINAL** = comportamento identificado no código-fonte de origem; **ATUAL** = presente na implementação inspecionada; **VALIDAR** = critério recomendado, ainda sem execução/comprovação aqui; **MUDANÇA METODOLÓGICA** = exige aprovação, comparação de resultados e ADR.

## 1. Escopo e regra geral

O código de origem **avalia** a diferença entre uma malha de referência (**GT**, ground truth) e outra malha já reconstruída (**RM**). **Não implementa a reconstrução de uma malha 3D a partir de uma imagem**. A comparação é dividida em:

1. **Geometria:** distâncias Euclidianas entre **vértices e seus vértices vizinhos mais próximos**; normalização e alinhamento condicional por ICP com escala; heatmap direcional.
2. **Percepção:** renderizações ortográficas de GT e RM alinhada sob as mesmas câmeras; LPIPS, PSNR e SSIM por vista; estatísticas agregadas.

**Invariante principal:** otimização, paralelização, GUI ou refatoração não autorizam substituir distâncias entre vértices por distâncias ponto-superfície, substituir o ICP com escala, alterar a definição de PSNR, ou modificar câmeras/máscaras sem tratar isso como **nova versão metodológica**.

## 2. Contratos de entrada e preparação

### CC-01 — Leitura, geometria e unidades

**ORIGINAL / ATUAL**

- Carregar malhas com `trimesh.load(path, force="scene", process=False, maintain_order=True)`.
- Quando for uma cena, aplicar transformações do grafo às geometrias instanciadas, concatenando as partes; remover vértices não referenciados.
- Rejeitar **FBX** diretamente; converter previamente. Outros formatos dependem do suporte efetivo do Trimesh, do conteúdo do arquivo e do carregador disponível.
- GT e RM precisam ter um sistema de coordenadas e unidades interpretáveis em conjunto. O código não realiza calibração semântica ou conversão automática de unidades.

**VALIDAR:** arquivos inexistentes/corrompidos, ausência de vértices, geometrias degeneradas e transformações de cena devem ser tratados de forma explícita; registrar os formatos realmente testados. O comportamento para entradas inválidas não deve ser considerado coberto só porque a função de carga existe.

**Fontes atuais:** `src/meshcomparison/common/io.py` e `src/meshcomparison/common/prepare.py`.

### CC-02 — Normalização interna comum à GT e RM

**ORIGINAL / ATUAL**

Seja `D = ||bbox_max(GT) - bbox_min(GT)||_2`, nas unidades de entrada. O pipeline exige `D >= 1e-12`, e aplica **o mesmo fator** `s=1/D` aos vértices das duas malhas:

```text
GT_normalizada = GT_original / D
RM_normalizada = RM_original / D
```

- **Não** normalizar cada malha pela própria diagonal; isso apagaria a diferença relativa de tamanho antes do alinhamento.
- Não presumir centralização na origem nessa etapa: o código apenas escala coordenadas.
- Distâncias de saída em unidades da GT são obtidas multiplicando os valores normalizados por `D`; MSE utiliza `D²`.
- `rm_aligned.ply` é exportada após desfazer a normalização global (`* D`).
- `final_transform_00`…`final_transform_23` representam a matriz **no espaço normalizado**, não uma transformação de translação pronta em unidades originais.

**VALIDAR:** para uma mesma execução, `mean_chamfer_gt_units ≈ mean_chamfer_normalized * D`, `symmetric_rmse_gt_units ≈ symmetric_rmse_normalized * D` e `pre/post_alignment_mse_gt_units_sq ≈ pre/post_alignment_mse_normalized * D²` dentro de tolerâncias de ponto flutuante.

## 3. Contratos geométricos

### CC-03 — Distância entre vértices e MSE de alinhamento

**ORIGINAL / ATUAL**

Para conjuntos de vértices normalizados `G` (GT) e `R` (RM), definir:

```text
d(g,R) = min_{r em R} ||g-r||₂
d(r,G) = min_{g em G} ||r-g||₂

MSE_sym = 1/2 [ mean_{g em G}(d(g,R)²)
              + mean_{r em R}(d(r,G)²) ]
```

A implementação usa `scipy.spatial.cKDTree`, consulta do vizinho mais próximo em ambas as direções e não estima distâncias às faces ou às superfícies contínuas.

**ATUAL:** `src/meshcomparison/common/distances.py` passou a chamar `cKDTree.query(..., workers=-1)`. Essa paralelização **não redefine** a métrica; eventuais divergências precisam de teste.

### CC-04 — Gatilho e transformação ICP

**ORIGINAL / ATUAL**

- Calcular `pre_alignment_mse_normalized` sobre GT e RM **antes** do ICP.
- Executar ICP **somente se** `pre_alignment_mse_normalized > 1e-4` (limiar padrão). Na igualdade, não executar.
- Fonte = RM; destino = GT.
- Transformação de similaridade ponto-a-ponto no Open3D: **rotação, translação e escala uniforme** (`TransformationEstimationPointToPoint(with_scaling=True)`).
- Inicialização por centros médios dos pontos e razão das diagonais das caixas da RM e GT amostradas.
- Subamostragem máxima: `50.000` pontos de cada lado; seeds `1` (RM) e `2` (GT), caso excedam o limite.
- ICP grosseiro: correspondência máxima normalizada `0.25`; ICP fino: `0.05`; até `100` iterações em cada etapa.
- Se não executar, manter RM e transformação identidade; se executar, aplicar matriz de similaridade à RM normalizada.
- Registrar resultados pré/pós-alinhamento separadamente. O algoritmo **não garante matematicamente** convergência ao mínimo global nem melhoria em todos os pares de malhas.

**Atenção científica:** como o ICP permite escala uniforme, diferenças dimensionais podem ser reduzidas no resultado **pós-alinhamento**. Não interpretar esse resultado isolado como medida fiel do erro de escala de reconstrução.

**VALIDAR:** limiar (abaixo, igual e acima), identidade, transformação controlada, consistência de `final_transform`, casos de falha/convergência e permanência das medidas pré-alinhamento.

**Fontes atuais:** `src/meshcomparison/common/prepare.py` e `src/meshcomparison/common/alignment.py`.

### CC-05 — Chamfer, Hausdorff, RMSE e MSE

**ORIGINAL / ATUAL** — para os mesmos conjuntos de vértices normalizados, **após** o ICP condicional:

```text
Chamfer_mean = 1/2 [ mean(d(g,R)) + mean(d(r,G)) ]
Hausdorff_sym = max( max(d(g,R)), max(d(r,G)) )
RMSE_sym = sqrt( 1/2 [ mean(d(g,R)²) + mean(d(r,G)²) ] )
MSE_sym = RMSE_sym²
```

- **Chamfer é média de distâncias, não média de distâncias quadradas.**
- **Hausdorff é o máximo bidirecional entre vértices amostrados pela malha, não Hausdorff contínuo entre superfícies.**
- **RMSE/MSE usam vizinhos mais próximos**, não correspondência por índice nem mesmo número de vértices.
- A média de cada direção recebe peso `0.5`; cada vértice recebe peso igual **dentro** da respectiva direção.
- Mudar densidade/distribuição de vértices pode modificar as métricas mesmo quando a superfície aparente é similar.

**VALIDAR:** identidade → métricas próximas de zero; `RMSE² ≈ MSE` (no mesmo espaço de unidades); invariância de ordem dos vértices sem alteração geométrica; casos assimétricos controlados; densidade desigual e incompletude sem assumir valor universal.

**Fonte atual:** `src/meshcomparison/geometry/metrics.py`.

### CC-06 — Heatmap direcional

**ORIGINAL / ATUAL**

- Associar a cada vértice da **GT normalizada** a distância **GT → RM alinhada**: `d(g,R)`.
- Colorir a **GT**, não a RM, usando `RdYlGn_r` do Matplotlib.
- Normalizar cores em `[0, max(percentil_95(d), 1e-12)]`; valores acima saturam na extremidade superior.
- A barra indica distância de vértice da GT até RM alinhada. **Não** é mapa de distâncias simétricas, assinadas ou calculadas sobre a superfície.
- Exportar malha colorida e PNG renderizado. A saturação visual no P95 não altera as métricas numéricas.

**VALIDAR:** relação exata entre `d_gt2rm` e cores; caso idêntico; erro local; mudança explícita de direção/paleta/percentil somente como alteração de contrato de visualização.

**Fonte atual:** `src/meshcomparison/geometry/heatmap.py`.

## 4. Contratos de renderização e percepção

### CC-07 — Renderização pareada e câmeras

**ORIGINAL / ATUAL**

- Usar projeção **ortográfica** com câmeras compartilhadas entre GT e RM alinhada; enquadramento calculado com a caixa envolvente conjunta, evitando condições de câmera diferentes entre comparações.
- No pipeline geométrico, gerar vista GT, vista RM e heatmap com a mesma configuração de câmera.
- No pipeline perceptual, usar `azimuths = linspace(0, 360, num_views, endpoint=False)`, indexação de vistas começando em `1`, elevação fixa e enquadramento por vista.
- Padrões perceptuais: `num_views=100`, `elevation=25.264°`, `camera_margin=1.05`, `radius_factor=1.45`, `1600x1200`; salvar vistas `1,33,66`.
- **Diferença entre interfaces:** a função Python `geometry.run_pipeline` tem padrões `azimuth=45°` e `elevation=35.264°`, enquanto a CLI **original** e o `RunConfig` da GUI atual usam `-135°` e `25.264°`. Comparar saídas somente após fixar explicitamente esses parâmetros.
- Renderização perceptual original usa `pyrender` RGBA com fundo transparente e iluminação direcional; a implementação atual reutiliza um renderer e pode processar métricas em threads. A equivalência de pixels **é hipótese a testar**, não fato comprovado pela refatoração.

**VALIDAR:** mesmo ângulo, projeção, enquadramento, iluminação, dimensões, máscara, driver e versões. Distinguir testes de equivalência numérica de renderizadores dos testes apenas de existência de PNG.

**Fontes atuais:** `geometry/rendering.py`, `perceptual/cameras.py`, `common/rendering.py`, `perceptual/pipeline.py`, `gui/config.py`.

### CC-08 — Preparação das imagens e máscaras

**ORIGINAL / ATUAL**

1. Normalizar RGB e alfa RGBA por `255` para `float32` em `[0,1]`.
2. Usar `mask = (alpha > 0)` para cada imagem e `rgb_masked = rgb * alpha`.
3. Formar a **união** das máscaras GT/RM e recortar a menor caixa com `pad=12` pixels (limitada à imagem); união vazia gera erro.
4. Zerar o fundo fora da união no crop usado no SSIM e LPIPS.
5. **PSNR** é calculado no crop com a máscara da união; **SSIM e LPIPS** recebem o crop com fundo zerado, mas não uma máscara espacial na API de suas métricas.

Isso é uma escolha metodológica da implementação e **não** equivale a uma comparação de todas as regiões renderizadas nem a um SSIM/LPIPS estritamente ponderado por máscara.

**Fonte atual:** `src/meshcomparison/perceptual/image_metrics.py`.

### CC-09 — PSNR legado: definição exata

**ORIGINAL / ATUAL**

Para `N` pixels da união de máscaras, a função soma os erros quadráticos dos **três canais RGB** e divide por **N**, **não por 3N**:

```text
E_legacy = [sum_{p na união} sum_{c em RGB} (GT[p,c]-RM[p,c])²] / (N + 1e-12)
PSNR_legacy = 10 * log10(1 / E_legacy)
```

- Entrada `float32` em `[0,1]`, pico `1`.
- Se `N = 0` retorna `NaN`; se `E_legacy <= 1e-12` retorna `+Infinity`.
- Esta **não é** a convenção usual de MSE médio sobre todos os canais. Trocar por uma biblioteca de PSNR convencional sem mudança de versão alterará resultados (diferença de cerca de `10*log10(3)` dB quando os erros estão acima do piso numérico).

**VALIDAR:** par RGB sintético com erro conhecido, igualdade exata, máscara vazia, múltiplos canais e comparação contra a fórmula legada — **não** contra um PSNR convencional usado como substituição.

### CC-10 — SSIM e LPIPS legados

**ORIGINAL / ATUAL**

- `SSIM`: `skimage.metrics.structural_similarity(gt_crop_masked, rm_crop_masked, channel_axis=-1, data_range=1.0)`. O fundo é zerado antes, mas participa do cálculo da janela local: **não rotular como SSIM espacialmente mascarado**.
- `LPIPS`: rede pré-treinada **AlexNet** via `lpips.LPIPS(net="alex")`, `eval()`, sem gradientes; converter `HWC → NCHW`, reescalar canais de `[0,1]` para `[-1,1]`, comparar o crop com fundo zerado.
- Dispositivo do LPIPS original: CUDA se disponível, senão CPU; GUI atual permite seleção `auto/cpu/cuda` conforme módulo de device. Alterar o dispositivo pode produzir pequenas diferenças numéricas; registrar versão de PyTorch, LPIPS, pesos e hardware.
- SSIM depende de dimensões suficientes para o tamanho padrão de janela da biblioteca; erros em crops pequenos devem ser explícitos, não convertidos em sucesso artificial.

**VALIDAR:** imagens iguais sob a mesma preparação; entradas pequenas; controle das versões/pesos; tolerâncias CPU/GPU justificadas.

### CC-11 — Resumo estatístico perceptual

**ORIGINAL / ATUAL**

Para cada métrica nas vistas avaliadas, remover valores **não finitos** (`NaN`, `±Infinity`) e calcular **min, max, p25, p75, mediana e média** com NumPy. Se não houver valores finitos, retornar `NaN` nos seis campos.

**Atenção:** imagens idênticas podem gerar `PSNR = +Infinity`, que **é omitido do resumo**, embora conste no CSV por vista. **Não substituir silenciosamente** esse procedimento por médias incluindo infinito, preenchimento de zeros ou outra agregação.

## 5. Contratos dos resultados e da proveniência

### CC-12 — Saídas obrigatórias e rastreabilidade

**ORIGINAL / ATUAL (sem alterar nomes do projeto atual)**

| Produto | Saída atual | Significado |
| --- | --- | --- |
| Métricas geométricas | `metrics/metrics_geometry.csv` | Pré/pós-ICP; Chamfer, Hausdorff, RMSE; valores normalizados e unidades da GT; câmera; matriz 3x4 |
| Métricas perceptuais por vista | `metrics/per_view_metrics.csv` | `view_idx`, azimute/elevação, LPIPS/PSNR/SSIM, dimensões do crop e câmera |
| Resumo perceptual | `metrics/metrics_perceptual.csv` | Estatísticas dos valores finitos por métrica |
| Metadados | `metrics/run_metadata.csv` | Paths GT/RM, alinhamento, threshold, vistas, câmera, matriz |
| Malha alinhada | `aligned/rm_aligned.ply` | RM após ICP condicional e retorno à escala original |
| Geometria renderizada | `renders/gt_ortho.png`, `renders/rm_aligned_ortho.png`, `heatmaps/gt_heatmap_ortho.png`, `heatmaps/gt_heatmap_colored.ply` | Visuais geométricos/heatmap |
| Vistas perceptuais | `renders/gt/`, `renders/rm/`, `renders/pairs/` | Imagens selecionadas de GT, RM e pares |

**Diferença de nomes entre repositórios:** o original documenta `mesh_metrics.csv` e `metric_summary.csv` em alguns materiais, enquanto os scripts inspecionados escrevem `metrics_geometry.csv` e `metrics_perceptual.csv`. A referência verificável é a **escrita efetiva no código**. Os nomes usados acima são os da branch atual.

**VALIDAR:** schema, unidades, valores e arquivos; `tests/test_output_schema.py` já executa subprocessos para testar **estrutura** dos CSVs, mas essa cobertura não assegura equivalência científica de conteúdo.

### CC-13 — Proveniência mínima de experimento (complemento proposto)

Para comparar execuções com rigor, registrar em relatório ou manifesto adicional, **sem mudar CSVs legados implicitamente**:

- Commit do código, commit/método de referência, SO, Python, versões NumPy/SciPy/Trimesh/Open3D/PyRender/scikit-image/PyTorch/LPIPS.
- Hash SHA-256 da GT e da RM; unidades e convenção de eixos; flags de carregamento; seed/subamostragem.
- Threshold, parâmetros ICP, opções de câmera, resolução, máscara/crop, número/índices de vistas, backend gráfico, dispositivo e pesos LPIPS.
- Tolerâncias por teste; local do resultado; divergências conhecidas CPU/GPU ou entre renderizadores.

Esse manifesto é **proposta**, não recurso já comprovado no original.

## 6. Matriz de aceitação — próximos testes (não declarados como concluídos)

| ID | Cenário | Critério observável | Estado nesta revisão |
| --- | --- | --- | --- |
| T-01 | GT = RM, mesma geometria/vértices | Distâncias geométricas ~0, MSE pré-ICP ~0 e ICP não acionado | **VALIDAR end-to-end** |
| T-02 | RM transladada/rotacionada de modo conhecido | Gatilho conforme MSE pré, transformação RM→GT documentada, métricas pós computadas | **VALIDAR** |
| T-03 | RM com escala diferente | Preservar escala no pré-ICP; registrar possível correção pelo ICP de similaridade | **VALIDAR** |
| T-04 | Permutação da ordem dos mesmos vértices | Métricas de vizinho mais próximo equivalentes dentro de tolerância | **VALIDAR** |
| T-05 | Densidade não uniforme/ausência de superfície | Documentar a sensibilidade de métricas entre vértices e direção dos erros | **VALIDAR** |
| T-06 | Deformação localizada | Heatmap GT→RM e métricas geométricas respondem de forma coerente | **VALIDAR** |
| T-07 | Imagens RGB e máscara sintéticas | PSNR calculado pela **fórmula legada**, inclusive casos `Inf/NaN` | **VALIDAR** |
| T-08 | Mesmo par renderizado, mesmos parâmetros | Contratos de câmeras, PNGs e métricas perceptuais dentro de tolerâncias justificadas | **VALIDAR** |
| T-09 | Saídas originais vs. refatoradas | Comparar valores e schemas sob **entradas/parâmetros/versões idênticos** | **VALIDAR** |
| T-10 | Dados inválidos/sem máscara/GT degenerada | Falha visível e sem resultados apresentados como sucesso | **VALIDAR** |

**Separação importante:** os testes unitários existentes em `tests/` cobrem partes das fórmulas; os testes `test_output_schema.py` e `test_worker.py` já possuem integração por subprocesso. Não reimplementar o que existe: **estender** com resultados esperados e tolerâncias justificadas. Nenhum teste adicional foi criado nem executado por este documento.

## 7. Regras de governança para agentes

**Antes de modificar o código:** ler este documento, `docs/harness/README.md`, os arquivos de origem citados e os módulos atuais correspondentes. Fazer plano com escopo, impacto numérico, testes, evidências e rollback.

**Permitir sem decisão metodológica nova, desde que validado:** reorganização de módulos, melhorias na interface e otimização de desempenho que preservem a definição matemática, o tratamento dos dados e os resultados dentro de tolerância acordada.

**Exigir aprovação humana + ADR + baseline comparativa antes de alterar:** normalização, unidades, distância vértice-vértice versus ponto-superfície, MSE/Chamfer/Hausdorff/RMSE, ICP com escala, limiares, amostragem, câmeras, iluminação, máscaras, definição legada de PSNR, modelo/pesos LPIPS, política de estatísticas finitas, schema/unidades dos CSVs.

**Nunca:** ocultar falhas, afirmar testes não executados, relaxar tolerâncias sem justificativa ou misturar resultados de versões metodológicas diferentes sob o mesmo rótulo.

**Evidência mínima em PR:** tarefa, commit inicial/final, parâmetros, execução real dos testes, comparação de resultados, arquivos alterados, diferenças deliberadas, limitações e decisão da pessoa revisora.

## 8. Rastreabilidade: original → projeto atual

| Origem (ThiagoFigueiroRibeiro) | Implementação da branch atual |
| --- | --- |
| `mesh_eval_pipeline.py:load_mesh` | `src/meshcomparison/common/io.py` |
| `mesh_eval_pipeline.py:symmetric_mse, nn_distances` | `common/distances.py` |
| `mesh_eval_pipeline.py:similarity_icp_align` | `common/alignment.py` |
| `mesh_eval_pipeline.py:run_pipeline` (etapas 1–4) | `common/prepare.py` |
| `mesh_eval_pipeline.py:compute_metrics` | `geometry/metrics.py` |
| `mesh_eval_pipeline.py:colorize_gt_heatmap` | `geometry/heatmap.py` |
| `mesh_eval_pipeline.py:build_shared_camera` | `geometry/rendering.py` |
| `percept_eval_pipeline.py:camera_pose_for_view, build_tight_ortho_camera` | `perceptual/cameras.py` |
| `percept_eval_pipeline.py:rgba_to_rgb_mask, crop_to_union_mask, masked_*` | `perceptual/image_metrics.py` |
| `percept_eval_pipeline.py:run_pipeline` | `perceptual/pipeline.py` |
| Renderer recriado por vista no original | `common/rendering.py:OrthoRenderer` (reuso do contexto; equivalência a comprovar) |

## 9. Processo de aprovação da versão metodológica

1. Registrar a **baseline de fato executada** (source commit, inputs, parâmetros, dependências, resultados).
2. Implementar os testes de aceitação prioritários sem introduzir outra fórmula científica.
3. Se for desejável corrigir PSNR, adotar comparação ponto-superfície ou mudar ICP, criar **nova metodologia versionada**, um ADR e métricas separadas; **não sobrescrever** resultados históricos como se fossem equivalentes.
4. Validar PR em ambiente real, com revisão humana, antes de declarar este conjunto de contratos **aprovado/verificado**.

**Leituras vinculadas:** [guia de Harness](README.md), [testes e regressões](step-by-step/03-testes-e-regressoes.md), [plano de validação científica](../implementation/step-by-step/10-limitacoes-evolucao.md).

**Autoria técnica de referência:** código-fonte de [ThiagoFigueiroRibeiro/MeshComparison](https://github.com/ThiagoFigueiroRibeiro/MeshComparison). Este documento caracteriza a metodologia observada e propõe verificações para o projeto derivado; não declara que o original seja uma referência científica publicada ou validada externamente.
