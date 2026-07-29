"""Standalone smoke test for GarnetApiClient, runnable outside Home Assistant.

It only exercises api.py + const.py, which depend on aiohttp alone (no
homeassistant import), so no Home Assistant install is needed.

Usage:
    pip install aiohttp
    python scripts/try_api.py <email> <password>

Optionally send a command (be careful — this operates the real alarm):
    python scripts/try_api.py <email> <password> arm-away <system_id> <partition>
    python scripts/try_api.py <email> <password> arm-home <system_id> <partition>
    python scripts/try_api.py <email> <password> disarm   <system_id> <partition>
"""

from __future__ import annotations

import asyncio
import importlib
import pathlib
import sys
import types

import aiohttp

# Load the `garnet_control.api` module WITHOUT running
# garnet_control/__init__.py (which imports homeassistant). We register a
# lightweight package that points at the source directory so api.py's
# `from .const import ...` relative import resolves.
GARNET_DIR = (
    pathlib.Path(__file__).resolve().parents[1]
    / "custom_components"
    / "garnet_control"
)
_pkg = types.ModuleType("garnet_control")
_pkg.__path__ = [str(GARNET_DIR)]
sys.modules["garnet_control"] = _pkg

api = importlib.import_module("garnet_control.api")


async def main(argv: list[str]) -> None:
    email, password = argv[1], argv[2]

    async with aiohttp.ClientSession() as session:
        client = api.GarnetApiClient(email, password, session)

        await client.async_login()
        print("Login OK")

        systems = await client.async_get_systems()
        print(f"{len(systems)} system(s) found:")
        for system in systems:
            print(f"- id={system.get('id')} nombre={system.get('nombre')!r}")
            for part, pdata in (system.get("estados") or {}).items():
                print(
                    f"    partition {part}: "
                    f"nombre={pdata.get('nombre')!r} estado={pdata.get('estado')!r}"
                )

        # Optional command: arm-away | arm-home | disarm
        if len(argv) >= 6:
            command, system_id, partition = argv[3], argv[4], argv[5]
            fn = {
                "arm-away": client.async_arm_away,
                "arm-home": client.async_arm_home,
                "disarm": client.async_disarm,
            }[command]
            print(f"Sending '{command}' to system={system_id} partition={partition}...")
            result = await fn(system_id, partition)
            print(f"Result: {result}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(
            "Usage: python scripts/try_api.py <email> <password> "
            "[arm-away|arm-home|disarm <system_id> <partition>]",
            file=sys.stderr,
        )
        sys.exit(2)
    asyncio.run(main(sys.argv))
