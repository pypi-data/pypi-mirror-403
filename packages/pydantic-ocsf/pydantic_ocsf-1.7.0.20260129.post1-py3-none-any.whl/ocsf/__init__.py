"""Pydantic models for the Open Cybersecurity Schema Framework (OCSF).

This package provides type-safe, validated models for OCSF security events.

Example:
    from ocsf import FileActivity, File, SeverityId

    event = FileActivity(
        time=1706000000000,
        activity_id=1,
        severity_id=SeverityId.INFORMATIONAL,
        file=File(name="test.txt"),
    )

The default imports are from OCSF 1.7.0 (latest). For other versions:
    from ocsf.v1_7_0 import FileActivity  # OCSF 1.7.0
    from ocsf.v1_6_0 import FileActivity  # OCSF 1.6.0
    from ocsf.v1_5_0 import FileActivity  # OCSF 1.5.0
    from ocsf.v1_2_0 import FileActivity  # OCSF 1.2.0
    from ocsf.v1_1_0 import FileActivity  # OCSF 1.1.0
    from ocsf.v1_0_0 import FileActivity  # OCSF 1.0.0
"""

from ocsf._base import OCSFBaseModel as OCSFBaseModel
from ocsf.v1_7_0 import *  # noqa: F401, F403

__version__ = "1.7.0.20260129"
