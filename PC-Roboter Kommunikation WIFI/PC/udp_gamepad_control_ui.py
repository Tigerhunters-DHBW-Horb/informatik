#!/usr/bin/env python3
"""Bluetooth-Xbox-Controller mit Live-Anzeige und UDP-Robotersteuerung."""

from __future__ import annotations

import math
import os
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any

from udp_sender import UDP_PORT, RobotCommand, UdpSender


POLL_INTERVAL_MS = 20
SEND_INTERVAL_MS = 20
MAX_LINEAR_SPEED_MPS = 5
STICK_DEADZONE = 0.08


def shape_stick(x: float, y: float) -> tuple[float, float]:
    magnitude = math.hypot(x, y)
    if magnitude <= STICK_DEADZONE:
        return 0.0, 0.0
    scaled = min(1.0, (min(magnitude, 1.0) - STICK_DEADZONE) / (1.0 - STICK_DEADZONE))
    return x / magnitude * scaled, y / magnitude * scaled


def command_from_gamepad(
    robot_id: int,
    axes: tuple[float, float, float, float, float],
    max_speed: float,
    max_omega: float,
    sprint_multiplier: float,
    sneak_multiplier: float,
) -> RobotCommand:
    left_x, left_y, right_x, left_trigger, right_trigger = axes
    move_x, move_y = shape_stick(left_x, left_y)
    if abs(right_x) <= STICK_DEADZONE:
        rotation = 0.0
    else:
        rotation = math.copysign(
            (abs(right_x) - STICK_DEADZONE) / (1.0 - STICK_DEADZONE), right_x
        )

    if left_trigger >= 0.5:
        speed = max_speed * sneak_multiplier
    elif right_trigger >= 0.5:
        speed = max_speed * sprint_multiplier
    else:
        speed = max_speed
    speed = min(speed, MAX_LINEAR_SPEED_MPS)

    return RobotCommand(
        robot_id,
        -move_y * speed,
        -move_x * speed,
        rotation * max_omega,
    )


