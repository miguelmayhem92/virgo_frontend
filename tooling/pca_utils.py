import operator

import numpy as np 
import pandas as pd 
import matplotlib.pyplot as plt

from sklearn.linear_model import LinearRegression

import fastcluster
from scipy.cluster import hierarchy
import seaborn as sns


def compute_sorted_correlations(returns, corr_estimator='pearson'):
    corr = returns.corr(method=corr_estimator)
    dist = 1 - corr.values
    tri_a, tri_b = np.triu_indices(len(dist), k=1) # indices of upper triangle
    linkage = fastcluster.linkage(dist[tri_a, tri_b], method='ward') # just upper triangle of the dist matrix then links
    permutation = hierarchy.leaves_list(
        hierarchy.optimal_leaf_ordering(linkage, dist[tri_a, tri_b])
    )
    sorted_coins = returns.columns[permutation]
    sorted_corrs = corr.values[permutation, :][:, permutation]

    return pd.DataFrame(sorted_corrs, index=sorted_coins, columns=sorted_coins)

def produce_clusters(n_clusters, correlation_matrix):
    dist = 1 - correlation_matrix.values
    dim = len(dist)
    tri_a, tri_b = np.triu_indices(dim, k=1)
    linkage = fastcluster.linkage(dist[tri_a, tri_b], method='ward')
    clustering_inds = hierarchy.fcluster(linkage, n_clusters, criterion='maxclust')
    clusters = {i: [] for i in range(min(clustering_inds), max(clustering_inds) + 1)}
    for i, v in enumerate(clustering_inds):
        clusters[v].append(i)
    return clusters

def sort_clusters(clusters):
    permutation = sorted([(min(elems), c) for c, elems in clusters.items()],
                         key=lambda x: x[0], reverse=False)
    sorted_clusters = {}
    for cluster in clusters:
        sorted_clusters[cluster] = clusters[permutation[cluster - 1][1]]
    return sorted_clusters

def plot_cluster(clusters, correlations, display=False):
    order = list(correlations.columns)
    order = order.copy()
    order = list(reversed(order))
    dim = len(correlations)
    fig = plt.figure(figsize=(10, 10))
    _ = sns.heatmap(correlations.loc[order,:].round(2), annot=True, cmap='RdYlGn',center=0)
    for cluster_id, cluster in clusters.items():
        xmin, xmax = min(cluster), max(cluster) # fix
        ymin, ymax = min(cluster), max(cluster)
        plt.axvline(x=xmin,
                    ymin=ymin / dim, ymax=(ymax + 1) / dim,
                    color='black')
        plt.axvline(x=xmax + 1,
                    ymin=ymin / dim, ymax=(ymax + 1) / dim,
                    color='black')
        
        plt.axhline(y=dim - ymin,
                    xmin=xmin / dim, xmax=(xmax + 1) / dim,
                    color='black')
        plt.axhline(y=dim - ymax - 1, 
                    xmin=xmin / dim, xmax=(xmax + 1) / dim,
                    color='black')
    plt.tight_layout()
    if display:
        plt.show()
    else:
        plt.close()
    return fig

def get_eigen_clusters(clusters, correlations, returns):
    eigen_clusters = {}
    for cluster in clusters:
        cluster_members = correlations.columns[  # get the assets of a given cluster
            clusters[cluster]].tolist()
        corr_cluster = correlations.loc[ # the bos or cluster members
            cluster_members, cluster_members]

        cluster_returns = returns[cluster_members]

        eigenvals, eigenvecs = np.linalg.eig(corr_cluster.values)  # getting eigen vector and eigen values from a cluster correlation matrix which changes dim depending on cluster
        # vals are the matrix shr
        # vec it is representation

        idx = eigenvals.argsort()[::-1] # reverser sorting of indices
        eigenvals = eigenvals[idx] # re arrange the velues
        eigenvecs = eigenvecs[:, idx] # re arrange the vectors
        #
        val1 = eigenvals[0] # first value
        vec1 = eigenvecs[:, 0] # first vector
        F1 = (1 / np.sqrt(val1)) * np.multiply(vec1, cluster_returns.values).sum(axis=1)

        eigen_clusters[cluster] = {
            'tickers': cluster_members,
            'val1': val1,
            'vec1': vec1,
            'F1': F1,}
    return eigen_clusters

def get_coin_to_cluster(clusters, correlations):
    coin_to_cluster = {}
    for cluster in clusters:
        cluster_members = correlations.columns[clusters[cluster]].tolist()
        for coin in cluster_members:
            coin_to_cluster[coin] = cluster
    return coin_to_cluster

def get_betas(eigen_clusters, returns, coin_to_cluster):
    betas = {}
    for coin in returns.columns: # coin or asset

        coin_returns = returns[coin] # asset return
        cluster_F1 = eigen_clusters[coin_to_cluster[coin]]['F1'] # ge f1 of a given asset (knowing that every assets is part of a cluster)

        # reshape the f1 score so that linreg can fit it, using returns as target
        reg = LinearRegression(fit_intercept=False).fit(
            cluster_F1.reshape(-1, 1), coin_returns)

        beta = reg.coef_[0] # get beta

        betas[coin] = beta
    return betas

def get_hpca_correlations(correlations, coin_to_cluster, betas, eigen_clusters):
    # hpca correlations, using previous pca values and clusters, compute new correlation matrix
    HPCA_corr = correlations.copy()
    for coin_1 in HPCA_corr.columns:  # assets
        beta_1 = betas[coin_1]  # get beta  from an asset
        F1_1 = eigen_clusters[coin_to_cluster[coin_1]]['F1']  # get F1 from an asset
        for coin_2 in HPCA_corr.columns:  # get asset
            beta_2 = betas[coin_2]  # get beta  from an asset
            F1_2 = eigen_clusters[coin_to_cluster[coin_2]]['F1']  # get F1 from an asset
            if coin_to_cluster[coin_1] != coin_to_cluster[coin_2]:  # compute if assets are different
                rho_sector = np.corrcoef(F1_1, F1_2)[0, 1]  # get corr coef
                mod_rho = beta_1 * beta_2 * rho_sector  # get mod
                HPCA_corr.at[coin_1, coin_2] = mod_rho  # replace the correlation in the matrix with the new value
    return HPCA_corr

def get_cluster_members(clusters, correlations):
    header = list(correlations.columns)
    func_l = lambda v: [header[i] for i in v]
    return {k:func_l(v) for k,v in clusters.items()}