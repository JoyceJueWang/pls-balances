import click
import numpy as np
import pandas as pd
from biom import load_table
from skbio.stats.composition import ancom
from skbio.stats.composition import (clr, centralize,
                                     multiplicative_replacement)
from sklearn.cross_decomposition import PLSRegression
from pls_balances.src.balances import round_balance


@click.group()
def run():
    pass

@run.command()
@click.option('--table-file',
              help='Input biom table of abundances')
@click.option('--metadata-file',
              help='Input metadata file')
@click.option('--category',
              help='Category specifying groups')
@click.option('--output-file',
              help='output file of differientially abundance features.')
def pls_balances_cmd(table_file, metadata_file, category, output_file):
    metadata = pd.read_table(metadata_file, index_col=0)
    table = load_table(table_file)
    table = pd.DataFrame(np.array(table.matrix_data.todense()).T,
                         index=table.ids(axis='sample'),
                         columns=table.ids(axis='observation'))

    ctable = pd.DataFrame(clr(centralize(table+1)),
                      index=table.index, columns=table.columns)

    rfc = PLSRegression(n_components=1)
    cats = np.unique(metadata[category])
    groups = (metadata[category] == cats[0]).astype(np.int)
    rfc.fit(X=ctable.values, Y=groups)

    pls_df = pd.DataFrame(rfc.x_weights_,
                          index=ctable.columns, columns=['PLS1'])
    l, r = round_balance(pls_df.values,
                         means_init=[[pls_df.PLS1.min()],
                                     [0],
                                     [pls_df.PLS1.max()]],
                         n_init=100)
    num = pls_df.loc[pls_df.PLS1 > r]
    denom = pls_df.loc[pls_df.PLS1 < l]
    diff_features = list(num.index.values)
    diff_features += list(denom.index.values)

    with open(output_file, 'w') as f:
        f.write(','.join(diff_features))


@run.command()
@click.option('--table-file',
              help='Input biom table of abundances')
@click.option('--metadata-file',
              help='Input metadata file')
@click.option('--category',
              help='Category specifying groups')
@click.option('--output-file',
              help='output file of differientially abundance features.')
def ancom_cmd(table_file, metadata_file, category, output_file):
    metadata = pd.read_table(metadata_file, index_col=0)
    table = load_table(table_file)
    table = pd.DataFrame(np.array(table.matrix_data.todense()).T,
                         index=table.ids(axis='sample'),
                         columns=table.ids(axis='observation'))
    res, _ = ancom(table+1, grouping=metadata[category])
    with open(output_file, 'w') as f:
        r = res["Reject null hypothesis"]
        f.write(','.join(res.loc[r].index.values))


if __name__ == "__main__":
    run()