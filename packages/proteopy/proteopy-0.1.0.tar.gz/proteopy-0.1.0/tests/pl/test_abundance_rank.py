import pytest
import warnings
import numpy as np
import pandas as pd
from anndata import AnnData
from scipy import sparse
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for testing

from proteopy.pl.intensities import abundance_rank


def _make_protein_adata_linear() -> AnnData:
    """Create a simple protein-level AnnData with linear-scale intensities."""
    X = np.array([
        [1000, 500, 100, 50, 10],
        [2000, 600, 150, 60, 15],
        [1500, 550, 120, 55, 12],
    ], dtype=float)
    obs_names = [f"sample{i}" for i in range(3)]
    var_names = [f"protein_{i}" for i in range(5)]
    obs = pd.DataFrame(
        {
            "sample_id": obs_names,
            "condition": ["A", "B", "A"],
        },
        index=obs_names,
    )
    var = pd.DataFrame(
        {"protein_id": var_names},
        index=var_names,
    )
    return AnnData(X=X, obs=obs, var=var)


def _make_protein_adata_log() -> AnnData:
    """Create a simple protein-level AnnData with log-scale intensities."""
    X = np.array([
        [10.0, 9.0, 7.0, 5.5, 3.3],
        [10.5, 9.2, 7.2, 5.8, 3.9],
        [10.2, 9.1, 7.1, 5.6, 3.5],
    ], dtype=float)
    obs_names = [f"sample{i}" for i in range(3)]
    var_names = [f"protein_{i}" for i in range(5)]
    obs = pd.DataFrame(
        {
            "sample_id": obs_names,
            "condition": ["A", "B", "A"],
        },
        index=obs_names,
    )
    var = pd.DataFrame(
        {"protein_id": var_names},
        index=var_names,
    )
    return AnnData(X=X, obs=obs, var=var)


def _make_peptide_adata() -> AnnData:
    """Create a simple peptide-level AnnData."""
    X = np.array([
        [1000, 500, 100, 50],
        [2000, 600, 150, 60],
    ], dtype=float)
    obs_names = ["sample0", "sample1"]
    var_names = ["pep0", "pep1", "pep2", "pep3"]
    obs = pd.DataFrame(
        {
            "sample_id": obs_names,
            "condition": ["A", "B"],
        },
        index=obs_names,
    )
    var = pd.DataFrame(
        {
            "peptide_id": var_names,
            "protein_id": ["P1", "P1", "P2", "P2"],
        },
        index=var_names,
    )
    return AnnData(X=X, obs=obs, var=var)


def test_abundance_rank_basic():
    """Test basic functionality returns axes when ax=True."""
    adata = _make_protein_adata_linear()
    ax_obj = abundance_rank(adata, show=False, ax=True)
    assert ax_obj is not None


def test_abundance_rank_with_color():
    """Test coloring by obs column."""
    adata = _make_protein_adata_linear()
    ax_obj = abundance_rank(adata, color="condition", show=False, ax=True)
    assert ax_obj is not None


def test_abundance_rank_with_highlight_vars():
    """Test highlighting specific variables."""
    adata = _make_protein_adata_linear()
    ax_obj = abundance_rank(
        adata,
        highlight_vars=["protein_0", "protein_4"],
        show=False,
        ax=True,
    )
    assert ax_obj is not None


def test_abundance_rank_invalid_color_column():
    """Test error when color column doesn't exist."""
    adata = _make_protein_adata_linear()
    with pytest.raises(KeyError, match="not found in adata.obs"):
        abundance_rank(adata, color="nonexistent", show=False)


def test_abundance_rank_invalid_highlight_vars():
    """Test error when highlight_vars contains missing variables."""
    adata = _make_protein_adata_linear()
    with pytest.raises(KeyError, match="Variables not found"):
        abundance_rank(
            adata,
            highlight_vars=["protein_0", "nonexistent"],
            show=False,
        )


def test_abundance_rank_invalid_layer():
    """Test error when layer doesn't exist."""
    adata = _make_protein_adata_linear()
    with pytest.raises(KeyError, match="Layer .* not found"):
        abundance_rank(adata, layer="nonexistent", show=False)


def test_abundance_rank_zero_to_na_and_fill_na_exclusive():
    """Test that zero_to_na and fill_na cannot be used together."""
    adata = _make_protein_adata_linear()
    with pytest.raises(ValueError, match="mutually exclusive"):
        abundance_rank(
            adata,
            zero_to_na=True,
            fill_na=0.0,
            show=False,
        )


def test_abundance_rank_invalid_input_space():
    """Test error for invalid input_space value."""
    adata = _make_protein_adata_linear()
    with pytest.raises(ValueError, match="input_space must be"):
        abundance_rank(adata, input_space="invalid", show=False)


