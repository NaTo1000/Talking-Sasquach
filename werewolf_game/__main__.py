from __future__ import annotations

import argparse
import json
from pathlib import Path
from time import time
from typing import Any

from .engine import GameEngine
from .models import AttackAlert, NearbyDevice


def _load_scenario(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict) or not isinstance(value.get("devices"), list):
        raise ValueError("Scenario must be an object containing a devices array")
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the safe Werewolf proximity-game simulator")
    parser.add_argument("scenario", type=Path, help="JSON scenario containing nearby game devices")
    parser.add_argument("--report", type=Path, help="Write full state and metrics as JSON")
    args = parser.parse_args()

    scenario = _load_scenario(args.scenario)
    devices = tuple(NearbyDevice.from_dict(item) for item in scenario["devices"])
    current_time = scenario.get("current_time")
    engine = GameEngine(
        clock=(lambda: float(current_time)) if current_time is not None else time
    )
    if scenario.get("attack_alert") is not None:
        if not engine.report_attack(AttackAlert.from_dict(scenario["attack_alert"])):
            raise ValueError("Scenario attack alert was rejected")
    result = engine.scan(devices)
    engine.charge_shield(int(scenario.get("shield_charge", 0)))

    attacker_id = scenario.get("attacker_device_id")
    if attacker_id is not None:
        opponent = next((d for d in devices if d.device_id == attacker_id), None)
        if opponent is None:
            raise ValueError("attacker_device_id must reference a detected device")
        engine.defend(opponent)

    report = engine.state.to_dict()
    output = json.dumps(report, indent=2)
    print(output)
    if args.report:
        args.report.write_text(output + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