class XboxController:
    """Uses SDL's standard Xbox controller mapping via pygame."""

    def __init__(self) -> None:
        os.environ["SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS"] = "1"
        import pygame
        from pygame._sdl2 import controller

        self.pygame: Any = pygame
        self.controller_api: Any = controller
        self.device: Any = None
        pygame.init()
        try:
            pygame.display.set_mode((1, 1), pygame.HIDDEN)
            controller.init()
            self.search()
        except pygame.error as exc:
            pygame.quit()
            raise RuntimeError(f"pygame konnte nicht gestartet werden: {exc}") from exc

    def search(self) -> None:
        if self.device is not None:
            self.device.quit()
            self.device = None
        try:
            self.pygame.event.pump()
            self.pygame.event.clear()
        except self.pygame.error:
            return
        for index in range(self.controller_api.get_count()):
            if self.controller_api.is_controller(index):
                try:
                    self.device = self.controller_api.Controller(index)
                except self.pygame.error:
                    self.device = None
                return

    @property
    def name(self) -> str | None:
        if self.device is None or not self.device.attached():
            return None
        return self.device.as_joystick().get_name()

    def read(self) -> dict[str, Any] | None:
        try:
            self.pygame.event.pump()
            self.pygame.event.clear()
        except self.pygame.error:
            return None

        if self.device is not None and not self.device.attached():
            self.device.quit()
            self.device = None
        if self.device is None:
            self.search()
        if self.device is None:
            return None

        p = self.pygame
        try:
            axes = tuple(
                max(-1.0, min(1.0, value))
                for value in (
                    self.device.get_axis(p.CONTROLLER_AXIS_LEFTX) / 32767.0,
                    self.device.get_axis(p.CONTROLLER_AXIS_LEFTY) / 32767.0,
                    self.device.get_axis(p.CONTROLLER_AXIS_RIGHTX) / 32767.0,
                    self.device.get_axis(p.CONTROLLER_AXIS_TRIGGERLEFT) / 32768.0,
                    self.device.get_axis(p.CONTROLLER_AXIS_TRIGGERRIGHT) / 32768.0,
                )
            )
            buttons = {
                "A": self.device.get_button(p.CONTROLLER_BUTTON_A),
                "B": self.device.get_button(p.CONTROLLER_BUTTON_B),
                "X": self.device.get_button(p.CONTROLLER_BUTTON_X),
                "Y": self.device.get_button(p.CONTROLLER_BUTTON_Y),
                "LB": self.device.get_button(p.CONTROLLER_BUTTON_LEFTSHOULDER),
                "RB": self.device.get_button(p.CONTROLLER_BUTTON_RIGHTSHOULDER),
                "View": self.device.get_button(p.CONTROLLER_BUTTON_BACK),
                "Menu": self.device.get_button(p.CONTROLLER_BUTTON_START),
                "L3": self.device.get_button(p.CONTROLLER_BUTTON_LEFTSTICK),
                "R3": self.device.get_button(p.CONTROLLER_BUTTON_RIGHTSTICK),
                "DPadUp": self.device.get_button(p.CONTROLLER_BUTTON_DPAD_UP),
                "DPadDown": self.device.get_button(p.CONTROLLER_BUTTON_DPAD_DOWN),
                "DPadLeft": self.device.get_button(p.CONTROLLER_BUTTON_DPAD_LEFT),
                "DPadRight": self.device.get_button(p.CONTROLLER_BUTTON_DPAD_RIGHT),
            }
            right_y = max(
                -1.0,
                min(
                    1.0,
                    self.device.get_axis(p.CONTROLLER_AXIS_RIGHTY) / 32767.0,
                ),
            )
        except self.pygame.error:
            self.device.quit()
            self.device = None
            return None

        return {"axes": axes, "buttons": buttons, "right_y": right_y}

    def close(self) -> None:
        if self.device is not None:
            self.device.quit()
            self.device = None
        self.controller_api.quit()
        self.pygame.quit()


class GamepadControlUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Robotersteuerung – Bluetooth-Controller")
        self.root.minsize(720, 600)

        self.controller: XboxController | None = None
        self.sender: UdpSender | None = None
        self.connected = False
        self.running = False
        self.robot_id = 0
        self.last_state: dict[str, Any] | None = None

        self.broadcast_var = tk.StringVar(value="10.42.0.255")
        self.port_var = tk.StringVar(value=str(UDP_PORT))
        self.robot_id_var = tk.StringVar(value="0")
        self.speed_var = tk.DoubleVar(value=0.3)
        self.omega_var = tk.DoubleVar(value=2.0)
        self.sprint_var = tk.DoubleVar(value=1.5)
        self.sneak_var = tk.DoubleVar(value=0.25)
        self.status_var = tk.StringVar(value="Controller wird initialisiert …")
        self.udp_status_var = tk.StringVar(value="UDP-Steuerung ist gestoppt.")
        self.mode_var = tk.StringVar(value="NORMAL")

        self._build_ui()
        self._init_controller()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.bind("<Escape>", self._escape)
        self.root.after(POLL_INTERVAL_MS, self._poll)

    def _build_ui(self) -> None:
        connection = ttk.LabelFrame(self.root, text="UDP-Verbindung", padding=8)
        connection.pack(fill="x", padx=12, pady=(12, 6))
        ttk.Label(connection, text="Broadcast-IP").grid(row=0, column=0, sticky="w")
        ttk.Entry(connection, textvariable=self.broadcast_var, width=17).grid(
            row=0, column=1, padx=(5, 12)
        )
        ttk.Label(connection, text="Port").grid(row=0, column=2, sticky="w")
        ttk.Entry(connection, textvariable=self.port_var, width=7).grid(
            row=0, column=3, padx=(5, 12)
        )
        ttk.Label(connection, text="Roboter-ID").grid(row=0, column=4, sticky="w")
        ttk.Entry(connection, textvariable=self.robot_id_var, width=5).grid(
            row=0, column=5, padx=(5, 12)
        )
        self.start_button = ttk.Button(
            connection, text="Steuerung starten", command=self.start
        )
        self.start_button.grid(row=0, column=6, padx=4)
        ttk.Button(connection, text="Stopp", command=self.stop).grid(
            row=0, column=7, padx=4
        )

        settings = ttk.LabelFrame(self.root, text="Geschwindigkeiten", padding=8)
        settings.pack(fill="x", padx=12, pady=6)
        self._scale(settings, "Normal (m/s)", self.speed_var, 0.1, 0.5, 0, 0)
        self._scale(settings, "Drehung (rad/s)", self.omega_var, 0.5, 2.0, 0, 2)
        self._scale(settings, "Sprint-Faktor", self.sprint_var, 1.1, 2.0, 1, 0)
        self._scale(settings, "Schleich-Faktor", self.sneak_var, 0.1, 0.5, 1, 2)

        visual = ttk.LabelFrame(
            self.root, text="Controller – Live-Anzeige", padding=8
        )
        visual.pack(fill="both", expand=True, padx=12, pady=6)
        ttk.Label(visual, textvariable=self.status_var).pack(anchor="w")
        ttk.Label(visual, textvariable=self.udp_status_var).pack(anchor="w")
        self.canvas = tk.Canvas(
            visual, height=300, background="#f2f4f7", highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True, pady=(6, 8))
        self.canvas.bind("<Configure>", lambda _event: self._draw_controller())
        self.mode_label = ttk.Label(
            visual, textvariable=self.mode_var, font=("", 15, "bold")
        )
        self.mode_label.pack(anchor="center", pady=(0, 4))

        ttk.Label(
            self.root,
            text=(
                "Linker Stick: fahren · Rechter Stick: drehen · LT: schleichen · "
                "RT: sprinten · Esc: Stopp"
            ),
            padding=(12, 2, 12, 10),
        ).pack(anchor="w")

    @staticmethod
    def _scale(
        parent: ttk.LabelFrame,
        label: str,
        variable: tk.DoubleVar,
        minimum: float,
        maximum: float,
        row: int,
        column: int,
    ) -> None:
        ttk.Label(parent, text=label).grid(
            row=row, column=column, padx=(8, 2), sticky="w"
        )
        tk.Scale(
            parent,
            variable=variable,
            from_=minimum,
            to=maximum,
            resolution=0.05 if maximum <= 0.5 else 0.1,
            orient=tk.HORIZONTAL,
            length=190,
        ).grid(row=row, column=column + 1, padx=(2, 8))

    def _init_controller(self) -> None:
        try:
            self.controller = XboxController()
        except (ImportError, RuntimeError) as exc:
            self.status_var.set(
                f"Controller nicht verfügbar: {exc}. Installiere requirements.txt."
            )
            return

    def _poll(self) -> None:
        if self.controller is not None:
            state = self.controller.read()
            name = self.controller.name
            self.connected = state is not None and name is not None
            self.last_state = state
            if self.connected:
                self.status_var.set(f"Verbunden: {name}")
            else:
                self.status_var.set(
                    "Kein Xbox-Controller erkannt – per Bluetooth koppeln; Suche läuft."
                )
        else:
            self.connected = False
            self.last_state = None

        self._draw_controller()
        if self.running and self.sender is not None:
            self._send_command()
        self.root.after(POLL_INTERVAL_MS, self._poll)

    def _draw_controller(self) -> None:
        canvas = self.canvas
        canvas.delete("all")
        width = max(canvas.winfo_width(), 500)
        height = max(canvas.winfo_height(), 250)
        cx, cy = width / 2, height / 2 + 5
        body_w, body_h = min(width * 0.72, 620), min(height * 0.56, 170)
        left, right = cx - body_w / 2, cx + body_w / 2
        top, bottom = cy - body_h / 2, cy + body_h / 2
        fill = "#344054" if self.connected else "#98a2b3"

        canvas.create_oval(left, top, right, bottom, fill=fill, outline=fill)
        canvas.create_rectangle(left + 30, top, right - 30, bottom, fill=fill, outline=fill)
        canvas.create_text(cx, top - 26, text="Xbox Controller", fill="#344054", font=("", 12, "bold"))

        axes = self.last_state["axes"] if self.last_state else (0.0,) * 5
        buttons = self.last_state["buttons"] if self.last_state else {}
        self._draw_stick(cx - body_w * 0.24, cy + 14, axes[0], axes[1], "LINKER STICK")
        right_y = self.last_state.get("right_y", 0.0) if self.last_state else 0.0
        self._draw_stick(
            cx + body_w * 0.23, cy + 14, axes[2], right_y, "RECHTER STICK"
        )

        dpad_x, dpad_y = cx - body_w * 0.39, cy - 5
        self._draw_button(
            dpad_x, dpad_y - 22, "↑", buttons.get("DPadUp", False)
        )
        self._draw_button(
            dpad_x, dpad_y + 22, "↓", buttons.get("DPadDown", False)
        )
        self._draw_button(
            dpad_x - 22, dpad_y, "←", buttons.get("DPadLeft", False)
        )
        self._draw_button(
            dpad_x + 22, dpad_y, "→", buttons.get("DPadRight", False)
        )

        face_x, face_y = cx + body_w * 0.39, cy - 6
        self._draw_button(face_x, face_y - 28, "Y", buttons.get("Y", False), "#fdb022")
        self._draw_button(face_x + 28, face_y, "B", buttons.get("B", False), "#f04438")
        self._draw_button(face_x, face_y + 28, "A", buttons.get("A", False), "#12b76a")
        self._draw_button(face_x - 28, face_y, "X", buttons.get("X", False), "#2e90fa")

        self._draw_trigger(left + body_w * 0.18, top - 5, axes[3], "LT", "#2e90fa")
        self._draw_trigger(right - body_w * 0.18, top - 5, axes[4], "RT", "#f79009")
        self._draw_button(
            cx - body_w * 0.3, top + 20, "LB", buttons.get("LB", False), "#7f56d9", 10
        )
        self._draw_button(
            cx + body_w * 0.3, top + 20, "RB", buttons.get("RB", False), "#7f56d9", 10
        )
        center_y = top + 20
        for offset, label in ((-24, "View"), (24, "Menu")):
            self._draw_button(cx + offset, center_y, label, buttons.get(label, False), "#7f56d9", 8)

        self.mode_var.set(self._drive_mode(axes[3], axes[4]))
        self.mode_label.configure(
            foreground="#b54708" if axes[3] >= 0.5 else "#175cd3" if axes[4] >= 0.5 else "#344054"
        )

    def _draw_stick(
        self, x: float, y: float, axis_x: float, axis_y: float, label: str
    ) -> None:
        radius = 30
        self.canvas.create_oval(
            x - radius, y - radius, x + radius, y + radius, outline="#d0d5dd", width=3
        )
        self.canvas.create_line(x - radius, y, x + radius, y, fill="#667085")
        self.canvas.create_line(x, y - radius, x, y + radius, fill="#667085")
        self.canvas.create_oval(
            x + axis_x * radius - 7,
            y + axis_y * radius - 7,
            x + axis_x * radius + 7,
            y + axis_y * radius + 7,
            fill="#84caff",
            outline="#1570ef",
            width=2,
        )
        self.canvas.create_text(
            x,
            y + radius + 16,
            text=f"{label}  {axis_x:+.2f}, {axis_y:+.2f}",
            fill="#344054",
        )

    def _draw_button(
        self,
        x: float,
        y: float,
        label: str,
        active: bool,
        color: str = "#d0d5dd",
        radius: int = 12,
    ) -> None:
        self.canvas.create_oval(
            x - radius,
            y - radius,
            x + radius,
            y + radius,
            fill=color if active else "#f2f4f7",
            outline="#ffffff" if active else "#98a2b3",
            width=2,
        )
        self.canvas.create_text(x, y, text=label, fill="white" if active else "#344054", font=("", 8, "bold"))

    def _draw_trigger(
        self, x: float, y: float, value: float, label: str, color: str
    ) -> None:
        width, height = 72, 12
        self.canvas.create_rectangle(
            x - width / 2, y - height / 2, x + width / 2, y + height / 2,
            fill="#eaecf0", outline="#d0d5dd",
        )
        self.canvas.create_rectangle(
            x - width / 2, y - height / 2,
            x - width / 2 + width * max(0.0, value), y + height / 2,
            fill=color, outline=color,
        )
        self.canvas.create_text(
            x, y - 14, text=f"{label} {value:.0%}", fill="#344054"
        )

    @staticmethod
    def _drive_mode(left_trigger: float, right_trigger: float) -> str:
        if left_trigger >= 0.5:
            return "SCHLEICHMODUS"
        if right_trigger >= 0.5:
            return "SPRINTMODUS"
        return "NORMALMODUS"

    def start(self) -> None:
        if self.running:
            return
        try:
            address = self.broadcast_var.get().strip()
            if not address:
                raise ValueError("Bitte eine Broadcast-IP eingeben.")
            port = int(self.port_var.get())
            if not 1 <= port <= 65535:
                raise ValueError("Der Port muss zwischen 1 und 65535 liegen.")
            self.robot_id = int(self.robot_id_var.get())
            if not 0 <= self.robot_id <= 255:
                raise ValueError("Die Roboter-ID muss zwischen 0 und 255 liegen.")
            self.sender = UdpSender(address, port)
        except (ValueError, OSError) as exc:
            messagebox.showerror("Ungültige Verbindung", str(exc), parent=self.root)
            return

        self.running = True
        self.start_button.configure(state=tk.DISABLED)
        self.udp_status_var.set(
            f"Sende an {address}:{port} – warte auf Controllerbewegung."
        )
        self._send_command()

    def _send_command(self) -> None:
        if self.sender is None:
            return
        axes = self.last_state["axes"] if self.connected and self.last_state else (0.0,) * 5
        try:
            command = command_from_gamepad(
                self.robot_id,
                axes,
                self.speed_var.get(),
                self.omega_var.get(),
                self.sprint_var.get(),
                self.sneak_var.get(),
            )
            self.sender.send([command])
            self.udp_status_var.set(
                f"UDP {self.sender.address[0]}:{self.sender.address[1]} | "
                f"ID {command.robot_id} | "
                f"vx {command.vx:+.2f} m/s, vy {command.vy:+.2f} m/s, "
                f"ω {command.omega:+.2f} rad/s"
            )
        except OSError as exc:
            self.stop()
            self.udp_status_var.set(f"UDP-Fehler: {exc}")

    def stop(self) -> None:
        self.running = False
        self.start_button.configure(state=tk.NORMAL)
        self.udp_status_var.set("UDP-Steuerung gestoppt.")
        if self.sender is not None:
            try:
                self.sender.send([RobotCommand(self.robot_id, 0.0, 0.0, 0.0)])
            except OSError as exc:
                self.udp_status_var.set(f"Fehler beim Senden des Stoppbefehls: {exc}")
            finally:
                self.sender.close()
                self.sender = None
        else:
            self.status_var.set("Gestoppt")

    def _escape(self, _event: tk.Event) -> str:
        self.stop()
        return "break"

    def close(self) -> None:
        self.stop()
        if self.controller is not None:
            self.controller.close()
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    GamepadControlUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
