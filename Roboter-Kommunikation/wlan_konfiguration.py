"""Zentrale Netzwerkwerte fuer die WLAN-Kommunikation mit dem Roboter.

Die WLAN-Verbindung selbst wird vom Betriebssystem hergestellt. Die IP-Adressen
sind Beispielwerte und muessen an das verwendete WLAN angepasst werden. Die
UDP-Ports muessen mit der Firmware des Roboters uebereinstimmen.
"""

PROTOKOLL = "UDP"

COMPUTER_IP = "192.168.1.10"
ROBOTER_IP = "192.168.1.20"

ROBOTER_BEFEHLS_PORT = 5005
COMPUTER_STATUS_PORT = 5006
