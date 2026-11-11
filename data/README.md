# Dados

Malhas de referência (GT) e um par de exemplo. O critério de escolha das GTs está no [guia de GTs](../docs/gt/README.md) e o resumo no [README](../README.md#user-content-datasets).

## Conteúdo

| Caminho | O que é |
| --- | --- |
| [`gso/selection.csv`](gso/selection.csv) | Seleção do Google Scanned Objects: 20 objetos principais, 4 suplentes e 1 excluído |
| `gso/meshes/` | As 20 malhas principais baixadas do Gazebo Fuel (`.obj`, `.png` e `.jpg` no Git LFS) |
| [`gso/meshes/manifest.csv`](gso/meshes/manifest.csv) | Manifesto das GTs: arquivo, URL, autoria, licença, data, categoria e motivo da escolha |
| [`gso/meshes/gt_report.csv`](gso/meshes/gt_report.csv) | Resultado do `check_gt.py` |
| `samples/gt.stl`, `samples/mod.stl` | Par de exemplo, só para demonstração (sem imagem de entrada) |

## Dataset: Google Scanned Objects (GSO)

São escaneamentos reais e texturizados de objetos domésticos e brinquedos, que em geral ficam fora dos dados de treino dos modelos avaliados. É o conjunto **quantitativo**, que dá os números principais, comparáveis com a literatura.

- **Artigo:** Downs et al., 2022, [arXiv:2204.11918](https://arxiv.org/abs/2204.11918v1)
- **Download (Gazebo Fuel, conta `GoogleResearch`):** [coleção Scanned Objects by Google Research](https://app.gazebosim.org/GoogleResearch/fuel/collections/Scanned%20Objects%20by%20Google%20Research)
- **Página de cada objeto:** `https://app.gazebosim.org/GoogleResearch/fuel/models/<gso_name>`. Exemplo: [Schleich_African_Black_Rhino](https://app.gazebosim.org/GoogleResearch/fuel/models/Schleich_African_Black_Rhino)
- **API usada pelo download:** `https://fuel.gazebosim.org/1.0`
- **Licença:** Creative Commons Attribution 4.0 International (CC BY 4.0). Cite a autoria registrada no manifesto.

Não use o Objaverse nem outros conjuntos de treino dos modelos avaliados como GT.

## Seleção atual

A seleção foi feita **à mão**, antes de rodar qualquer modelo. O critério foi alternar corpos lisos com partes finas (asas, chifres, hélices, alças) e incluir alguns casos de controle rígidos ou quase simétricos (ônibus, panda). O artigo precisa declarar esse critério.

| Categoria | Objetos |
| --- | --- |
| Animais | Schleich_African_Black_Rhino, Schleich_Lion_Action_Figure, Schleich_Bald_Eagle, Schleich_Hereford_Bull, Weisshai_Great_White_Shark, Sootheze_Cold_Therapy_Elephant, Breyer_Horse_Of_The_Year_2015 |
| Dinossauros | Schleich_Spinosaurus_Action_Figure, Schleich_Allosaurus, Great_Dinos_Triceratops_Toy |
| Fantasia | Animal_Planet_Foam_2Headed_Dragon, Schleich_S_Bayala_Unicorn_70432 |
| Figuras | Android_Figure_Panda, Nintendo_Yoshi_Action_Figure, Nintendo_Mario_Action_Figure, My_Little_Pony_Princess_Celestia |
| Veículos | Turboprop_Airplane_with_Pilot, SCHOOL_BUS |
| Utensílios | Crosley_Alarm_Clock_Vintage_Metal, Threshold_Porcelain_Teapot_White |

- **Suplentes:** Nickelodeon_Teenage_Mutant_Ninja_Turtles_Leonardo, Elephant, Dino_4, Marvel_Avengers_Titan_Hero_Series_Doctor_Doom.
- **Excluído:** Transformers_Age_of_Extinction_Mega_1Step_Bumblebee_Figure deu WARN no `check_gt.py` (6,7 % da superfície encerrada: faces ocultas ou sobrepostas). Foi trocado pelo primeiro suplente, Great_Dinos_Triceratops_Toy.
- **Checagem atual:** 20 OK, 0 WARN, 0 falhas.

## Conjunto curado

São 10–20 objetos escolhidos à mão: escaneamentos ou modelos próprios, ou publicados depois do corte de treino dos modelos. Servem para figuras e generalização e são reportados em separado. Ainda não estão no repositório, e as GTs próprias em `gt/` ficam fora do Git.

## Como obter os arquivos

Depois de clonar, baixe as malhas do Git LFS:

```bash
git lfs install
git lfs pull
```

Para baixar de novo do Gazebo Fuel e checar as malhas:

```bash
python scripts/fetch_gso.py --out data/gso/meshes
python scripts/check_gt.py --manifest data/gso/meshes/manifest.csv --out data/gso/meshes/gt_report.csv
```
