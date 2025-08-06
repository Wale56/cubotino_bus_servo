"""
25.7.2025  Walter Gantenbein

Das Programm erlaubt das Trimmen eines Servos, welches bereits in einem Modell verbaut ist

- Anzeige der aktuellen Position
- Eingabe von Speed (0-1000)
- Eingabe von zwei Positionen (0-1000)
- 't' zum Umschalten zwischen den Positionen
- 'r' zum Neustarten mit neuen Werten
- 'q' zum Beenden

Die wichtigsten Aenderungen sind:
1. Neue Konstanten:
    - `POSITION_TOLERANCE = 3` - Erlaubte Abweichung von der Zielposition
    - `MAX_WAIT_TIME = 5.0` - Maximale Wartezeit in Sekunden

2. Neue Funktion `wait_for_position`:
    - Wartet bis die Zielposition erreicht ist
    - Beruecksichtigt die Toleranz
    - Bricht nach der maximalen Wartezeit ab
    - Gibt regelmaessige Positions-Updates

3. Verbesserte Position-Verfolgung:
    - Zeigt die Bewegung zur Zielposition an
    - Bestaetigt das Erreichen der Position
    - Meldet wenn die Position nicht erreicht wurde

Dies sollte eine genauere Kontrolle der Servobewegungen ermoeglichen. Sie koennen die `POSITION_TOLERANCE` und `MAX_WAIT_TIME` nach Bedarf anpassen.
"""

import os
import time
from scservo_sdk import *

# Settings
DEVICENAME = '/dev/serial0'
BAUDRATE = 1000000
SCS_ID = 1
POSITION_TOLERANCE = 20  # Toleranz fuer Positionsabweichung
MAX_WAIT_TIME = 5.0  # Maximale Wartezeit in Sekunden


def setup_servo():
    portHandler = PortHandler(DEVICENAME)
    packetHandler = PacketHandler(1)

    if portHandler.openPort() and portHandler.setBaudRate(BAUDRATE):
        packetHandler.write1ByteTxRx(portHandler, SCS_ID, 40, 1)
        return portHandler, packetHandler
    return None, None


def get_input(prompt, min_val, max_val):
    while True:
        try:
            value = int(input(prompt))
            if min_val <= value <= max_val:
                return value
            print(f"Value must be between {min_val} and {max_val}")
        except ValueError:
            print("Please enter a valid number")


def wait_for_position(packetHandler, portHandler, target_pos):
    start_time = time.time()
    while True:
        position, result, error = packetHandler.read2ByteTxRx(portHandler, SCS_ID, 56)
        if abs(position - target_pos) <= POSITION_TOLERANCE:
            return True

        if time.time() - start_time > MAX_WAIT_TIME:
            print(f"Timeout reached. Position: {position}")
            return False

        time.sleep(0.1)


def trim_servo():
    portHandler, packetHandler = setup_servo()
    if not portHandler:
        print("Connection failed")
        return

    try:
        toggle_state = True

        while True:
            print("\n--- Servo Trim Program ---")
            position, result, error = packetHandler.read2ByteTxRx(portHandler, SCS_ID, 56)
            print(f"Current Position: {position}")

            speed = get_input("Speed (0-2000): ", 0, 2000)
            pos1 = get_input("First Position (0-1000): ", 0, 1000)
            pos2 = get_input("Second Position (0-1000): ", 0, 1000)

            print("\nCommands: 't' = Toggle, 'r' = Restart, 'q' = Quit")

            while True:
                cmd = input("Command: ").lower()

                if cmd == 'q':
                    return
                elif cmd == 'r':
                    break
                elif cmd == 't':
                    target_pos = pos1 if toggle_state else pos2
                    toggle_state = not toggle_state

                    packetHandler.write2ByteTxRx(portHandler, SCS_ID, 46, speed)
                    packetHandler.write2ByteTxRx(portHandler, SCS_ID, 42, target_pos)

                    print(f"Moving to position: {target_pos}")
                    if wait_for_position(packetHandler, portHandler, target_pos):
                        position, result, error = packetHandler.read2ByteTxRx(portHandler, SCS_ID, 56)
                        print(f"Position reached: {position}")
                    else:
                        print("Position not reached within timeout")
                else:
                    print("Unknown command")

    finally:
        packetHandler.write1ByteTxRx(portHandler, SCS_ID, 40, 0)
        portHandler.closePort()
        print("Program ended")


if __name__ == "__main__":
    trim_servo()

