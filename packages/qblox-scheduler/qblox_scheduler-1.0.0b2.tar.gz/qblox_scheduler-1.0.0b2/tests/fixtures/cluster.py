import pytest
from qblox_instruments import (
    Cluster,
    ClusterType,
    SequencerStates,
    SequencerStatus,
    SequencerStatuses,
    SequencerStatusFlags,
)

from qblox_scheduler.helpers.qblox_dummy_instrument import start_dummy_cluster_armed_sequencers
from qblox_scheduler.instrument_coordinator.components import qblox


def patch_qtm_parameters(mocker, module):
    """
    Patch QTM QCoDeS parameters.
    """
    for seq_no in range(8):
        sequencer = module[f"sequencer{seq_no}"]
        io_channel = module[f"io_channel{seq_no}"]
        mocker.patch.object(sequencer.sync_en, "set", wraps=sequencer.sync_en.set)
        # sequence is not wrapped because the QTM instructions are not yet in the qblox-instruments
        # assembler binaries.
        mocker.patch.object(sequencer.sequence, "set")
        mocker.patch.object(io_channel.mode, "set", wraps=io_channel.mode.set)
        mocker.patch.object(
            io_channel.forward_trigger_en, "set", wraps=io_channel.forward_trigger_en.set
        )
        mocker.patch.object(
            io_channel.analog_threshold, "set", wraps=io_channel.analog_threshold.set
        )
        mocker.patch.object(
            io_channel.binned_acq_time_ref, "set", wraps=io_channel.binned_acq_time_ref.set
        )
        mocker.patch.object(
            io_channel.binned_acq_time_source, "set", wraps=io_channel.binned_acq_time_source.set
        )
        mocker.patch.object(
            io_channel.binned_acq_on_invalid_time_delta,
            "set",
            wraps=io_channel.binned_acq_on_invalid_time_delta.set,
        )
        mocker.patch.object(
            io_channel.scope_trigger_mode, "set", wraps=io_channel.scope_trigger_mode.set
        )
        mocker.patch.object(io_channel.scope_mode, "set", wraps=io_channel.scope_mode.set)


@pytest.fixture
def make_cluster_component(mocker):
    cluster_component: qblox.ClusterComponent | None = None

    default_modules = {
        "1": "QCM",
        "2": "QCM_RF",
        "3": "QRM",
        "4": "QRM_RF",
        "5": "QTM",
        "7": "QCM",
        "10": "QCM",  # for flux pulsing q0_q3
        "12": "QCM",  # for flux pulsing q4
        "14": "QRC",
    }

    def _make_cluster_component(
        name: str = "cluster0",
        modules: dict = default_modules,
        sequencer_status: SequencerStatuses = SequencerStatuses.OKAY,
        sequencer_state: SequencerStates = SequencerStates.ARMED,
        info_flags: list[SequencerStatusFlags] | None = None,
        warn_flags: list[SequencerStatusFlags] | None = None,
        err_flags: list[SequencerStatusFlags] | None = None,
        sequencer_logs: list[str] | None = None,
    ) -> qblox.ClusterComponent:
        qblox_types = {
            "QCM": ClusterType.CLUSTER_QCM,
            "QCM_RF": ClusterType.CLUSTER_QCM_RF,
            "QRM": ClusterType.CLUSTER_QRM,
            "QRM_RF": ClusterType.CLUSTER_QRM_RF,
            "QTM": ClusterType.CLUSTER_QTM,
            "QRC": ClusterType.CLUSTER_QRC,
        }
        cluster = Cluster(
            name=name,
            dummy_cfg={
                slot_idx: qblox_types[module_type] for slot_idx, module_type in modules.items()
            },
        )

        nonlocal cluster_component
        cluster_component = qblox.ClusterComponent(cluster)

        mocker.patch.object(cluster, "reference_source", wraps=cluster.reference_source)

        mocker.patch.object(
            cluster,
            "start_sequencer",
            wraps=lambda: start_dummy_cluster_armed_sequencers(cluster_component),  # type: ignore
        )

        mocker.patch.object(cluster, "stop_sequencer", wraps=cluster.stop_sequencer)

        for comp in cluster_component._cluster_modules.values():
            instrument = comp.instrument
            mocker.patch.object(instrument, "arm_sequencer", wraps=instrument.arm_sequencer)
            mocker.patch.object(instrument, "start_sequencer", wraps=instrument.start_sequencer)
            mocker.patch.object(instrument, "stop_sequencer", wraps=instrument.stop_sequencer)
            if not instrument.is_rf_type and not instrument.is_qtm_type:
                mocker.patch.object(instrument, "out0_offset", wraps=instrument.out0_offset)
            mocker.patch.object(instrument, "set", wraps=instrument.set)
            mocker.patch.object(
                instrument,
                "get_sequencer_status",
                return_value=SequencerStatus(
                    sequencer_status,
                    sequencer_state,
                    info_flags if info_flags else [],
                    warn_flags if warn_flags else [],
                    err_flags if err_flags else [],
                    sequencer_logs if sequencer_logs else [],
                ),
            )
            if instrument.is_qrm_type or instrument.is_qrc_type:
                mocker.patch.object(
                    instrument,
                    "store_scope_acquisition",
                    wraps=instrument.store_scope_acquisition,
                )
            elif instrument.is_qtm_type:
                patch_qtm_parameters(mocker, instrument)

        return cluster_component

    yield _make_cluster_component


@pytest.fixture
def dummy_cluster():
    cluster: Cluster | None = None

    def _dummy_cluster(
        name: str = "cluster0",
        dummy_cfg: dict | None = None,
    ) -> Cluster:
        nonlocal cluster
        cluster = Cluster(
            name=name,
            dummy_cfg=(
                dummy_cfg
                if dummy_cfg is not None
                else {2: ClusterType.CLUSTER_QCM, 4: ClusterType.CLUSTER_QRM}
            ),
        )
        return cluster

    yield _dummy_cluster
