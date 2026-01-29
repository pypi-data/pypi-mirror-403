import pathlib
from itertools import product
from os import path
from unittest import TestCase

from pandas import read_csv
from pandas.testing import assert_frame_equal

from liana.method import rank_aggregate
from liana.method.sc._rank_aggregate import AggregateClass
from liana.testing._sample_anndata import generate_toy_adata, generate_toy_mdata

test_path = pathlib.Path(__file__).parent

def test_consensus_meta():
    assert isinstance(rank_aggregate, AggregateClass)
    assert rank_aggregate.magnitude == 'magnitude_rank'
    assert rank_aggregate.specificity == 'specificity_rank'
    assert rank_aggregate.method_name == 'Rank_Aggregate'


def test_aggregate_specs():
    specificity_specs = {'CellPhoneDB': ('cellphone_pvals', True),
                         'Connectome': ('scaled_weight', False),
                         'log2FC': ('lr_logfc', False),
                         'NATMI': ('spec_weight', False),
                    }
    TestCase().assertDictEqual(rank_aggregate.specificity_specs, specificity_specs)

    magnitude_specs = {'CellPhoneDB': ('lr_means', False),
                       'Connectome': ('expr_prod', False),
                       'NATMI': ('expr_prod', False),
                       'SingleCellSignalR': ('lrscore', False),
                       }

    TestCase().assertDictEqual(rank_aggregate.magnitude_specs, magnitude_specs)


def test_aggregate_res():
    adata = generate_toy_adata()
    lr_res = rank_aggregate(adata, groupby='bulk_labels', n_perms=2,
                            seed=1337, inplace=False, n_jobs=1)
    lr_exp = read_csv(test_path.joinpath(path.join("data", "aggregate_rank_rest.csv")), index_col=0)
    lr_res = lr_res.sort_values(by=list(lr_res.columns))
    lr_exp = lr_exp.sort_values(by=list(lr_res.columns))
    lr_res.index = lr_exp.index
    assert_frame_equal(lr_res, lr_exp, check_dtype=False, check_exact=False, rtol=1e-4, atol=1e-6)


def test_aggregate_all():
    adata = generate_toy_adata()
    rank_aggregate(adata,
                   groupby='bulk_labels',
                   aggregate_method='mean',
                   return_all_lrs=True,
                   seed=1,
                   n_perms=2,
                   n_jobs=1,
                   key_added='all_res')
    assert adata.uns['all_res'].shape == (4200, 13)


def test_aggregate_by_sample():
    adata = generate_toy_adata()
    rank_aggregate.by_sample(adata, groupby='bulk_labels', n_jobs=1, n_perms=2,
                             return_all_lrs=True, sample_key='sample',
                             key_added='liana_by_sample')
    lr_by_sample = adata.uns['liana_by_sample']

    assert 'sample' in lr_by_sample.columns
    assert lr_by_sample.shape == (10836, 14)

def test_aggregate_no_perms():
    adata = generate_toy_adata()
    rank_aggregate(adata, groupby='bulk_labels',
                   return_all_lrs=True, key_added='all_res',
                   n_perms=None)
    assert adata.uns['all_res'].shape == (4200, 11)

def test_aggregate_on_mdata():
    mdata = generate_toy_mdata()
    mdata.mod['adata_y'].var.index = 'scaled:' + mdata.mod['adata_y'].var.index
    interactions = list(product(mdata.mod['adata_x'].var.index, mdata.mod['adata_y'].var.index))
    interactions = interactions[0:10]

    rank_aggregate(mdata,
                   groupby='bulk_labels',
                   n_perms=None,
                   mdata_kwargs={
                       'x_mod': 'adata_x',
                       'y_mod': 'adata_y',
                       'x_transform': False,
                       'y_transform': False
                   },
                   use_raw=False,
                   interactions=interactions,
                   verbose=True)

    assert mdata.uns['liana_res'].shape == (132, 11)
