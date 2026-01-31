=========
Workflows
=========

.. contents::

Array Calibration
=================

Telescope Cross Calibration
---------------------------

.. cwl_workflow:: ../../workflows/array/uc-120-2.3-telescope-cross-calibration.cwl

Atmospheric Calibration
=======================

.. cwl_workflow:: ../../workflows/atmosphere/uc-120-1.2-calculate-macobac.cwl

.. cwl_workflow:: ../../workflows/atmosphere/uc-120-1.3-select-reference-atmospheric-model.cwl

.. cwl_workflow:: ../../workflows/atmosphere/uc-120-1.7-create-contemporary-atmospheric-model.cwl

Telescope Calibration
=====================

Optical Throughput Calibration with Muons
-----------------------------------------

.. cwl_workflow_graph:: ../../workflows/telescope/throughput/uc-120-2.2-optical-throughput-calibration-with-muons.cwl
.. cwl_workflow:: ../../workflows/telescope/throughput/uc-120-2.2-optical-throughput-calibration-with-muons.cwl
.. cwl_workflow:: ../../workflows/telescope/throughput/calibpipe-throughput-muon-tool.cwl

Camera Calibration
------------------

.. cwl_workflow_graph:: ../../workflows/telescope/camera/uc-120-2.20-perform-camera-calibration.cwl
.. cwl_workflow:: ../../workflows/telescope/camera/uc-120-2.20-perform-camera-calibration.cwl
.. cwl_workflow:: ../../workflows/telescope/camera/calibpipe-camcalib-tool.cwl
.. cwl_workflow:: ../../workflows/telescope/ctapipe-pix-stats-tool.cwl
