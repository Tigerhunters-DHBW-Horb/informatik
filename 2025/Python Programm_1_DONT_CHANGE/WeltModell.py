import numpy as np
from geometrie import Pose, Vektor2D
from KF_Ball import BallKalmanFilter
from KF_Roboter import RobotExtendedKalmanFilter


class Roboter:
    def __init__(self, roboter_id, dt=0.016):
        self.roboter_id = roboter_id
        self.pose = Pose(0, 0, 0)
        self.filter = RobotExtendedKalmanFilter(dt)
        self.ist_aktiv = False

    def update_vision(self, x, y, orientierung):
        if not self.ist_aktiv:
            self.filter.initialize([x, y, orientierung])
            self.ist_aktiv = True

        self.filter.predict()
        zustand = self.filter.update([x, y, orientierung])

        # Wichtig: Pose hat position.x und position.y
        self.pose.position.x = float(zustand[0])
        self.pose.position.y = float(zustand[1])
        self.pose.orientierung = float(zustand[2])


class Ball:
    def __init__(self, dt=0.016):
        self.pose = Pose(0, 0, 0)
        self.filter = BallKalmanFilter(dt, beta=0.5)
        self.ist_aktiv = False

    def update_vision(self, x, y):
        if not self.ist_aktiv:
            self.filter.initialize([x, y])
            self.ist_aktiv = True

        self.filter.predict()
        zustand = self.filter.update([x, y])

        # Wichtig: Pose hat position.x und position.y
        self.pose.position.x = float(zustand[0])
        self.pose.position.y = float(zustand[1])


class WeltModell:
    def __init__(self):
        self.roboter_heim = {i: Roboter(i) for i in range(16)}
        self.roboter_gast = {i: Roboter(i) for i in range(16)}
        self.ball = Ball()
        print("WeltModell mit Kalman-Filtern bereit!")

    def verarbeite_vision_daten(self, vision_daten):
        """
        Diese Funktion brauchst du aktuell nicht, weil du in main.py
        direkt det.balls und det.robots_yellow/blue ausliest.
        """
        pass