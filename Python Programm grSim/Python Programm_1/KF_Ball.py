import numpy as np
import matplotlib.pyplot as plt

class BallKalmanFilter:
    def __init__(self, dt, beta):
        self.dt = dt
        
        # 1. System-Matrizen aufbauen
        alpha = np.exp(-beta * dt) # Reibungsterm
        
        # Zustandsübergangsmatrix (A)
        self.A = np.array([
            [1, 0, dt, 0],
            [0, 1, 0, dt],
            [0, 0, alpha, 0],
            [0, 0, 0, alpha]
        ])
        
        # Messmatrix (H) - Wir messen nur Position
        self.H = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0]
        ])
        
        # 2. Rausch-Matrizen (Tuning)
        # Q: Unsicherheit im Modell (klein)
        self.Q = np.eye(4) * 0.001
        self.Q[2:, 2:] = 0.1 # Mehr Unsicherheit bei Speed
        
        # R: Unsicherheit der Messung (Kamera rauscht)
        self.R = np.eye(2) * 0.05 
        
        # Initialer Zustand (wird beim Start überschrieben)
        self.x = np.zeros(4)
        self.P = np.eye(4)

    def initialize(self, measurement):
        """Startet den Filter mit der ersten Messung"""
        self.x[0] = measurement[0]
        self.x[1] = measurement[1]
        self.x[2] = 0 # Annahme
        self.x[3] = 0 # Annahme
        
        # Unsicherheit initialisieren
        self.P = np.eye(4)
        self.P[0,0] = 0.1 # Position sicher
        self.P[1,1] = 0.1
        self.P[2,2] = 100.0 # Speed unsicher
        self.P[3,3] = 100.0

    def predict(self):
        """Schritt 1: Vorhersage"""
        # x = A * x
        self.x = self.A @ self.x
        
        # P = A * P * A_T + Q
        self.P = self.A @ self.P @ self.A.T + self.Q

    def update(self, measurement):
        """Schritt 2: Korrektur"""
        z = np.array(measurement)
        
        # Residuum (y = z - H * x)
        y = z - self.H @ self.x
        
        # Systemunsicherheit im Messraum (S = H * P * H_T + R)
        S = self.H @ self.P @ self.H.T + self.R
        
        # Kalman Gain (K = P * H_T * S^-1)
        K = self.P @ self.H.T @ np.linalg.inv(S)
        
        # Zustand korrigieren (x = x + K * y)
        self.x = self.x + K @ y
        
        # Kovarianz verringern (P = (I - K * H) * P)
        I = np.eye(4)
        self.P = (I - K @ self.H) @ self.P
        
        return self.x

# --- Simulation und Test ---

def run_test():
    # Parameter
    dt = 0.1
    beta = 0.5
    steps = 50
    
    kf = BallKalmanFilter(dt, beta)
    
    # Wahre Trajektorie generieren (Ground Truth)
    true_pos = []
    measurements = []
    estimates = []
    
    # Ball startet bei 0,0 mit Speed 5, 2
    sim_x = np.array([0, 0, 5, 2], dtype=float) 
    
    # Loop
    for i in range(steps):
        # 1. Physik simulieren (Wahrheit)
        # Wir nutzen die gleichen Formeln wie der Filter für die Physik
        alpha = np.exp(-beta * dt)
        sim_x[0] += sim_x[2] * dt
        sim_x[1] += sim_x[3] * dt
        sim_x[2] *= alpha
        sim_x[3] *= alpha
        true_pos.append(sim_x[:2].copy())
        
        # 2. Messung simulieren (Wahrheit + Rauschen)
        noise = np.random.normal(0, 0.15, 2) # Rauschen hinzufügen
        z = sim_x[:2] + noise
        measurements.append(z)
        
        # 3. Filter anwenden
        if i == 0:
            kf.initialize(z)
            est = kf.x
        else:
            kf.predict()
            est = kf.update(z)
        
        estimates.append(est.copy())

    # --- Plotten ---
    true_pos = np.array(true_pos)
    measurements = np.array(measurements)
    estimates = np.array(estimates)
    
    plt.figure(figsize=(10, 6))
    plt.plot(true_pos[:,0], true_pos[:,1], 'g-', label='Wahrheit (Ground Truth)', linewidth=2)
    plt.scatter(measurements[:,0], measurements[:,1], c='r', marker='x', label='Messung (Verrauscht)')
    plt.plot(estimates[:,0], estimates[:,1], 'b-', label='EKF Schätzung', linewidth=2)
    
    plt.title('Kalman Filter Ball Tracking')
    plt.xlabel('X Position (m)')
    plt.ylabel('Y Position (m)')
    plt.legend()
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    run_test()