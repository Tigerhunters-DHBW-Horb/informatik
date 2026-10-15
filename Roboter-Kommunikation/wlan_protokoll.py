"""Nachrichtenformat fuer die Kommunikation zwischen Computer und Robotern.

Uebertragung: eine UTF-8-kodierte JSON-Nachricht pro UDP-Datagramm.

Computer -> Roboter (type="command"):
    version, type, robot_id, sequence, timestamp, valid_for_ms,
    velocity.{x_mps, y_mps, omega_radps}, kick_speed_mps, dribbler

Roboter -> Computer (type="telemetry"):
    version, type, robot_id, sequence, timestamp, last_command_sequence,
    battery_voltage_v, velocity.{x_mps, y_mps, omega_radps}, faults

Die Befehle sind in Roboterkoordinaten angegeben. Der Roboter soll einen
Befehl nach valid_for_ms verwerfen und bei ausbleibenden gueltigen Befehlen
anhalten. Die Telemetrie bestaetigt den zuletzt verarbeiteten Befehl anhand
seiner Sequenznummer. IP-Adressen und UDP-Ports stehen in
wlan_konfiguration.py und muessen mit der Roboter-Firmware uebereinstimmen.
"""

import json
import math
from typing import Any, Dict, List, Optional


PROTOKOLL_VERSION = 1
MAX_ROBOTER = 12
BEFEHL_GUELTIGKEIT_MS = 100


def _pruefe_robot_id(robot_id: int) -> None:
    if isinstance(robot_id, bool) or not isinstance(robot_id, int):
        raise ValueError("robot_id muss eine ganze Zahl sein.")
    if not 0 <= robot_id < MAX_ROBOTER:
        raise ValueError("robot_id muss zwischen 0 und 11 liegen.")


def _pruefe_sequenznummer(sequence: int, feldname: str = "sequence") -> None:
    if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 0:
        raise ValueError(f"{feldname} muss eine nichtnegative ganze Zahl sein.")


def _pruefe_zahl(wert: float, feldname: str) -> None:
    if isinstance(wert, bool) or not isinstance(wert, (int, float)):
        raise ValueError(f"{feldname} muss eine Zahl sein.")
    if not math.isfinite(wert):
        raise ValueError(f"{feldname} muss endlich sein.")


