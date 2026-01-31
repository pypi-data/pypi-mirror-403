"""pytest setup and fixtures for wms integration tests"""

import subprocess as sp
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def _dirac_token():
    """Get token to talk to DiracX"""
    from DIRAC.FrameworkSystem.Utilities.diracx import get_token
    from diracx.core.models import TokenResponse
    from diracx.core.utils import write_credentials

    username = "dpps_user"
    group = "dpps_group"
    dirac_properties = {"NormalUser", "PrivateLimitedDelegation"}
    data = get_token(
        username,
        group,
        dirac_properties,
        expires_minutes=1440,
        source="ProxyManager",
    )

    write_credentials(
        TokenResponse(**data),
        location=Path("/home/dirac/.cache/diracx/credentials.json"),
    )


@pytest.fixture(scope="session")
def _dirac_proxy():
    sp.run(["dirac-proxy-init", "-g", "dpps_group"], check=True)


@pytest.fixture(scope="session")
def _init_dirac(_dirac_proxy):
    """Import and init DIRAC, needs to be run first for anything using DIRAC"""
    import DIRAC

    DIRAC.initialize()
