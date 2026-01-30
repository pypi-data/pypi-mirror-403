import pytest

from pepmeasure.maxquant import _convert_peptide_txt
from pepmeasure.constants import DATA_PATH


@pytest.mark.parametrize(
    "dataset",
    [
        "./data/peptides.txt",
        DATA_PATH / "peptides.txt",
        pytest.param(lambda: open(DATA_PATH / "peptides.txt", "r"), id="text_file"),
        pytest.param(lambda: open(DATA_PATH / "peptides.txt", "rb"), id="binary_file"),
    ],
)
def test_convert_peptide_txt(dataset):
    if callable(dataset):
        with dataset() as f:
            df = _convert_peptide_txt(f)
    else:
        df = _convert_peptide_txt(dataset)

    assert not df.empty
    assert [
        "Sample",
        "Protein ID",
        "Sequence",
        "Intensity",
        "PEP",
        "Charges",
    ] == df.columns.tolist()
