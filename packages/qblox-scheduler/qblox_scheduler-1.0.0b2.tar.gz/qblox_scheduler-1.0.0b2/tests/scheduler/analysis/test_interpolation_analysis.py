from collections.abc import Iterable

import pytest

from qblox_scheduler.analysis import interpolation_analysis as ia
from qblox_scheduler.analysis.data_handling import OutputDirectoryManager
from quantify_core.data.types import TUID

tuid_list = [TUID("20210419-170747-902-9c5a05")]
offset_list = [[0.0008868002631485698, 0.006586920009126688]]


@pytest.fixture(scope="session", autouse=True)
def analysis(tmp_analysis_test_data_dir: str) -> list:
    """
    Used to run the analysis a single time and run unit tests against the created
    analysis object.
    """
    OutputDirectoryManager.set_datadir(tmp_analysis_test_data_dir)
    analysis = [ia.InterpolationAnalysis2D(tuid=tuid).run() for tuid in tuid_list]

    return analysis


def test_figures_generated(analysis: Iterable) -> None:
    """
    Test that the right figures get created.
    """
    for a_obj in analysis:
        assert set(a_obj.figs_mpl.keys()) == {
            "Signalhound Power interpolating",
        }