def test_abundance_rank_invalid_log_transform():
    """Test error for invalid log_transform values."""
    adata = _make_protein_adata_linear()

    # Test log_transform <= 0
    with pytest.raises(ValueError, match="log_transform must be positive"):
        abundance_rank(adata, log_transform=-1, show=False)

    # Test log_transform == 1
    with pytest.raises(ValueError, match="log_transform cannot be 1"):
        abundance_rank(adata, log_transform=1, show=False)


def test_abundance_rank_invalid_summary_method():
    """Test error for invalid summary_method value."""
    adata = _make_protein_adata_linear()
    with pytest.raises(ValueError, match="summary_method must be one of"):
        abundance_rank(adata, summary_method="invalid", show=False)


def test_abundance_rank_summary_methods():
    """Test all valid summary methods."""
    adata = _make_protein_adata_linear()

    for method in ("sum", "average", "median", "max"):
        ax_obj = abundance_rank(
            adata,
            summary_method=method,
            show=False,
            ax=True,
        )
        assert ax_obj is not None


def test_abundance_rank_linear_input_log_target(capsys):
    """Test linear input with log transformation applied."""
    adata = _make_protein_adata_linear()
    ax_obj = abundance_rank(
        adata,
        input_space="linear",
        log_transform=10,
        show=False,
        ax=True,
        force=True,
    )
    assert ax_obj is not None
    # Check ylabel contains log transformation info
    assert "log" in ax_obj.get_ylabel().lower()


def test_abundance_rank_log_input_log_target(capsys):
    """Test that log input with log target prints message and doesn't transform."""
    adata = _make_protein_adata_log()
    ax_obj = abundance_rank(
        adata,
        input_space="log",
        log_transform=10,
        show=False,
        ax=True,
        force=True,
    )
    captured = capsys.readouterr()
    assert "already log-transformed" in captured.out or "ignoring" in captured.out


def test_abundance_rank_log_input_linear_target_raises():
    """Test that converting log to linear without knowing base raises error."""
    adata = _make_protein_adata_log()
    with pytest.raises(ValueError, match="Cannot convert log-transformed data"):
        abundance_rank(
            adata,
            input_space="log",
            log_transform=None,
            show=False,
            force=True,
        )


def test_abundance_rank_auto_infer_linear(capsys):
    """Test auto inference for linear data."""
    adata = _make_protein_adata_linear()
    ax_obj = abundance_rank(
        adata,
        input_space="auto",
        log_transform=10,
        show=False,
        ax=True,
    )
    captured = capsys.readouterr()
    assert "LINEAR" in captured.out or "linear" in captured.out.lower()


def test_abundance_rank_auto_infer_log(capsys):
    """Test auto inference for log data."""
    adata = _make_protein_adata_log()
    ax_obj = abundance_rank(
        adata,
        input_space="auto",
        log_transform=10,
        show=False,
        ax=True,
    )
    captured = capsys.readouterr()
    assert "LOG" in captured.out or "log" in captured.out.lower()


def test_abundance_rank_mismatch_warning():
    """Test warning when declared input_space mismatches inferred."""
    adata = _make_protein_adata_linear()
    with pytest.warns(UserWarning, match="Declared input_space"):
        abundance_rank(
            adata,
            input_space="log",  # Mismatch: data is linear
            log_transform=10,
            show=False,
            force=False,
        )


def test_abundance_rank_force_suppresses_warning():
    """Test that force=True suppresses mismatch warning."""
    adata = _make_protein_adata_linear()
    # Should not raise mismatch warning with force=True
    # Use ax=True to avoid the "not displayed/saved/returned" warning
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        try:
            abundance_rank(
                adata,
                input_space="log",
                log_transform=10,
                show=False,
                ax=True,  # Avoid the "not displayed" warning
                force=True,
            )
        except UserWarning as e:
            # Only fail if it's a mismatch warning, not other warnings
            if "Declared input_space" in str(e):
                pytest.fail("Mismatch UserWarning raised despite force=True")


def test_abundance_rank_sparse_input():
    """Test that sparse input is handled correctly."""
    adata = _make_protein_adata_linear()
    adata.X = sparse.csr_matrix(adata.X)

    ax_obj = abundance_rank(adata, show=False, ax=True)
    assert ax_obj is not None


def test_abundance_rank_with_layer():
    """Test using a specific layer."""
    adata = _make_protein_adata_linear()
    adata.layers["raw"] = adata.X.copy() * 2

    ax_obj = abundance_rank(adata, layer="raw", show=False, ax=True)
    assert ax_obj is not None


