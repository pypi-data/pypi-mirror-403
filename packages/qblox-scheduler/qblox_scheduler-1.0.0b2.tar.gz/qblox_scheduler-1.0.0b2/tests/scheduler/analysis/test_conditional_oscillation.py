import warnings
from pathlib import Path

import numpy as np
import pytest

from qblox_scheduler.analysis.conditional_oscillation_analysis import (
    ConditionalOscillationAnalysis,
)
from qblox_scheduler.analysis.data_handling import AnalysisDataContainer


@pytest.fixture(
    scope="session",
    autouse=True,
    params=[
        # tuid                    leakage estimator             2-qubit phase
        ("20230509-165523-132-dcfea7", 0.0008966770852672354, 177.3772464754731),
        ("20230509-165651-504-cabfd0", 0.0007817506219041951, 193.97152963647227),
        ("20230509-165733-096-5016ba", 0.0008335984071690091, 164.6742324870603),
        ("20230509-165820-224-324d99", 0.0008556314763556684, 169.43540496128574),
        ("20230509-165850-578-8a48c2", 0.0008849521635840999, 172.60453682725986),
    ],
)
def analysis_and_ref(tmp_analysis_test_data_dir, request):
    tuid, leakage, phi = request.param
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        analysis = ConditionalOscillationAnalysis(
            tuid=tuid, dataset=AnalysisDataContainer.load_dataset(tuid)
        ).run()

    return analysis, (leakage, phi)


def test_load_fit_results(analysis_and_ref, tmp_analysis_test_data_dir):
    analysis, _ = analysis_and_ref
    for fit_name, fit_result in analysis.fit_results.items():
        loaded_fit_result = ConditionalOscillationAnalysis.load_fit_result(
            tuid=analysis.tuid, fit_name=fit_name
        )
        assert loaded_fit_result.params == fit_result.params


def test_processed_dataset(analysis_and_ref, tmp_analysis_test_data_dir):
    analysis, _ = analysis_and_ref

    # Based on the tuid check if there is a respective folder(s)
    container = Path(AnalysisDataContainer.locate_experiment_container(analysis.tuid))
    file_path = container / "analysis_ConditionalOscillationAnalysis" / "dataset_processed.hdf5"
    dataset_processed = AnalysisDataContainer.load_dataset_from_path(file_path)

    # only magnitude is saved in the dataset
    assert dataset_processed.mag_lf_off.units == "V"
    assert dataset_processed.mag_hf_off.units == "V"
    assert dataset_processed.mag_lf_on.units == "V"
    assert dataset_processed.mag_hf_on.units == "V"

    assert dataset_processed.phi.units == "deg"


def test_quantities_of_interest(analysis_and_ref):
    analysis, (leakage, phi) = analysis_and_ref

    fitted_leakage = analysis.quantities_of_interest["leak"]
    fitted_phi = analysis.quantities_of_interest["phi_2q_deg"]

    # Tests that the fitted values are approximately correct.
    # Tests that the fitted values are approximately correct.
    assert abs(leakage - fitted_leakage) < 5 * fitted_leakage.std_dev
    assert abs(phi - fitted_phi) < 5 * fitted_phi.std_dev


def test_print_error_without_crash(analysis_and_ref, capsys):
    analysis, _ = analysis_and_ref

    # re-run analysis with nan values
    bad_ds = analysis.dataset
    bad_ds.y0.data[10:] = np.asarray([float("nan")] * (bad_ds.y0.data.size - 10))

    _ = ConditionalOscillationAnalysis(dataset=bad_ds).run()

    # Capture the printed output
    captured = capsys.readouterr()

    assert "Error during fit:" in captured.out
