WMS v0.4.0 (2025-09-26)
-----------------------

Major update including update to DIRAC 9.0 + DiracX.

We do not fore-see an upgrade path from an existing WMS v0.3.1 installation.


New Features
~~~~~~~~~~~~

- Update charts with DiracX + CTADIRAC 3.0.2 (DIRAC 9.0) [`!57 <https://gitlab.cta-observatory.org/cta-computing/dpps/workload/wms/-/merge_requests/57>`__]

- Update rucio to 38.2 to sync with BDMS. [`!68 <https://gitlab.cta-observatory.org/cta-computing/dpps/workload/wms/-/merge_requests/68>`__]


Bug Fixes
~~~~~~~~~

- Replace bitnami images with legacy versions, make configurable to allow future replacement with custom updated images. [`!66 <https://gitlab.cta-observatory.org/cta-computing/dpps/workload/wms/-/merge_requests/66>`__]


WMS v0.3.1 (2025-07-14)
-----------------------


Maintenance
~~~~~~~~~~~

- Update cvmfs chart to version 0.5.0. [`!61 <https://gitlab.cta-observatory.org/cta-computing/dpps/workload/wms/-/merge_requests/61>`__]


WMS v0.3.0 (2025-06-26)
-----------------------

API Changes
~~~~~~~~~~~

- Replace custom mysql deployment by including the bitnami mariadb helm chart.
- Improve structure in values to more clearly show which options apply to which
  pods. See the chart documentation for new values. [`!51 <https://gitlab.cta-observatory.org/cta-computing/dpps/workload/wms/-/merge_requests/51>`__]


New Features
~~~~~~~~~~~~

- Update CTADIRAC dependency to 2.2.81 to enable CWLJob running CWL workflows [`!58 <https://gitlab.cta-observatory.org/cta-computing/dpps/workload/wms/-/merge_requests/58>`__]


WMS v0.2.0 (2025-05-08)
-----------------------

* New CWL interface for job submission

WMS v0.1.0 (2025-02-21)
-----------------------

Initial release of the Workload Management System.

* Deployment of DIRAC 8 with CTADIRAC using helm.
* Python client package pinning correct version of CTADIRAC.
* Docker image for DIRAC server, clients and a test computing element