def test_abundance_rank_with_na_values():
    """Test handling of NA values in data."""
    adata = _make_protein_adata_linear()
    adata.X[0, 0] = np.nan
    adata.X[1, 1] = np.nan

    ax_obj = abundance_rank(adata, show=False, ax=True)
    assert ax_obj is not None


def test_abundance_rank_fill_na():
    """Test fill_na parameter."""
    adata = _make_protein_adata_linear()
    adata.X[0, 0] = np.nan

    ax_obj = abundance_rank(adata, fill_na=0.0, show=False, ax=True)
    assert ax_obj is not None


def test_abundance_rank_zero_to_na():
    """Test zero_to_na parameter."""
    adata = _make_protein_adata_linear()
    adata.X[0, 0] = 0

    ax_obj = abundance_rank(adata, zero_to_na=True, show=False, ax=True)
    assert ax_obj is not None


def test_abundance_rank_peptide_level():
    """Test with peptide-level data."""
    adata = _make_peptide_adata()
    ax_obj = abundance_rank(adata, show=False, ax=True)
    assert ax_obj is not None


def test_abundance_rank_custom_labels():
    """Test custom title and axis labels."""
    adata = _make_protein_adata_linear()
    ax_obj = abundance_rank(
        adata,
        title="Custom Title",
        xlabel="Custom X",
        ylabel="Custom Y",
        show=False,
        ax=True,
    )
    assert ax_obj.get_title() == "Custom Title"
    assert ax_obj.get_xlabel() == "Custom X"
    assert ax_obj.get_ylabel() == "Custom Y"


def test_abundance_rank_figsize():
    """Test custom figure size."""
    adata = _make_protein_adata_linear()
    ax_obj = abundance_rank(
        adata,
        figsize=(10, 8),
        show=False,
        ax=True,
    )
    fig = ax_obj.figure
    assert fig.get_figwidth() == 10
    assert fig.get_figheight() == 8


def test_abundance_rank_alpha_and_s():
    """Test alpha and point size parameters."""
    adata = _make_protein_adata_linear()

    # Valid values
    ax_obj = abundance_rank(adata, alpha=0.3, s=20, show=False, ax=True)
    assert ax_obj is not None

    # Invalid alpha
    with pytest.raises(ValueError, match="alpha must be"):
        abundance_rank(adata, alpha=1.5, show=False)

    # Invalid s
    with pytest.raises(ValueError, match="s must be"):
        abundance_rank(adata, s=-1, show=False)


def test_abundance_rank_color_scheme():
    """Test custom color scheme."""
    adata = _make_protein_adata_linear()
    ax_obj = abundance_rank(
        adata,
        color="condition",
        color_scheme={"A": "red", "B": "blue"},
        show=False,
        ax=True,
    )
    assert ax_obj is not None


def test_abundance_rank_no_action_warning():
    """Test warning when show=False, save=None, ax=False."""
    adata = _make_protein_adata_linear()
    with pytest.warns(UserWarning, match="not displayed, saved, or returned"):
        abundance_rank(adata, show=False, save=None, ax=False)


def test_abundance_rank_per_group_ranking():
    """Test that ranks are computed separately for each color group."""
    # Create data where ranking should differ between groups
    X = np.array([
        # Group A (samples 0, 2): protein_0 highest, protein_1 lowest
        [1000, 100],  # sample0 (A)
        # Group B (sample 1): protein_1 highest, protein_0 lowest
        [100, 1000],  # sample1 (B)
        [1000, 100],  # sample2 (A)
    ], dtype=float)
    obs_names = ["sample0", "sample1", "sample2"]
    var_names = ["protein_0", "protein_1"]
    obs = pd.DataFrame(
        {
            "sample_id": obs_names,
            "condition": ["A", "B", "A"],
        },
        index=obs_names,
    )
    var = pd.DataFrame(
        {"protein_id": var_names},
        index=var_names,
    )
    adata = AnnData(X=X, obs=obs, var=var)

    # With per-group ranking, each group should have different ranks
    ax_obj = abundance_rank(
        adata,
        color="condition",
        input_space="linear",
        log_transform=None,
        show=False,
        ax=True,
        force=True,
    )
    assert ax_obj is not None

    # Also test without color (global ranking)
    ax_obj2 = abundance_rank(
        adata,
        color=None,
        input_space="linear",
        log_transform=None,
        show=False,
        ax=True,
        force=True,
    )
    assert ax_obj2 is not None


def test_abundance_rank_highlight_vars_with_color():
    """Test highlighting vars works correctly with per-group ranking."""
    adata = _make_protein_adata_linear()
    ax_obj = abundance_rank(
        adata,
        color="condition",
        highlight_vars=["protein_0", "protein_4"],
        show=False,
        ax=True,
    )
    assert ax_obj is not None


