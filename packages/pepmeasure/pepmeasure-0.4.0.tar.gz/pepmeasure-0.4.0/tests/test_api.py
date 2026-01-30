import pytest
import plotly.graph_objects as go

from pepmeasure import Calculator
from pepmeasure.features import FEATURES
from pepmeasure.plots import PLOTS
from tests.constants import PEPTIDES, METADATA
from pepmeasure.constants import DATA_PATH, COLORS


def test_simple_init():
    calc = Calculator(
        dataset=PEPTIDES,
        metadata=METADATA,
        seq="SVIDQSRVLNLGPITR",
    )
    assert PEPTIDES.equals(calc.dataset)
    assert METADATA.equals(calc.metadata)
    assert list(METADATA.columns) == calc.metadata_list
    assert METADATA.columns[0] == calc.key_metadata


@pytest.mark.parametrize(
    "dataset",
    [
        PEPTIDES,
        "./data/peptides.txt",
        "./data/peptides.csv",
        DATA_PATH / "peptides.txt",
        DATA_PATH / "peptides.csv",
        pytest.param(
            lambda: open(DATA_PATH / "peptides.txt", "r"), id="dataset_txt_text_file"
        ),
        pytest.param(
            lambda: open(DATA_PATH / "peptides.txt", "rb"), id="dataset_txt_binary_file"
        ),
        pytest.param(
            lambda: open(DATA_PATH / "peptides.csv", "r"), id="dataset_csv_text_file"
        ),
        pytest.param(
            lambda: open(DATA_PATH / "peptides.csv", "rb"), id="dataset_csv_binary_file"
        ),
    ],
)
def test_setup_dataset_input_types(dataset):
    if callable(dataset):
        with dataset() as f:
            calc = Calculator(dataset=f)
    else:
        calc = Calculator(dataset=dataset)

    assert calc.dataset is not None
    assert not calc.dataset.empty
    assert "Sequence" in calc.dataset.columns


@pytest.mark.parametrize(
    "metadata",
    [
        METADATA,
        "./data/metadata.csv",
        DATA_PATH / "metadata.csv",
        pytest.param(
            lambda: open(DATA_PATH / "metadata.csv", "r"), id="metadata_text_file"
        ),
        pytest.param(
            lambda: open(DATA_PATH / "metadata.csv", "rb"), id="metadata_binary_file"
        ),
    ],
)
def test_setup_metadata_input_types(metadata):
    if callable(metadata):
        with metadata() as f:
            calc = Calculator(metadata=f)
    else:
        calc = Calculator(metadata=metadata)

    assert calc.metadata is not None
    assert not calc.metadata.empty


def test_set_feature_params():
    calc = Calculator()
    calc.set_feature_params(gravy=True)
    assert ("gravy", True) in calc.feature_params.items()
    assert ("molecular_weight", False) in calc.feature_params.items()
    assert "self" not in calc.feature_params.keys()


def test_set_plot_params():
    calc = Calculator()
    calc.set_plot_params(hydropathy_profile=True)
    assert ("hydropathy_profile", True) in calc.plot_params.items()
    assert ("titration_curve", False) in calc.plot_params.items()
    assert "self" not in calc.plot_params.keys()


def test_ensure_attrs():
    calc = Calculator()
    with pytest.raises(ValueError) as e:
        calc.get_features()
    assert "not available" in str(e.value)
    calc.setup(dataset=PEPTIDES, seq="SVIDQSRVLNLGPITR")
    with pytest.raises(ValueError) as e:
        calc.get_plots()
    assert "not available" in str(e.value)


def test_get_features_with_params():
    calc = Calculator(dataset=PEPTIDES, feature_params={"gravy": True})
    res = calc.get_features()
    assert len(PEPTIDES.columns) + 1 == len(res.columns)
    expected = calc.gravy(calc.dataset["Sequence"][0])
    assert expected == res["GRAVY"][0]


def test_get_features_without_params():
    calc = Calculator(dataset=PEPTIDES)
    res = calc.get_features()
    assert len(FEATURES) + len(PEPTIDES.columns) == len(res.columns)


def test_get_peptide_features_with_params():
    calc = Calculator(seq="SVIDQSRVLNLGPITR", feature_params={"gravy": True})
    res = calc.get_peptide_features()
    assert 2 == len(res.columns)
    assert 0.075 == res["GRAVY"][0]


def test_get_peptide_features_without_params():
    calc = Calculator(seq="SVIDQSRVLNLGPITR")
    res = calc.get_peptide_features()
    assert len(FEATURES) + 1 == len(res.columns)


def test_get_plots_for_seq_with_params():
    calc = Calculator(
        seq="SVIDQSRVLNLGPITR",
        plot_params={"hydropathy_profile": True},
    )
    plots = calc.get_plots()
    assert 1 == len(plots)
    assert isinstance(plots[0], go.Figure)


def test_get_plots_for_dataset_with_params():
    calc = Calculator(
        dataset=PEPTIDES,
        metadata=METADATA,
        feature_params={"molecular_weight": True},
        plot_params={
            "raincloud": True,
            "raincloud_feature": "Molecular weight",
            "raincloud_group_by": "Group",
            "raincloud_log_scaled": True,
        },
    )
    calc.get_features()
    plots = calc.get_plots()
    assert 1 == len(plots)
    assert isinstance(plots[0], go.Figure)


def test_get_plots_without_params():
    calc = Calculator(dataset=PEPTIDES, metadata=METADATA, seq="SVIDQSRVLNLGPITR")
    calc.get_features()
    plots = calc.get_plots()
    assert len(PLOTS) == len(plots)


def test_get_plots_as_tuple():
    calc = Calculator(dataset=PEPTIDES, metadata=METADATA, seq="SVIDQSRVLNLGPITR")
    calc.get_features()
    plots = calc.get_plots(as_tuple=True)
    assert 2 == len(plots)


@pytest.mark.parametrize("set_by", ["constructor", "setter"])
def test_custom_colors(set_by):
    if set_by == "constructor":
        calc = Calculator(
            dataset=PEPTIDES,
            metadata=METADATA,
            seq="SVIDQSRVLNLGPITR",
            colors=["#a2191f", "#8a3800", "#684e00"],
        )
    else:
        calc = Calculator(
            dataset=PEPTIDES,
            metadata=METADATA,
            seq="SVIDQSRVLNLGPITR",
        )
        calc.set_colors(["#a2191f", "#8a3800", "#684e00"])

    calc.get_features()
    plots = calc.get_plots()
    for plot in plots:
        plot_json = plot.to_json().lower()
        if "raincloud" not in plot_json:
            assert "a2191f" in plot_json


def test_default_colors():
    calc = Calculator(
        dataset=PEPTIDES,
        metadata=METADATA,
        seq="SVIDQSRVLNLGPITR",
    )
    calc.get_features()
    plots = calc.get_plots()
    for plot in plots:
        plot_json = plot.to_json().lower()
        if "raincloud" not in plot_json:
            assert COLORS[0][1:].lower() in plot_json