def _kodieren(nachricht: Dict[str, Any]) -> bytes:
    return json.dumps(
        nachricht,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def kodiere_befehl(
    robot_id: int,
    sequence: int,
    x_mps: float,
    y_mps: float,
    omega_radps: float,
    kick_speed_mps: float = 0.0,
    dribbler: bool = False,
    timestamp: Optional[float] = None,
) -> bytes:
    """Erzeugt ein UDP-Nutzdatenpaket fuer einen Fahr- und Aktuatorbefehl."""
    _pruefe_robot_id(robot_id)
    _pruefe_sequenznummer(sequence)
    for name, value in (
        ("x_mps", x_mps),
        ("y_mps", y_mps),
        ("omega_radps", omega_radps),
        ("kick_speed_mps", kick_speed_mps),
    ):
        _pruefe_zahl(value, name)
    if not isinstance(dribbler, bool):
        raise ValueError("dribbler muss ein boolescher Wert sein.")

    nachricht: Dict[str, Any] = {
        "version": PROTOKOLL_VERSION,
        "type": "command",
        "robot_id": robot_id,
        "sequence": sequence,
        "valid_for_ms": BEFEHL_GUELTIGKEIT_MS,
        "velocity": {
            "x_mps": x_mps,
            "y_mps": y_mps,
            "omega_radps": omega_radps,
        },
        "kick_speed_mps": kick_speed_mps,
        "dribbler": dribbler,
    }
    if timestamp is not None:
        _pruefe_zahl(timestamp, "timestamp")
        nachricht["timestamp"] = timestamp

    return _kodieren(nachricht)


def kodiere_telemetrie(
    robot_id: int,
    sequence: int,
    last_command_sequence: int,
    battery_voltage_v: float,
    x_mps: float,
    y_mps: float,
    omega_radps: float,
    faults: Optional[List[str]] = None,
    timestamp: Optional[float] = None,
) -> bytes:
    """Erzeugt ein UDP-Nutzdatenpaket mit Status- und Messwerten des Roboters."""
    _pruefe_robot_id(robot_id)
    _pruefe_sequenznummer(sequence)
    _pruefe_sequenznummer(last_command_sequence, "last_command_sequence")
    for name, value in (
        ("battery_voltage_v", battery_voltage_v),
        ("x_mps", x_mps),
        ("y_mps", y_mps),
        ("omega_radps", omega_radps),
    ):
        _pruefe_zahl(value, name)
    if faults is None:
        faults = []
    if not isinstance(faults, list) or not all(
        isinstance(fault, str) for fault in faults
    ):
        raise ValueError("faults muss eine Liste aus Textmeldungen sein.")

    nachricht: Dict[str, Any] = {
        "version": PROTOKOLL_VERSION,
        "type": "telemetry",
        "robot_id": robot_id,
        "sequence": sequence,
        "last_command_sequence": last_command_sequence,
        "battery_voltage_v": battery_voltage_v,
        "velocity": {
            "x_mps": x_mps,
            "y_mps": y_mps,
            "omega_radps": omega_radps,
        },
        "faults": faults,
    }
    if timestamp is not None:
        _pruefe_zahl(timestamp, "timestamp")
        nachricht["timestamp"] = timestamp

    return _kodieren(nachricht)


def dekodiere_nachricht(data: bytes) -> Dict[str, Any]:
    """Dekodiert eine empfangene Nachricht und prueft Version und Grundstruktur."""
    try:
        nachricht = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Nachricht ist kein gueltiges UTF-8-JSON.") from exc

    if not isinstance(nachricht, dict):
        raise ValueError("Die Nachricht muss ein JSON-Objekt sein.")
    if nachricht.get("version") != PROTOKOLL_VERSION:
        raise ValueError("Nicht unterstuetzte Protokollversion.")
    if nachricht.get("type") not in ("command", "telemetry"):
        raise ValueError("Unbekannter Nachrichtentyp.")

    _pruefe_robot_id(nachricht.get("robot_id"))
    _pruefe_sequenznummer(nachricht.get("sequence"))
    velocity = nachricht.get("velocity")
    if not isinstance(velocity, dict):
        raise ValueError("velocity muss ein JSON-Objekt sein.")
    for feld in ("x_mps", "y_mps", "omega_radps"):
        _pruefe_zahl(velocity.get(feld), f"velocity.{feld}")

    if "timestamp" in nachricht:
        _pruefe_zahl(nachricht["timestamp"], "timestamp")

    if nachricht["type"] == "command":
        valid_for_ms = nachricht.get("valid_for_ms")
        if (
            isinstance(valid_for_ms, bool)
            or not isinstance(valid_for_ms, int)
            or valid_for_ms <= 0
        ):
            raise ValueError("valid_for_ms muss eine positive ganze Zahl sein.")
        _pruefe_zahl(nachricht.get("kick_speed_mps"), "kick_speed_mps")
        if not isinstance(nachricht.get("dribbler"), bool):
            raise ValueError("dribbler muss ein boolescher Wert sein.")
    else:
        _pruefe_sequenznummer(
            nachricht.get("last_command_sequence"), "last_command_sequence"
        )
        _pruefe_zahl(nachricht.get("battery_voltage_v"), "battery_voltage_v")
        faults = nachricht.get("faults")
        if not isinstance(faults, list) or not all(
            isinstance(fault, str) for fault in faults
        ):
            raise ValueError("faults muss eine Liste aus Textmeldungen sein.")

    return nachricht
