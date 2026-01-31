"""Tests for proteopy.pl.clustering module."""

import pytest
import warnings
import numpy as np
import pandas as pd
from anndata import AnnData
from scipy.cluster.hierarchy import linkage
from scipy.spatial.distance import pdist
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for testing

from proteopy.pl.clustering import hclustv_silhouette, hclustv_elbow


def _make_protein_adata_with_hclust() -> AnnData:
    """Create protein-level AnnData with pre-computed hclust results."""
    # 6 samples, 5 proteins - enough for meaningful silhouette analysis
    np.random.seed(42)
    X = np.random.rand(6, 5) * 1000

    obs_names = [f"sample{i}" for i in range(6)]
    var_names = [f"protein_{i}" for i in range(5)]
    obs = pd.DataFrame(
        {
            "sample_id": obs_names,
            "condition": ["A", "A", "A", "B", "B", "B"],
        },
        index=obs_names,
    )
    var = pd.DataFrame(
        {"protein_id": var_names},
        index=var_names,
    )
    adata = AnnData(X=X, obs=obs, var=var)

    # Create profile values DataFrame (groups x vars)
    profile_df = pd.DataFrame(
        X,
        index=obs_names,
        columns=var_names,
    )

    # Compute linkage matrix
    clustering_matrix = profile_df.T
    dist_matrix = pdist(clustering_matrix.values, metric="euclidean")
    Z = linkage(dist_matrix, method="average")

    # Store in .uns with standard keys
    adata.uns["hclustv_linkage;condition;abc12345;X"] = Z
    adata.uns["hclustv_values;condition;abc12345;X"] = profile_df

    return adata


def _make_peptide_adata_with_hclust() -> AnnData:
    """Create peptide-level AnnData with pre-computed hclust results."""
    np.random.seed(42)
    X = np.random.rand(4, 6) * 1000

    obs_names = [f"sample{i}" for i in range(4)]
    var_names = [f"pep_{i}" for i in range(6)]
    obs = pd.DataFrame(
        {
            "sample_id": obs_names,
            "condition": ["A", "A", "B", "B"],
        },
        index=obs_names,
    )
    var = pd.DataFrame(
        {
            "peptide_id": var_names,
            "protein_id": ["P1", "P1", "P2", "P2", "P3", "P3"],
        },
        index=var_names,
    )
    adata = AnnData(X=X, obs=obs, var=var)

    profile_df = pd.DataFrame(
        X,
        index=obs_names,
        columns=var_names,
    )
    clustering_matrix = profile_df.T
    dist_matrix = pdist(clustering_matrix.values, metric="euclidean")
    Z = linkage(dist_matrix, method="average")

    adata.uns["hclustv_linkage;condition;def67890;X"] = Z
    adata.uns["hclustv_values;condition;def67890;X"] = profile_df

    return adata


def test_silhouette_scores_basic():
    """Test basic functionality returns axes when ax=True."""
    adata = _make_protein_adata_with_hclust()
    ax_obj = hclustv_silhouette(
        adata, k=4, show=False, ax=True, verbose=False
    )
    assert ax_obj is not None


def test_silhouette_scores_auto_detection(capsys):
    """Test auto-detection of single linkage/values keys."""
    adata = _make_protein_adata_with_hclust()
    ax_obj = hclustv_silhouette(
        adata, k=4, show=False, ax=True, verbose=True
    )

    captured = capsys.readouterr()
    assert "Using linkage matrix" in captured.out
    assert "Using profile values" in captured.out
    assert ax_obj is not None


def test_silhouette_scores_explicit_keys():
    """Test with explicitly specified keys."""
    adata = _make_protein_adata_with_hclust()
    ax_obj = hclustv_silhouette(
        adata,
        linkage_key="hclustv_linkage;condition;abc12345;X",
        values_key="hclustv_values;condition;abc12345;X",
        k=4,
        show=False,
        ax=True,
        verbose=False,
    )
    assert ax_obj is not None


def test_silhouette_scores_multiple_linkage_keys_error():
    """Test error when multiple linkage keys exist without explicit key."""
    adata = _make_protein_adata_with_hclust()

    # Add a second linkage matrix
    adata.uns["hclustv_linkage;cond2;second;X"] = adata.uns[
        "hclustv_linkage;condition;abc12345;X"
    ].copy()

    with pytest.raises(ValueError, match="Multiple linkage matrices found"):
        hclustv_silhouette(adata, show=False, verbose=False)


