#!/usr/bin/env python3
"""Steuere einen ESP32-Roboter über eine einfache UDP-Oberfläche."""

from __future__ import annotations

import math
import tkinter as tk
from tkinter import messagebox, ttk

from udp_sender import UDP_PORT, RobotCommand, UdpSender


SEND_INTERVAL_MS = 20
CONTROL_KEYS = {
    "w": "x+",
    "s": "x-",
    "a": "y+",
    "d": "y-",
    "q": "omega-",
    "e": "omega+",
    "Up": "x+",
    "Down": "x-",
    "Left": "y+",
    "Right": "y-",
}


def command_from_controls(
    robot_id: int,
    controls: set[str],
    max_speed: float,
    max_omega: float,
) -> RobotCommand:
    """Create a velocity command from the currently held controls."""
    vx = float(int("x+" in controls) - int("x-" in controls))
    vy = float(int("y+" in controls) - int("y-" in controls))
    magnitude = math.hypot(vx, vy)
    if magnitude > 1.0:
        vx /= magnitude
        vy /= magnitude

    omega_direction = int("omega+" in controls) - int("omega-" in controls)
    return RobotCommand(
        robot_id,
        vx * max_speed,
        vy * max_speed,
        omega_direction * max_omega,
    )


class RobotControlUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Roboter-Fernsteuerung")
        self.root.resizable(False, False)

        self.sender: UdpSender | None = None
        self.robot_id = 0
        self.running = False
        self.pressed_controls: set[str] = set()

        self.broadcast_var = tk.StringVar(value="10.42.0.255")
        self.port_var = tk.StringVar(value=str(UDP_PORT))
        self.robot_id_var = tk.StringVar(value="0")
        self.speed_var = tk.DoubleVar(value=0.5)
        self.omega_var = tk.DoubleVar(value=2.0)
        self.status_var = tk.StringVar(value="Gestoppt")

        self._build_ui()
        self.root.bind("<KeyPress>", self._on_key_press)
        self.root.bind("<KeyRelease>", self._on_key_release)
        self.root.bind("<Escape>", self._on_escape)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.focus_set()

    def _build_ui(self) -> None:
        network = ttk.LabelFrame(self.root, text="Verbindung", padding=8)
        network.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="ew")

        ttk.Label(network, text="Broadcast-IP").grid(row=0, column=0, sticky="w")
        ttk.Entry(network, textvariable=self.broadcast_var, width=17).grid(
            row=0, column=1, padx=(5, 12)
        )
        ttk.Label(network, text="Port").grid(row=0, column=2, sticky="w")
        ttk.Entry(network, textvariable=self.port_var, width=7).grid(
            row=0, column=3, padx=(5, 12)
        )
        ttk.Label(network, text="Roboter-ID").grid(row=0, column=4, sticky="w")
        ttk.Entry(network, textvariable=self.robot_id_var, width=5).grid(
            row=0, column=5, padx=(5, 0)
        )

        settings = ttk.LabelFrame(self.root, text="Geschwindigkeitsgrenzen", padding=8)
        settings.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        ttk.Label(settings, text="Linear (m/s)").grid(row=0, column=0, sticky="w")
        tk.Scale(
            settings,
            variable=self.speed_var,
            from_=0.1,
            to=1.5,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            length=220,
        ).grid(row=0, column=1, padx=5)
        ttk.Label(settings, text="Drehung (rad/s)").grid(row=1, column=0, sticky="w")
        tk.Scale(
            settings,
            variable=self.omega_var,
            from_=0.5,
            to=6.0,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            length=220,
        ).grid(row=1, column=1, padx=5)

        controls = ttk.LabelFrame(self.root, text="Fahren", padding=8)
        controls.grid(row=2, column=0, padx=(10, 5), pady=5, sticky="nsew")
        ttk.Label(controls, text="X+/W").grid(row=0, column=1, pady=3)
        ttk.Label(controls, text="Y+/A").grid(row=1, column=0, padx=4)
        ttk.Label(controls, text="Y-/D").grid(row=1, column=2, padx=4)
        ttk.Label(controls, text="X-/S").grid(row=2, column=1, pady=3)
        self._bind_hold_button(controls, "X+", "x+", 0, 1)
        self._bind_hold_button(controls, "Y+", "y+", 1, 0)
        self._bind_hold_button(controls, "Y-", "y-", 1, 2)
        self._bind_hold_button(controls, "X-", "x-", 2, 1)

        rotation = ttk.LabelFrame(self.root, text="Drehung", padding=8)
        rotation.grid(row=2, column=1, padx=(5, 10), pady=5, sticky="nsew")
        self._bind_hold_button(rotation, "Q  -", "omega-", 0, 0)
        self._bind_hold_button(rotation, "E  +", "omega+", 0, 1)

        footer = ttk.Frame(self.root, padding=(10, 5, 10, 10))
        footer.grid(row=3, column=0, columnspan=2, sticky="ew")
        self.start_button = ttk.Button(footer, text="Steuerung starten", command=self.start)
        self.start_button.grid(row=0, column=0)
        ttk.Button(footer, text="Stopp", command=self.stop).grid(
            row=0, column=1, padx=6
        )
        ttk.Label(footer, textvariable=self.status_var).grid(
            row=0, column=2, padx=(8, 0), sticky="w"
        )

        ttk.Label(
            self.root,
            text="Tasten gedrückt halten: W/S = X, A/D = Y, Q/E = Drehung; Esc = Stopp",
            padding=(10, 0, 10, 8),
        ).grid(row=4, column=0, columnspan=2, sticky="w")

    def _bind_hold_button(
        self, parent: ttk.LabelFrame, label: str, control: str, row: int, column: int
    ) -> None:
        button = ttk.Button(parent, text=label, width=8)
        button.grid(row=row, column=column, padx=3, pady=3)
        button.bind(
            "<ButtonPress-1>",
            lambda _event, value=control: self._set_control(value, True),
        )
        button.bind(
            "<ButtonRelease-1>",
            lambda _event, value=control: self._set_control(value, False),
        )

    def start(self) -> None:
        if self.running:
            return
        try:
            broadcast_ip = self.broadcast_var.get().strip()
            if not broadcast_ip:
                raise ValueError("Bitte eine Broadcast-IP-Adresse eingeben.")
            port = int(self.port_var.get())
            if not 1 <= port <= 65535:
                raise ValueError("Der Port muss zwischen 1 und 65535 liegen.")
            self.robot_id = int(self.robot_id_var.get())
            if not 0 <= self.robot_id <= 255:
                raise ValueError("Die Roboter-ID muss zwischen 0 und 255 liegen.")
            self.sender = UdpSender(broadcast_ip, port)
        except (ValueError, OSError) as exc:
            messagebox.showerror("Ungültige Verbindung", str(exc), parent=self.root)
            return

        self.running = True
        self.pressed_controls.clear()
        self.start_button.configure(state=tk.DISABLED)
        self.status_var.set(f"Sende an {broadcast_ip}:{port}")
        self._send_tick()

    def stop(self) -> None:
        if not self.running:
            return
        self.running = False
        self.pressed_controls.clear()
        self.start_button.configure(state=tk.NORMAL)
        error = self._send_zero_and_close()
        self.status_var.set(error or "Gestoppt (Stoppbefehl gesendet)")

    def _send_zero_and_close(self) -> str | None:
        if self.sender is None:
            return None
        error = None
        try:
            self.sender.send([RobotCommand(self.robot_id, 0.0, 0.0, 0.0)])
        except OSError as exc:
            error = f"Fehler beim Senden des Stoppbefehls: {exc}"
        finally:
            self.sender.close()
            self.sender = None
        return error

    def _send_tick(self) -> None:
        if not self.running or self.sender is None:
            return
        command = command_from_controls(
            self.robot_id,
            self.pressed_controls,
            self.speed_var.get(),
            self.omega_var.get(),
        )
        try:
            self.sender.send([command])
        except OSError as exc:
            self.running = False
            self.pressed_controls.clear()
            self.start_button.configure(state=tk.NORMAL)
            self.sender.close()
            self.sender = None
            self.status_var.set(f"UDP-Fehler: {exc}")
            return
        self.root.after(SEND_INTERVAL_MS, self._send_tick)

    def _set_control(self, control: str, pressed: bool) -> None:
        if not self.running:
            return
        if pressed:
            self.pressed_controls.add(control)
        else:
            self.pressed_controls.discard(control)

    def _on_key_press(self, event: tk.Event) -> None:
        if event.keysym in CONTROL_KEYS:
            self._set_control(CONTROL_KEYS[event.keysym], True)

    def _on_key_release(self, event: tk.Event) -> None:
        if event.keysym in CONTROL_KEYS:
            self._set_control(CONTROL_KEYS[event.keysym], False)

    def _on_escape(self, _event: tk.Event) -> str:
        self.stop()
        return "break"

    def _on_close(self) -> None:
        if self.running:
            self.stop()
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    RobotControlUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
