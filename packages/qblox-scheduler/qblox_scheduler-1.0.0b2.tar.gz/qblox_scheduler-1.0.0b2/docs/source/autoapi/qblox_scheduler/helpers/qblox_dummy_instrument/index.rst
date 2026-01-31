qblox_dummy_instrument
======================

.. py:module:: qblox_scheduler.helpers.qblox_dummy_instrument 

.. autoapi-nested-parse::

   Helpers for Qblox dummy device.



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   qblox_scheduler.helpers.qblox_dummy_instrument.start_dummy_cluster_armed_sequencers



.. py:function:: start_dummy_cluster_armed_sequencers(cluster_component: qblox_scheduler.instrument_coordinator.components.qblox.ClusterComponent) -> None

   Starting all armed sequencers in a dummy cluster.

   Starting all armed sequencers via Cluster.start_sequencer() doesn't yet
   work with dummy acquisition data (verified it does work on hardware).
   Hence, we need still need to call start_sequencer() for all sequencers separately.
   TODO: qblox_instruments.ieee488_2.cluster_dummy_transport.ClusterDummyTransport
   See SE-441.


