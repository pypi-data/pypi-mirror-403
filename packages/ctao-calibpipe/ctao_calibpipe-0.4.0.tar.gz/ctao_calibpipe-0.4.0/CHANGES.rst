calibpipe 0.3.0 (2025-11-27)
----------------------------


API Changes
~~~~~~~~~~~


Bug Fixes
~~~~~~~~~


New Features
~~~~~~~~~~~~


Maintenance
~~~~~~~~~~~

- Update CWL workflows

  - Unify ctapipe merge configuration and make it optional
  - Make merging step optional (only if multiple input files are provided)
  - Add output filenames for final products
  - Fix warnings related to conditional steps [`!206 <https://gitlab.cta-observatory.org/cta-computing/dpps/calibpipe/calibpipe/-/merge_requests/206>`__]


Refactoring and Optimization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

calibpipe 0.3.0-rc1 (2025-11-20)
--------------------------------


API Changes
~~~~~~~~~~~

- Update configuration for new chunking scheme from ctapipe above 0.28.0 [`!199 <https://gitlab.cta-observatory.org/cta-computing/dpps/calibpipe/calibpipe/-/merge_requests/199>`__]


Bug Fixes
~~~~~~~~~

- Use small zst muon file for testing [`!205 <https://gitlab.cta-observatory.org/cta-computing/dpps/calibpipe/calibpipe/-/merge_requests/205>`__]


New Features
~~~~~~~~~~~~

- Refactor muon throughput calculation tool and allow different statistical aggregation methods [`!186 <https://gitlab.cta-observatory.org/cta-computing/dpps/calibpipe/calibpipe/-/merge_requests/186>`__]

- Add CWL workflows for optical throughput calibration with muons [`!195 <https://gitlab.cta-observatory.org/cta-computing/dpps/calibpipe/calibpipe/-/merge_requests/195>`__]

- Add test for MST [`!204 <https://gitlab.cta-observatory.org/cta-computing/dpps/calibpipe/calibpipe/-/merge_requests/204>`__]


Maintenance
~~~~~~~~~~~

- Adopt ctapipe tooling to download test data [`!190 <https://gitlab.cta-observatory.org/cta-computing/dpps/calibpipe/calibpipe/-/merge_requests/190>`__]

- Polish and reorganize the documentation structure of CalibPipe to align with other DPPS pipelines. [`!201 <https://gitlab.cta-observatory.org/cta-computing/dpps/calibpipe/calibpipe/-/merge_requests/201>`__]


Refactoring and Optimization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