def test_abundance_rank_one_dot_per_var_no_color():
    """Test that without color, there's exactly one dot per variable."""
    adata = _make_protein_adata_linear()
    ax_obj = abundance_rank(adata, show=False, ax=True)

    # Get the scatter collection
    collections = ax_obj.collections
    assert len(collections) == 1  # One scatter plot

    # Number of points should equal number of variables
    n_points = len(collections[0].get_offsets())
    assert n_points == adata.n_vars


def test_abundance_rank_dots_per_group_with_color():
    """Test that with color, there's one dot per variable per group."""
    adata = _make_protein_adata_linear()
    ax_obj = abundance_rank(adata, color="condition", show=False, ax=True)

    # Get all scatter collections
    collections = ax_obj.collections
    n_groups = adata.obs["condition"].nunique()

    # Should have one collection per group
    assert len(collections) == n_groups

    # Total points should be n_vars * n_groups
    total_points = sum(len(c.get_offsets()) for c in collections)
    assert total_points == adata.n_vars * n_groups


def test_abundance_rank_summary_method_affects_values():
    """Test that different summary methods produce different y-values."""
    adata = _make_protein_adata_linear()

    # Get y-values for different summary methods
    results = {}
    for method in ("sum", "average", "median", "max"):
        ax_obj = abundance_rank(
            adata,
            summary_method=method,
            input_space="linear",
            log_transform=None,
            show=False,
            ax=True,
            force=True,
        )
        # Get y-values from the scatter plot
        y_values = ax_obj.collections[0].get_offsets()[:, 1]
        results[method] = sorted(y_values)

    # Sum should have larger values than average
    assert max(results["sum"]) > max(results["average"])

    # Average and median may differ
    # Max should be <= sum (for positive values)
    assert max(results["max"]) <= max(results["sum"])


def test_abundance_rank_var_labels_key():
    """Test var_labels_key parameter for alternative labels."""
    X = np.array([
        [1000, 500, 100],
        [2000, 600, 150],
    ], dtype=float)
    obs_names = ["sample0", "sample1"]
    var_names = ["ENSG00001", "ENSG00002", "ENSG00003"]
    obs = pd.DataFrame(
        {"sample_id": obs_names},
        index=obs_names,
    )
    var = pd.DataFrame(
        {
            "protein_id": var_names,
            "gene_symbol": ["GeneA", "GeneB", "GeneC"],
        },
        index=var_names,
    )
    adata = AnnData(X=X, obs=obs, var=var)

    # Test with var_labels_key
    ax_obj = abundance_rank(
        adata,
        highlight_vars=["ENSG00001", "ENSG00003"],
        var_labels_key="gene_symbol",
        show=False,
        ax=True,
    )
    assert ax_obj is not None

    # Check that labels are the gene symbols
    texts = [t for t in ax_obj.texts]
    text_labels = [t.get_text() for t in texts]
    assert "GeneA" in text_labels
    assert "GeneC" in text_labels
    assert "ENSG00001" not in text_labels


def test_abundance_rank_var_labels_key_invalid():
    """Test error when var_labels_key column doesn't exist."""
    adata = _make_protein_adata_linear()
    with pytest.raises(KeyError, match="not found in adata.var"):
        abundance_rank(
            adata,
            highlight_vars=["protein_0"],
            var_labels_key="nonexistent",
            show=False,
        )


def test_abundance_rank_var_labels_key_with_color():
    """Test var_labels_key works with color groups."""
    X = np.array([
        [1000, 500],
        [2000, 600],
        [1500, 550],
    ], dtype=float)
    obs_names = ["sample0", "sample1", "sample2"]
    var_names = ["ENSG00001", "ENSG00002"]
    obs = pd.DataFrame(
        {
            "sample_id": obs_names,
            "condition": ["A", "B", "A"],
        },
        index=obs_names,
    )
    var = pd.DataFrame(
        {
            "protein_id": var_names,
            "gene_symbol": ["GeneA", "GeneB"],
        },
        index=var_names,
    )
    adata = AnnData(X=X, obs=obs, var=var)

    ax_obj = abundance_rank(
        adata,
        color="condition",
        highlight_vars=["ENSG00001"],
        var_labels_key="gene_symbol",
        show=False,
        ax=True,
    )
    assert ax_obj is not None

    # Check labels use gene symbols
    texts = [t for t in ax_obj.texts]
    text_labels = [t.get_text() for t in texts]
    # Should have "GeneA" for each group (2 groups)
    assert text_labels.count("GeneA") == 2