def test_silhouette_scores_multiple_values_keys_error():
    """Test error when multiple values keys exist without explicit key."""
    adata = _make_protein_adata_with_hclust()

    # Add a second values DataFrame
    adata.uns["hclustv_values;cond2;second;X"] = adata.uns[
        "hclustv_values;condition;abc12345;X"
    ].copy()

    with pytest.raises(ValueError, match="Multiple profile values found"):
        hclustv_silhouette(adata, show=False, verbose=False)


def test_silhouette_scores_no_linkage_error():
    """Test error when no linkage results are found."""
    X = np.random.rand(4, 5) * 1000
    obs_names = [f"sample{i}" for i in range(4)]
    var_names = [f"protein_{i}" for i in range(5)]
    obs = pd.DataFrame({"sample_id": obs_names}, index=obs_names)
    var = pd.DataFrame({"protein_id": var_names}, index=var_names)
    adata = AnnData(X=X, obs=obs, var=var)

    with pytest.raises(ValueError, match="No hierarchical clustering results"):
        hclustv_silhouette(adata, show=False)


def test_silhouette_scores_no_values_error():
    """Test error when no values DataFrame is found."""
    adata = _make_protein_adata_with_hclust()
    # Remove values but keep linkage
    del adata.uns["hclustv_values;condition;abc12345;X"]

    with pytest.raises(ValueError, match="No profile values found"):
        hclustv_silhouette(adata, show=False, verbose=False)


def test_silhouette_scores_invalid_linkage_key_error():
    """Test error when specified linkage_key doesn't exist."""
    adata = _make_protein_adata_with_hclust()

    with pytest.raises(KeyError, match="not found in adata.uns"):
        hclustv_silhouette(
            adata,
            linkage_key="nonexistent_key",
            show=False,
        )


def test_silhouette_scores_invalid_values_key_error():
    """Test error when specified values_key doesn't exist."""
    adata = _make_protein_adata_with_hclust()

    with pytest.raises(KeyError, match="not found in adata.uns"):
        hclustv_silhouette(
            adata,
            values_key="nonexistent_key",
            show=False,
        )


def test_silhouette_scores_k_limiting(capsys):
    """Test k is limited when exceeding n_vars."""
    adata = _make_protein_adata_with_hclust()  # 5 proteins, max k = 4

    ax_obj = hclustv_silhouette(
        adata, k=10, show=False, ax=True, verbose=True
    )

    captured = capsys.readouterr()
    assert "exceeds maximum valid clusters" in captured.out
    assert "Limiting to k=4" in captured.out
    assert ax_obj is not None


def test_silhouette_scores_k_less_than_2_error():
    """Test error when k < 2."""
    adata = _make_protein_adata_with_hclust()

    with pytest.raises(ValueError, match="k must be at least 2"):
        hclustv_silhouette(adata, k=1, show=False)


def test_silhouette_scores_peptide_level():
    """Test with peptide-level data."""
    adata = _make_peptide_adata_with_hclust()
    ax_obj = hclustv_silhouette(
        adata, k=5, show=False, ax=True, verbose=False
    )
    assert ax_obj is not None


def test_silhouette_scores_valid_range():
    """Test that silhouette scores are in valid range [-1, 1]."""
    adata = _make_protein_adata_with_hclust()
    ax_obj = hclustv_silhouette(
        adata, k=4, show=False, ax=True, verbose=False
    )

    # Get y-values from the plot
    line = ax_obj.get_lines()[0]
    y_values = line.get_ydata()

    assert all(-1 <= y <= 1 for y in y_values)


def test_silhouette_scores_x_axis_values():
    """Test that x-axis contains correct k values."""
    adata = _make_protein_adata_with_hclust()
    ax_obj = hclustv_silhouette(
        adata, k=4, show=False, ax=True, verbose=False
    )

    # Get x-values from the plot
    line = ax_obj.get_lines()[0]
    x_values = line.get_xdata()

    expected_k_values = [2, 3, 4]
    assert list(x_values) == expected_k_values


