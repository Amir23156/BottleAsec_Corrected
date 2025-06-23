import os
import types
import builtins
import io
import sys
import logging
import pytest

# Ensure source modules are importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Provide a dummy memcache module if missing
if 'memcache' not in sys.modules:
    class DummyClient:
        def __init__(self, *args, **kwargs):
            self.store = {}
        def set(self, k, v):
            self.store[k] = v
        def get(self, k):
            return self.store.get(k)
        def disconnect_all(self):
            pass
    sys.modules['memcache'] = types.SimpleNamespace(Client=DummyClient)

# Provide dummy pyModbusTCP modules if missing
if 'pyModbusTCP.client' not in sys.modules:
    sys.modules['pyModbusTCP.client'] = types.SimpleNamespace(ModbusClient=lambda *a, **kw: None)
if 'pyModbusTCP.server' not in sys.modules:
    dummy_server = types.SimpleNamespace(start=lambda: None, stop=lambda: None,
                                        data_bank=types.SimpleNamespace(
                                            set_holding_registers=lambda *a, **kw: None,
                                            get_holding_registers=lambda *a, **kw: [0]))
    sys.modules['pyModbusTCP.server'] = types.SimpleNamespace(ModbusServer=lambda *a, **kw: dummy_server,
                                                             DataBank=types.SimpleNamespace())
if 'pyModbusTCP' not in sys.modules:
    sys.modules['pyModbusTCP'] = types.SimpleNamespace(client=sys.modules['pyModbusTCP.client'],
                                                       server=sys.modules['pyModbusTCP.server'])

from Configs import TAG, SimulationConfig
from ics_sim import connectors
from ics_sim.protocol import ProtocolFactory
from ics_sim.Device import HMI
from HMI3 import HMI3
from PLC1 import PLC1


def test_office_network_restriction_invalid_host():
    with pytest.raises(ValueError):
        connectors._validate_office_host('10.0.0.1')


def test_plc_network_restriction_invalid_host():
    with pytest.raises(ValueError):
        ProtocolFactory.create_client('ModbusWriteRequest-TCP', '10.0.0.5', 502)


def test_hmi_wifi_bridge_detection(monkeypatch):
    hmi = HMI.__new__(HMI)
    monkeypatch.setattr(os, 'listdir', lambda path: ['wlan0', 'eth0'])

    def fake_open(path, *args, **kwargs):
        return io.StringIO('up')
    monkeypatch.setattr(builtins, 'open', fake_open)

    with pytest.raises(RuntimeError):
        HMI._HMI__enforce_single_network(hmi)


def test_hmi3_access_code(monkeypatch):
    hmi = HMI3.__new__(HMI3)
    hmi._set_clear_scr = lambda value: None
    hmi.report = lambda *a, **kw: None

    inputs = iter(['y', 'wrong', 'y', SimulationConfig.HMI3_ACCESS_CODE])
    monkeypatch.setattr(builtins, 'input', lambda *args: next(inputs))
    with monkeypatch.context() as m:
        m.setattr(HMI, '_before_start', lambda self: None)
        hmi._before_start()


def test_plc1_corrosive_monitoring():
    plc = PLC1.__new__(PLC1)
    data = {
        TAG.TAG_TANK_LEVEL_VALUE: 5,
        TAG.TAG_TANK_LEVEL_MAX: 7,
        TAG.TAG_TANK_LEVEL_MIN: 3,
        TAG.TAG_TANK_PH_VALUE: 4.0,
        TAG.TAG_TANK_PH_MIN: 5.0,
        TAG.TAG_TANK_PH_MAX: 9.0,
        TAG.TAG_BOTTLE_LEVEL_VALUE: 3,
        TAG.TAG_BOTTLE_DISTANCE_TO_FILLER_VALUE: 2,
        TAG.TAG_BOTTLE_LEVEL_MAX: 2,
        TAG.TAG_TANK_INPUT_VALVE_STATUS: 1,
        TAG.TAG_TANK_OUTPUT_VALVE_STATUS: 1,
    }

    plc._get = lambda tag: data[tag]
    plc._set = lambda tag, value: data.__setitem__(tag, value)
    plc._check_manual_input = lambda c, a: False
    plc.report = lambda *a, **kw: None

    plc._logic()

    assert data[TAG.TAG_TANK_INPUT_VALVE_STATUS] == 0
    assert data[TAG.TAG_TANK_OUTPUT_VALVE_STATUS] == 0
