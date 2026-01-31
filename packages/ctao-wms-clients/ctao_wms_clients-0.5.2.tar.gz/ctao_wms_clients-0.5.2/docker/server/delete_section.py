"""Minimal script needed to update dirac config."""

__RCSID__ = "$Id$"

import DIRAC
from DIRAC import gLogger
from DIRAC.ConfigurationSystem.Client.CSAPI import CSAPI
from DIRAC.Core.Base import Script

Script.parseCommandLine()

args = Script.getPositionalArgs()

if len(args) == 1:
    section = args[0]
else:
    gLogger.error("Needs 1 argument: configuration file")
    DIRAC.exit(-1)

cs_api = CSAPI()

res = cs_api.delSection(section)
if not res["OK"]:
    gLogger.error(f"Can't delete section {section} ", f"{res['Message']}")
    DIRAC.exit(-1)

res = cs_api.commit()
if not res["OK"]:
    gLogger.error("Can't commit new configuration data", f"{res['Message']}")
    DIRAC.exit(-1)