def test_silhouette_scores_figsize():
    """Test custom figure size."""
    adata = _make_protein_adata_with_hclust()
    ax_obj = hclustv_silhouette(
        adata, k=4, figsize=(10, 8), show=False, ax=True, verbose=False
    )

    fig = ax_obj.figure
    assert fig.get_figwidth() == 10
    assert fig.get_figheight() == 8


def test_silhouette_scores_no_action_warning():
    """Test warning when show=False, save=None, ax=False."""
    adata = _make_protein_adata_with_hclust()

    with pytest.warns(UserWarning, match="does not do anything"):
        hclustv_silhouette(
            adata, k=4, show=False, save=None, ax=False, verbose=False
        )


def test_silhouette_scores_plot_labels():
    """Test that plot has correct axis labels and title."""
    adata = _make_protein_adata_with_hclust()
    ax_obj = hclustv_silhouette(
        adata, k=4, show=False, ax=True, verbose=False
    )

    assert ax_obj.get_xlabel() == "Number of clusters (k)"
    assert ax_obj.get_ylabel() == "Average silhouette score"
    assert "Silhouette" in ax_obj.get_title()


def test_silhouette_scores_multiple_keys_with_explicit_selection():
    """Test that explicit key selection works when multiple keys exist."""
    adata = _make_protein_adata_with_hclust()

    # Add second set of keys
    adata.uns["hclustv_linkage;cond2;second;X"] = adata.uns[
        "hclustv_linkage;condition;abc12345;X"
    ].copy()
    adata.uns["hclustv_values;cond2;second;X"] = adata.uns[
        "hclustv_values;condition;abc12345;X"
    ].copy()

    # Should work with explicit keys
    ax_obj = hclustv_silhouette(
        adata,
        linkage_key="hclustv_linkage;condition;abc12345;X",
        values_key="hclustv_values;condition;abc12345;X",
        k=4,
        show=False,
        ax=True,
        verbose=False,
    )
    assert ax_obj is not None


def test_silhouette_scores_verbose_false(capsys):
    """Test that verbose=False suppresses output."""
    adata = _make_protein_adata_with_hclust()
    hclustv_silhouette(
        adata, k=4, show=False, ax=True, verbose=False
    )

    captured = capsys.readouterr()
    assert captured.out == ""


# =============================================================================
# Tests for hclustv_elbow
# =============================================================================


def test_elbow_basic():
    """Test basic functionality returns axes when ax=True."""
    adata = _make_protein_adata_with_hclust()
    ax_obj = hclustv_elbow(
        adata, k=4, show=False, ax=True, verbose=False
    )
    assert ax_obj is not None


def test_elbow_auto_detection(capsys):
    """Test auto-detection of single linkage/values keys."""
    adata = _make_protein_adata_with_hclust()
    ax_obj = hclustv_elbow(
        adata, k=4, show=False, ax=True, verbose=True
    )

    captured = capsys.readouterr()
    assert "Using linkage matrix" in captured.out
    assert "Using profile values" in captured.out
    assert ax_obj is not None


def test_elbow_explicit_keys():
    """Test with explicitly specified keys."""
    adata = _make_protein_adata_with_hclust()
    ax_obj = hclustv_elbow(
        adata,
        linkage_key="hclustv_linkage;condition;abc12345;X",
        values_key="hclustv_values;condition;abc12345;X",
        k=4,
        show=False,
        ax=True,
        verbose=False,
    )
    assert ax_obj is not None


def test_elbow_multiple_linkage_keys_error():
    """Test error when multiple linkage keys exist without explicit key."""
    adata = _make_protein_adata_with_hclust()

    adata.uns["hclustv_linkage;cond2;second;X"] = adata.uns[
        "hclustv_linkage;condition;abc12345;X"
    ].copy()

    with pytest.raises(ValueError, match="Multiple linkage matrices found"):
        hclustv_elbow(adata, show=False, verbose=False)


def test_elbow_no_linkage_error():
    """Test error when no linkage results are found."""
    X = np.random.rand(4, 5) * 1000
    obs_names = [f"sample{i}" for i in range(4)]
    var_names = [f"protein_{i}" for i in range(5)]
    obs = pd.DataFrame({"sample_id": obs_names}, index=obs_names)
    var = pd.DataFrame({"protein_id": var_names}, index=var_names)
    adata = AnnData(X=X, obs=obs, var=var)

    with pytest.raises(ValueError, match="No hierarchical clustering results"):
        hclustv_elbow(adata, show=False)


