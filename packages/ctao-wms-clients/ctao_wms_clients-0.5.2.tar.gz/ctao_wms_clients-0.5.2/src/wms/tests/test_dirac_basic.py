"""Test job status."""

import logging
import subprocess
from pathlib import Path

import pytest
import yaml

from wms.tests.utils import wait_for_status

pytestmark = [
    pytest.mark.wms,
    pytest.mark.dirac_client,
]


# Simple test using the dirac-cwl proto CLI
@pytest.mark.usefixtures("_dirac_token")
def test_dirac_cwl_proto():
    project_path = Path("../dirac-cwl-proto")
    pixi_cmd = [
        "pixi",
        "run",
        "dirac-cwl job submit test/workflows/helloworld/description_basic.cwl --no-local",
    ]
    result = subprocess.run(pixi_cmd, cwd=project_path, capture_output=True, text=True)
    print(result.stdout)
    assert result.returncode == 0


# missing "Run a single-job workflow" UC ID
# @pytest.mark.verifies_usecase("DPPS-UC-110-????")
@pytest.mark.usefixtures("_init_dirac")
def test_simple_job(tmp_path):
    from DIRAC.Interfaces.API.Dirac import Dirac
    from DIRAC.Interfaces.API.Job import Job

    dirac = Dirac()

    job = Job()
    job.setExecutable("echo", arguments="Hello world")
    job.setName("testjob")
    job.setDestination("CTAO.CI.de")
    res = dirac.submitJob(job)
    assert res["OK"]
    job_id = res["Value"]

    # wait for job to succeed, will error in case of timeout or job failure
    result = wait_for_status(
        dirac,
        job_id=job_id,
        status="Done",
        error_on={"Failed"},
        timeout=300,
        job_output_dir=tmp_path,
    )
    print(result)


@pytest.mark.usefixtures("_init_dirac")
def test_cvmfs_available_on_ce(tmp_path):
    from DIRAC.Interfaces.API.Dirac import Dirac
    from DIRAC.Interfaces.API.Job import Job

    dirac = Dirac()

    job = Job()
    job.setExecutable("ls", "/cvmfs/ctao.dpps.test/")
    job.setExecutable("cat", "/cvmfs/ctao.dpps.test/new_repository")
    job.setName("cvmfs_job")
    job.setDestination("CTAO.CI.de")
    res = dirac.submitJob(job)
    assert res["OK"]
    job_id = res["Value"]

    # wait for job to succeed, will error in case of timeout or job failure
    result = wait_for_status(
        dirac,
        job_id=job_id,
        status="Done",
        error_on={"Failed"},
        timeout=300,
        job_output_dir=tmp_path,
    )
    print(result)


@pytest.mark.verifies_usecase("DPPS-UC-100-2")
@pytest.mark.usefixtures("_init_dirac")
def test_cwl_job(tmp_path):
    from CTADIRAC.Interfaces.API.CWLJob import CWLJob
    from DIRAC.Interfaces.API.Dirac import Dirac

    log = logging.getLogger(__name__)

    dirac = Dirac()

    base_path = Path("src/wms/tests/cwl/hello_world/")
    cwl_workflow = base_path / "container_example.cwl"
    hello_world_script = base_path / "hello_world.py"

    def cwl_file(path):
        return {"class": "File", "path": str(path)}

    cwl_inputs = {
        "local_script": cwl_file(hello_world_script),
    }
    cwl_inputs_path = base_path / "container_example_inputs.yaml"
    with cwl_inputs_path.open("w") as f:
        yaml.dump(cwl_inputs, f)

    cvmfs_path = Path("/cvmfs/ctao.dpps.test/")
    job = CWLJob(
        cwl_workflow=cwl_workflow,
        cwl_inputs=cwl_inputs_path,
        cvmfs_base_path=cvmfs_path,
    )
    job.setName("test_hello_world_container_clt")
    job.logfile_name = "test_hello_world_container_clt"
    job.setDestination("CTAO.CI.de")
    res = job.submit()
    assert res["OK"], f"Submitting job failed: {res!r}"
    job_id = res["Value"]

    # wait for job to succeed, will error in case of timeout or job failure
    result = wait_for_status(
        dirac,
        job_id=job_id,
        status="Done",
        error_on={"Failed"},
        timeout=300,
        job_output_dir=tmp_path,
    )
    log.info(result)


@pytest.mark.verifies_usecase("DPPS-UC-100-2")
@pytest.mark.usefixtures("_init_dirac")
def test_cwl_workflow_job(tmp_path):
    from CTADIRAC.Interfaces.API.CWLJob import CWLJob
    from DIRAC.Interfaces.API.Dirac import Dirac

    def cwl_file(path):
        return {"class": "File", "path": str(path)}

    log = logging.getLogger(__name__)

    dirac = Dirac()
    base_path = Path("src/wms/tests/cwl/basic_workflow/")
    cwl_workflow = base_path / "gaussian-fit-workflow.cwl"
    random_data_gen_script = base_path / "random_data_gen.py"
    gaussian_fit_script = base_path / "gaussian_fit.py"

    cwl_inputs = {
        "script_data_gen": [cwl_file(random_data_gen_script)],
        "output_file_name": "data_gen_test.txt",
        "script_gauss": [cwl_file(gaussian_fit_script)],
    }
    cwl_inputs_path = base_path / "inputs_gaussian_fit.yaml"
    with cwl_inputs_path.open("w") as f:
        yaml.dump(cwl_inputs, f)

    cvmfs_path = Path("/cvmfs/ctao.dpps.test/")
    job = CWLJob(
        cwl_workflow=cwl_workflow,
        cwl_inputs=cwl_inputs_path,
        cvmfs_base_path=cvmfs_path,
    )
    log.info("Input Sandbox: %s", job.input_sandbox)
    log.info("Input Data: %s", job.input_data)
    job.setName("test_gaussian_fit_workflow")
    job.logfile_name = "test_gaussian_fit_workflow"
    job.setDestination("CTAO.CI.de")
    res = job.submit()
    assert res["OK"], f"Submitting job failed: {res!r}"
    job_id = res["Value"]
    # wait for job to succeed, will error in case of timeout or job failure
    result = wait_for_status(
        dirac,
        job_id=job_id,
        status="Done",
        error_on={"Failed"},
        timeout=300,
        job_output_dir=tmp_path,
    )
    log.info(result)
