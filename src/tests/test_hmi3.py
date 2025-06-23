def test_hmi3_network_fallback(monkeypatch):
    from HMI3 import HMI3
    from Configs import TAG

    # Simulate eth0 being down and wlan0 being available
    monkeypatch.setattr(os, 'listdir', lambda path: ['wlan0'])
    fallback_result = {}

    hmi3 = HMI3.__new__(HMI3)
    hmi3._send = lambda tag, value: fallback_result.setdefault(tag, value)
    hmi3.report = lambda msg, level=logging.INFO: print(f"[TEST LOG] {msg}")

    monkeypatch.setattr(HMI3, '_HMI3__get_choice', lambda self: (1, 2.0))  # Skip random inputs
    monkeypatch.setattr(HMI3, '_set_clear_scr', lambda self, val: None)
    monkeypatch.setattr(HMI3, '_operate', lambda self: None)  # Skip runtime ops
    monkeypatch.setattr('builtins.input', lambda _: SimulationConfig.HMI3_ACCESS_CODE)

    hmi3._before_start()

    assert fallback_result[TAG.TAG_HMI3_NETWORK_FALLBACK] == 1