def test_elbow_k_limiting(capsys):
    """Test k is limited when exceeding n_vars."""
    adata = _make_protein_adata_with_hclust()  # 5 proteins, max k = 5

    ax_obj = hclustv_elbow(
        adata, k=10, show=False, ax=True, verbose=True
    )

    captured = capsys.readouterr()
    assert "exceeds maximum valid clusters" in captured.out
    assert "Limiting to k=5" in captured.out
    assert ax_obj is not None


def test_elbow_k_less_than_1_error():
    """Test error when k < 1."""
    adata = _make_protein_adata_with_hclust()

    with pytest.raises(ValueError, match="k must be at least 1"):
        hclustv_elbow(adata, k=0, show=False)


def test_elbow_peptide_level():
    """Test with peptide-level data."""
    adata = _make_peptide_adata_with_hclust()
    ax_obj = hclustv_elbow(
        adata, k=5, show=False, ax=True, verbose=False
    )
    assert ax_obj is not None


def test_elbow_wcss_decreasing():
    """Test that WCSS decreases as k increases."""
    adata = _make_protein_adata_with_hclust()
    ax_obj = hclustv_elbow(
        adata, k=4, show=False, ax=True, verbose=False
    )

    line = ax_obj.get_lines()[0]
    y_values = line.get_ydata()

    # WCSS should generally decrease (or stay same) as k increases
    for i in range(len(y_values) - 1):
        assert y_values[i] >= y_values[i + 1]


def test_elbow_wcss_non_negative():
    """Test that WCSS values are non-negative."""
    adata = _make_protein_adata_with_hclust()
    ax_obj = hclustv_elbow(
        adata, k=4, show=False, ax=True, verbose=False
    )

    line = ax_obj.get_lines()[0]
    y_values = line.get_ydata()

    assert all(y >= 0 for y in y_values)


def test_elbow_x_axis_values():
    """Test that x-axis contains correct k values starting from 1."""
    adata = _make_protein_adata_with_hclust()
    ax_obj = hclustv_elbow(
        adata, k=4, show=False, ax=True, verbose=False
    )

    line = ax_obj.get_lines()[0]
    x_values = line.get_xdata()

    expected_k_values = [1, 2, 3, 4]
    assert list(x_values) == expected_k_values


def test_elbow_figsize():
    """Test custom figure size."""
    adata = _make_protein_adata_with_hclust()
    ax_obj = hclustv_elbow(
        adata, k=4, figsize=(10, 8), show=False, ax=True, verbose=False
    )

    fig = ax_obj.figure
    assert fig.get_figwidth() == 10
    assert fig.get_figheight() == 8


def test_elbow_no_action_warning():
    """Test warning when show=False, save=None, ax=False."""
    adata = _make_protein_adata_with_hclust()

    with pytest.warns(UserWarning, match="does not do anything"):
        hclustv_elbow(
            adata, k=4, show=False, save=None, ax=False, verbose=False
        )


def test_elbow_plot_labels():
    """Test that plot has correct axis labels and title."""
    adata = _make_protein_adata_with_hclust()
    ax_obj = hclustv_elbow(
        adata, k=4, show=False, ax=True, verbose=False
    )

    assert ax_obj.get_xlabel() == "Number of clusters (k)"
    assert "WCSS" in ax_obj.get_ylabel()
    assert "Elbow" in ax_obj.get_title()


def test_elbow_verbose_false(capsys):
    """Test that verbose=False suppresses output."""
    adata = _make_protein_adata_with_hclust()
    hclustv_elbow(
        adata, k=4, show=False, ax=True, verbose=False
    )

    captured = capsys.readouterr()
    assert captured.out == ""


def test_elbow_k_equals_1():
    """Test that k=1 works (single cluster)."""
    adata = _make_protein_adata_with_hclust()
    ax_obj = hclustv_elbow(
        adata, k=1, show=False, ax=True, verbose=False
    )

    line = ax_obj.get_lines()[0]
    x_values = line.get_xdata()
    y_values = line.get_ydata()

    assert list(x_values) == [1]
    assert len(y_values) == 1
    assert y_values[0] >= 0
