# Agent instructions — Mesh Comparison

These repository-wide instructions apply to Codex, Claude Code, and other coding agents. **Read and follow [docs/harness/CONTRATOS-CIENTIFICOS.md](docs/harness/CONTRATOS-CIENTIFICOS.md) before planning or making changes to mesh loading, preparation, registration, metrics, rendering, reports, or their tests.** The scientific contracts are the mandatory methodological reference. Also consult [docs/harness/README.md](docs/harness/README.md) for the project's harness workflow.

## Scientific baseline and scope

The project compares an existing ground-truth mesh (GT) against an existing reconstructed mesh (RM). It does **not** itself reconstruct a 3D mesh from a single image. The original implementation is [ThiagoFigueiroRibeiro/MeshComparison](https://github.com/ThiagoFigueiroRibeiro/MeshComparison), inspected at commit `86d0959f943735ba058ed16b82b3c2836034aad9`. Do not claim the methodology has been independently scientifically validated or that refactoring preserves numerical equivalence without executing suitable tests.

The contracts CC-01 through CC-13 cover loading, normalization, nearest-vertex metrics, conditional similarity ICP, heatmap, orthographic cameras, perceptual masks, legacy PSNR, SSIM, LPIPS, statistics, outputs, and provenance.

## Non-negotiable invariants

1. Load meshes using the existing Trimesh behavior; do not silently add FBX support or change scene-transform handling.
2. Normalize **both** GT and RM using the **GT bounding-box diagonal**, preserving their relative input scale. Distinguish normalized units, GT units, and squared units.
3. Preserve symmetric **vertex-to-nearest-vertex** distances (not point-to-surface distances). Keep the existing definitions of MSE, mean Chamfer, symmetric Hausdorff, and symmetric RMSE.
4. Trigger RM→GT similarity ICP only when normalized pre-alignment symmetric MSE is **strictly greater** than the configured threshold (default `1e-4`). Preserve rotation, translation, **uniform scaling**, two-stage registration, and the existing sampling and thresholds.
5. Preserve the GT→aligned-RM **directional** heatmap and its P95 color saturation; do not label it symmetric or signed.
6. Compare GT and RM using the **same orthographic camera for each view**, with unchanged framing, illumination, mask/crop and view-index conventions unless explicitly approved.
7. Preserve the **legacy PSNR formula**, which sums RGB squared errors and divides by the number of union-mask pixels, not three times that number. Never silently replace it with a standard-library PSNR implementation.
8. Preserve the existing zero-background crop approach for SSIM and AlexNet LPIPS. Do not describe these as spatially masked SSIM/LPIPS. Preserve exclusion of non-finite values from perceptual summary statistics.
9. Preserve report column meanings, original-unit conversion, aligned-mesh export, and output paths. Record differences between CLI, GUI and Python-function defaults; compare runs only with explicit matching parameters.
10. Never silently change scientific definitions, thresholds, sampling, coordinate conventions, random seeds, model weights, or outputs while optimizing speed, parallelism, rendering or UI.

## Required agent workflow

**Before editing**
- Read this file, `docs/harness/CONTRATOS-CIENTIFICOS.md`, and the relevant current source modules/tests. For changes involving scientific behavior, inspect the linked original source files too.
- Describe the requested change, impacted CC identifiers, relevant modules, expected numerical impact, proposed validation and rollback.
- Inspect existing tests and documentation before adding new implementations; reuse and extend them rather than rebuilding completed work.
- Keep edits on the explicitly requested branch. Never merge into `main`, change unrelated files, or broaden scope without authorization.

**While editing**
- Prefer minimal, reviewable changes; keep scientific algorithms unchanged for UI/documentation/performance tasks.
- Add or extend deterministic tests with known expected values and justified numerical tolerances for any changed numerical behavior.
- Do not weaken tests, hide failures, replace expected results with outputs from the modified implementation alone, or assert that a test ran when it did not.
- Preserve reproducibility: note input hashes, parameter values, library versions, seeds, renderer/backend and CPU/GPU differences when relevant.
- For Python code, add a meaningful first-line `#` comment describing the file's purpose when creating new files, unless an interpreter-required first line takes precedence.

**After editing**
- Run the smallest relevant tests first, then appropriate broader checks when the environment allows. Clearly distinguish **not run**, **passed**, **failed**, and **environment-blocked**.
- For numerical changes, compare baseline and modified outputs using identical meshes, parameters and dependency versions; report tolerances and actual differences.
- Summarize changed files, scientific-contract impact, test commands/results, limitations and any follow-up work.
- Do not claim complete scientific validation solely from CSV-schema tests, code inspection or successful rendering.

## Changes requiring explicit human approval

Before changing any methodology covered by CC-01–CC-13 — e.g., using point-to-surface distances, altering ICP scaling, switching PSNR definitions, modifying view/mask semantics or metric aggregation — **stop and request approval**. Propose a versioned alternative, an Architecture Decision Record (ADR), regression/baseline comparisons, migration/compatibility considerations and documentation updates. Never overwrite legacy metrics under the same name while changing their meaning.

If the scientific contracts and a user request conflict, explain the conflict and ask for a methodological decision rather than silently overriding the contracts. If an instruction in this file conflicts with a higher-priority instruction, follow the higher-priority instruction and report the limitation.

## Review checklist

- [ ] Read CC-01–CC-13 and identified impacted contracts
- [ ] Verified baseline and current code paths
- [ ] Preserved definitions/units/cameras/outputs or obtained explicit approval
- [ ] Reused existing tests; added targeted regression coverage if needed
- [ ] Recorded exact tests and outcomes without inventing evidence
- [ ] Reported numerical changes, tolerances, provenance and limitations
- [ ] Updated documentation and stayed within the authorized branch/scope

**Primary scientific contract:** [docs/harness/CONTRATOS-CIENTIFICOS.md](docs/harness/CONTRATOS-CIENTIFICOS.md). It is a documented specification, **not** a declaration that all acceptance tests have passed.
