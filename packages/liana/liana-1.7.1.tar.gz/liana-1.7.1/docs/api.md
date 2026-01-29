# API

Import liana as:

```python
import liana as li
```

## Single-cell

### Callable Ligand-Receptor Method instances

Ligand-receptor method instances provide helper functions and consistent
attributes, to describe each method instance, and are callable:

```{eval-rst}
.. module:: liana.method
.. currentmodule:: liana.method

.. autosummary::
    :toctree: generated

    cellchat.__call__
    cellphonedb.__call__
    connectome.__call__
    logfc.__call__
    natmi.__call__
    singlecellsignalr.__call__
    geometric_mean.__call__
    rank_aggregate.__call__
```

## Spatial

### Local bivariate metrics

```{eval-rst}
.. module:: liana.method
.. currentmodule:: liana.method

.. autosummary::
    :toctree: generated

    bivariate.__call__
```

### Learn Spatial Relationships

```{eval-rst}
.. module:: liana.method
.. currentmodule:: liana.method

.. autosummary::
    :toctree: generated

    MistyData
    genericMistyData
    lrMistyData
```

## Multi-Sample

```{eval-rst}
.. module:: liana.multi
.. currentmodule:: liana.multi

.. autosummary::
    :toctree: generated

    df_to_lr
    to_tensor_c2c
    adata_to_views
    lrs_to_views
    nmf
    estimate_elbow
```

## Visualization

```{eval-rst}
.. module:: liana.plotting
.. currentmodule:: liana.plotting

.. autosummary::
    :toctree: generated

    dotplot
    dotplot_by_sample
    tileplot
    connectivity
    target_metrics
    contributions
    interactions
```

## Utility

```{eval-rst}
.. module:: liana.utils
.. currentmodule:: liana.utils

.. autosummary::
    :toctree: generated

    obsm_to_adata
    mdata_to_anndata
    zi_minmax
    neg_to_zero
    spatial_neighbors
    get_factor_scores
    get_variable_loadings
    interpolate_adata
```

## Prior knowledge

```{eval-rst}
.. module:: liana.resource
.. currentmodule:: liana.resource

.. autosummary::
    :toctree: generated

    select_resource
    show_resources
    generate_lr_geneset
    explode_complexes
    get_metalinks
    describe_metalinks
    get_metalinks_values
```

## Intracellular

```{eval-rst}
.. module:: liana.method
.. currentmodule:: liana.method

.. autosummary::
    :toctree: generated

    find_causalnet
    build_prior_network
    estimate_metalinks
```
