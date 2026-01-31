import pytest
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mimage
from clustermap_imshow import apply_patch


def test_patch_applied():
    """Test that the patch is correctly applied to seaborn."""
    import seaborn.matrix as sm
    original_plot = sm._HeatMapper.plot
    apply_patch()
    assert sm._HeatMapper.plot != original_plot
    assert sm._HeatMapper.plot.__name__ == "imshow_plot"


def test_clustermap_runs_with_patch():
    """Test that clustermap runs without error after patching."""
    apply_patch()
    data = np.random.rand(10, 10)
    try:
        g = sns.clustermap(data)
        plt.close(g.fig)
    except Exception as e:
        pytest.fail(f"clustermap failed with patch: {e}")


def test_imshow_used():
    """Test that an AxesImage (from imshow) is created instead of a QuadMesh."""
    apply_patch()
    data = np.random.rand(10, 10)
    g = sns.clustermap(data)
    # Check if any AxesImage exists in the heatmap axes
    images = [child for child in g.ax_heatmap.get_children() if isinstance(child, mimage.AxesImage)]
    assert len(images) > 0, "No AxesImage found in heatmap axes"

    plt.close(g.fig)


def test_annotations_work():
    """Test that annotations still work with the patch."""
    apply_patch()
    data = np.random.rand(5, 5)
    g = sns.clustermap(data, annot=True)
    # Check for text objects in the heatmap axes
    texts = [child for child in g.ax_heatmap.get_children() if isinstance(child, plt.Text)]
    # Seaborn adds some texts for labels, but annotations should be many more
    assert len(texts) > 25, "Annotations not found in heatmap axes"
    plt.close(g.fig)
