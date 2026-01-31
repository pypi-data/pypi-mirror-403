# pydantic-ocsf

Pydantic models for the Open Cybersecurity Schema Framework (OCSF).

## Installation

```bash
pip install pydantic-ocsf
```

## Version Scheme

This package uses a version format of `{ocsf_version}.{generation_date}`:
- **OCSF Version**: The latest OCSF schema version included (e.g., `1.7.0`)
- **Generation Date**: When the models were generated (format: `YYYYMMDD`)

**Example**: `1.7.0.20260129` means OCSF schema v1.7.0 generated on January 29, 2026

This versioning scheme ensures you can track both the OCSF schema version and when the Pydantic models were last regenerated.

## Quick Start

```python
from ocsf import File, StatusId
import time

# Create a file object (using latest v1.7.0 by default)
file = File(
    name="document.pdf",
    type_id=1,
    size=1024000,
)

# Serialize to JSON
json_str = file.model_dump_json(indent=2)
print(json_str)

# Parse from JSON
parsed = File.model_validate_json(json_str)
```

## Supported OCSF Versions

- `ocsf.v1_7_0` - OCSF 1.7.0 (also available as `from ocsf import ...`)
- `ocsf.v1_6_0` - OCSF 1.6.0
- `ocsf.v1_5_0` - OCSF 1.5.0
- `ocsf.v1_2_0` - OCSF 1.2.0
- `ocsf.v1_1_0` - OCSF 1.1.0
- `ocsf.v1_0_0` - OCSF 1.0.0

## License

Apache 2.0
