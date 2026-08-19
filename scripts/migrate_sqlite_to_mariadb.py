from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.migration_seed import MigrationSeedError, migrate_existing_sqlite_data


if __name__ == "__main__":
    try:
        result = migrate_existing_sqlite_data(
            sqlite_path=Path(__file__).resolve().parent.parent / "data" / "inventory.db",
            strict=False,
        )
        result["unmatched_bom_items"] = [item.__dict__ for item in result["unmatched_bom_items"]]
        print(json.dumps(result, indent=2))
    except MigrationSeedError as error:
        print(json.dumps({"error": str(error), "unmatched_bom_items": [item.__dict__ for item in error.unmatched_bom_items]}, indent=2))
        raise SystemExit(1)
