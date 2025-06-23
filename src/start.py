import random
import sys
import memcache
import os
from pyModbusTCP.server import ModbusServer

from Configs import TAG, Connection, SimulationConfig
from HMI1 import HMI1
from HMI3 import HMI3
from FactorySimulation import FactorySimulation
from PLC1 import PLC1
from PLC2 import PLC2

from ics_sim.protocol import ProtocolFactory
from ics_sim.connectors import FileConnector, ConnectorFactory

def simulate_corrosive_risk(plc):
    # Simulate PH outside normal range
    plc._get = lambda tag: {
        TAG.TAG_TANK_LEVEL_VALUE: 5,
        TAG.TAG_TANK_LEVEL_MAX: 7,
        TAG.TAG_TANK_LEVEL_MIN: 3,
        TAG.TAG_TANK_PH_VALUE: 3.0,
        TAG.TAG_TANK_PH_MIN: 5.0,
        TAG.TAG_TANK_PH_MAX: 9.0,
        TAG.TAG_BOTTLE_LEVEL_VALUE: 1.0,
        TAG.TAG_BOTTLE_DISTANCE_TO_FILLER_VALUE: 0.5,
        TAG.TAG_BOTTLE_LEVEL_MAX: 2.0,
        TAG.TAG_TANK_INPUT_VALVE_MODE: 0,
        TAG.TAG_TANK_OUTPUT_VALVE_MODE: 0,
    }[tag]
    plc._check_manual_input = lambda a, b: False
    plc._set = lambda tag, val: print(f"[CORROSIVE RISK] {tag} set to {val}")
    plc.report = lambda msg, lvl=0: print(f"[CORROSIVE RISK] {msg}")
    plc._logic()

def simulate_bottle_position_risk(plc):
    plc._get = lambda tag: {
        TAG.TAG_TANK_LEVEL_VALUE: 5,
        TAG.TAG_TANK_LEVEL_MAX: 7,
        TAG.TAG_TANK_LEVEL_MIN: 3,
        TAG.TAG_PH_VALUE: 7.0,
        TAG.TAG_TANK_PH_MIN: 5.0,
        TAG.TAG_TANK_PH_MAX: 9.0,
        TAG.TAG_BOTTLE_LEVEL_VALUE: 3.0,
        TAG.TAG_BOTTLE_DISTANCE_TO_FILLER_VALUE: 2.0,
        TAG.TAG_BOTTLE_LEVEL_MAX: 2.0,
        TAG.TAG_TANK_INPUT_VALVE_MODE: 0,
        TAG.TAG_TANK_OUTPUT_VALVE_MODE: 0,
    }[tag]
    plc._check_manual_input = lambda a, b: False
    plc._set = lambda tag, val: print(f"[BOTTLE POSITION RISK] {tag} set to {val}")
    plc.report = lambda msg, lvl=0: print(f"[BOTTLE POSITION RISK] {msg}")
    plc._logic()

def simulate_hmi3_dual_interface():
    hmi3 = HMI3.__new__(HMI3)
    os.listdir = lambda path: ['wlan0', 'eth0']
    input_backup = __builtins__.input
    __builtins__.input = lambda prompt='': 'y' if 'start auto' in prompt else SimulationConfig.HMI3_ACCESS_CODE
    hmi3._set_clear_scr = lambda v: None
    hmi3.report = lambda msg, lvl=0: print(f"[HMI3 RISK] {msg}")
    try:
        hmi3._before_start()
    except RuntimeError as e:
        print(f"[HMI3 RISK] {e}")
    __builtins__.input = input_backup

def simulate_office_network_breach():
    try:
        ProtocolFactory.create_client('ModbusWriteRequest-TCP', '10.0.0.5', 502)
    except ValueError as e:
        print(f"[OFFICE NETWORK RISK] {e}")

def simulate_modbus_link_between_plc1_plc2():
    try:
        client = ProtocolFactory.create_client('ModbusWriteRequest-TCP', '192.168.0.2', 502)
        print("[MODBUS PLC1-PLC2 RISK] Simulated Modbus connection from PLC1 to PLC2")
    except Exception as e:
        print(f"[MODBUS PLC1-PLC2 RISK] {e}")

def start_simulation():
    factory = FactorySimulation()
    factory.start()

    plc1 = PLC1()
    plc1.start()

    plc2 = PLC2()
    plc2.start()

    hmi1 = HMI1()
    hmi1.start()

    # Simulate all 5 security risks
    print("[SIMULATING SECURITY RISKS]")
    simulate_corrosive_risk(plc1)
    simulate_bottle_position_risk(plc1)
    simulate_hmi3_dual_interface()
    simulate_office_network_breach()
    simulate_modbus_link_between_plc1_plc2()

if __name__ == "__main__":
    print("[STARTING SIMULATION WITH SECURITY RISK SCENARIOS]")
    start_simulation()
