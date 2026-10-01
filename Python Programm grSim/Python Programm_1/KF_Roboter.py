import numpy as np
import matplotlib.pyplot as plt

class RobotExtendedKalmanFilter:
    def __init__(self, dt):
        self.dt = dt
        
        # Zustand x: [x, y, psi (Blick), theta (Kurs), v (Speed)]
        self.x = np.zeros(5)
        self.P = np.eye(5) * 1.0
        
        # Prozessrauschen Q (Wie sehr vertrauen wir der Physik?)
        self.Q = np.diag([0.01, 0.01, 0.01, 0.1, 0.1])
        
        # Messrauschen R (Kamera misst x, y und Blickrichtung psi)
        self.R = np.diag([0.05, 0.05, 0.02])
        
        # Messmatrix H (linear, da wir x, y, psi direkt messen)
        self.H = np.array([
            [1, 0, 0, 0, 0],
            [0, 1, 0, 0, 0],
            [0, 0, 1, 0, 0]
        ])

    def initialize(self, measurement):
        """ Startet mit [x, y, psi] von der Kamera """
        self.x[0] = measurement[0]
        self.x[1] = measurement[1]
        self.x[2] = measurement[2]
        self.x[3] = 0 # Kurs unbekannt
        self.x[4] = 0 # Speed unbekannt
        self.P = np.eye(5) * 10.0

    def predict(self):
        """ Schritt 1: Vorhersage mit nichtlinearer Physik """
        x, y, psi, theta, v = self.x
        dt = self.dt

        # 1. Zustandsfortschreibung f(x)
        # Position ändert sich durch v und theta (Omni-Bewegung)
        self.x[0] = x + v * np.cos(theta) * dt
        self.x[1] = y + v * np.sin(theta) * dt
        # psi, theta, v bleiben laut Modell erst mal gleich (Trägheit)
        self.x[2] = psi
        self.x[3] = theta
        self.x[4] = v

        # 2. Jacobimatrix J_f (Ableitung der Vorhersage nach dem Zustand)
        # Das ist das "E" in EKF
        J_f = np.array([
            [1, 0, 0, -v * np.sin(theta) * dt, np.cos(theta) * dt],
            [0, 1, 0,  v * np.cos(theta) * dt, np.sin(theta) * dt],
            [0, 0, 1,  0,                      0],
            [0, 0, 0,  1,                      0],
            [0, 0, 0,  0,                      1]
        ])

        # 3. Kovarianz-Vorhersage
        self.P = J_f @ self.P @ J_f.T + self.Q

    def update(self, measurement):
        """ Schritt 2: Korrektur mit Kamera [x, y, psi] """
        z = np.array(measurement)
        
        # Residuum (Innovation)
        y = z - self.H @ self.x
        
        # Kalman Gain
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)
        
        # Zustand korrigieren
        self.x = self.x + K @ y
        self.P = (np.eye(5) - K @ self.H) @ self.P
        
        return self.x

# --- Test-Simulation ---
def run_robot_test():
    dt = 0.05
    steps = 60
    ekf = RobotExtendedKalmanFilter(dt)
    
    # Simulierter Roboter: fährt schräg (45°), schaut aber nach vorne (0°)
    true_x = 0
    true_y = 0
    true_psi = 0.0      # Blickrichtung
    true_theta = 0.785  # 45 Grad Bewegungsrichtung
    true_v = 2.0        # 2 m/s
    
    path_true = []
    path_measure = []
    path_est = []

    for i in range(steps):
        # 1. Wahre Position (Physik)
        true_x += true_v * np.cos(true_theta) * dt
        true_y += true_v * np.sin(true_theta) * dt
        path_true.append([true_x, true_y])
        
        # 2. Messung (mit Rauschen)
        z = [true_x + np.random.normal(0, 0.1), 
             true_y + np.random.normal(0, 0.1), 
             true_psi + np.random.normal(0, 0.05)]
        path_measure.append(z[:2])
        
        # 3. EKF
        if i == 0:
            ekf.initialize(z)
        else:
            ekf.predict()
            ekf.update(z)
        path_est.append(ekf.x[:2].copy())

    # Plot
    path_true = np.array(path_true)
    path_measure = np.array(path_measure)
    path_est = np.array(path_est)

    plt.figure(figsize=(8,8))
    plt.plot(path_true[:,0], path_true[:,1], 'g-', label="Wahre Bahn")
    plt.scatter(path_measure[:,0], path_measure[:,1], c='r', alpha=0.3, label="Messung (Kamera)")
    plt.plot(path_est[:,0], path_est[:,1], 'b--', label="EKF Schätzung")
    plt.legend()
    plt.title("Omni-Robot EKF Tracking")
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    run_robot_test()


    
#-----------------------#
#KF mit Fikter py#

import numpy as np
from filterpy.kalman import ExtendedKalmanFilter




class OmniRobotFilterPy:
    def __init__(self, dt):
        self.dt = dt
        
        # 1. EKF Objekt erstellen
        # dim_x = 5: [x, y, psi, theta, v]
        # dim_z = 3: [x, y, psi] (was die Kamera sieht)
        self.ekf = ExtendedKalmanFilter(dim_x=5, dim_z=3)
        
        # 2. Anfangszustand und Unsicherheit
        self.ekf.x = np.array([0., 0., 0., 0., 0.]) 
        self.ekf.P *= 10.0
        
        # 3. Messrauschen R (Kamera)
        self.ekf.R = np.diag([0.05, 0.05, 0.02])
        
        # 4. Prozessrauschen Q (Physik-Modell)
        self.ekf.Q = np.diag([0.01, 0.01, 0.01, 0.1, 0.1])

    def H_jacobian(self, x):
        """ Messmatrix H (wie die 5 Zustände auf die 3 Messwerte abgebildet werden) """
        return np.array([
            [1, 0, 0, 0, 0],
            [0, 1, 0, 0, 0],
            [0, 0, 1, 0, 0]
        ])

    def Hx(self, x):
        """ Messfunktion: Rechnet den Zustand zurück in den Messraum """
        # Da wir x, y, psi direkt messen, ist das einfach:
        return np.array([x[0], x[1], x[2]])

    def predict(self):
        """ Vorhersageschritt """
        x = self.ekf.x
        dt = self.dt
        
        # Physik-Update (f(x))
        # x_neu = x + v * cos(theta) * dt
        # y_neu = y + v * sin(theta) * dt
        v = x[4]
        theta = x[3]
        
        self.ekf.x[0] += v * np.cos(theta) * dt
        self.ekf.x[1] += v * np.sin(theta) * dt
        # psi, theta, v bleiben gleich im Modell

        # Jacobimatrix F berechnen
        F = np.array([
            [1, 0, 0, -v * np.sin(theta) * dt, np.cos(theta) * dt],
            [0, 1, 0,  v * np.cos(theta) * dt, np.sin(theta) * dt],
            [0, 0, 1,  0,                      0],
            [0, 0, 0,  1,                      0],
            [0, 0, 0,  0,                      1]
        ])
        
        # Die EKF-Klasse von filterpy braucht F für das Update der Kovarianz P
        self.ekf.predict_update(f=None, F=F, Q=self.ekf.Q)

    def update(self, measurement):
        """ Korrekturschritt mit Kameradaten """
        z = np.array(measurement)
        self.ekf.update(z, self.H_jacobian, self.Hx)
        return self.ekf.x

#--- Benutzung im Loop ---
#kf = OmniRobotFilterPy(dt=0.016)
#kf.predict()
#kf.update([kamera_x, kamera_y, kamera_psi])

