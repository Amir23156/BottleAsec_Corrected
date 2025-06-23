from ics_sim.Device import PLC, SensorConnector, ActuatorConnector
from Configs import TAG, Controllers, Connection
import logging


class PLC1(PLC):
    def __init__(self):
        sensor_connector = SensorConnector(Connection.CONNECTION)
        actuator_connector = ActuatorConnector(Connection.CONNECTION)
        super().__init__(1, sensor_connector, actuator_connector, TAG.TAG_LIST, Controllers.PLCs)

    def _logic(self):
        # --- Tank input valve control ---
        if not self._check_manual_input(TAG.TAG_TANK_INPUT_VALVE_MODE, TAG.TAG_TANK_INPUT_VALVE_STATUS):
            tank_level = self._get(TAG.TAG_TANK_LEVEL_VALUE)
            tank_max = self._get(TAG.TAG_TANK_LEVEL_MAX)
            tank_min = self._get(TAG.TAG_TANK_LEVEL_MIN)

            if tank_level > tank_max:
                self.report("Tank overflow risk – shutting input valve", logging.WARNING)
                self._set(TAG.TAG_TANK_INPUT_VALVE_STATUS, 0)
            elif tank_level < tank_min:
                self.report("Tank underflow risk – opening input valve", logging.WARNING)
                self._set(TAG.TAG_TANK_INPUT_VALVE_STATUS, 1)

        # --- Corrosive risk detection ---
        ph_value = self._get(TAG.TAG_TANK_PH_VALUE)
        ph_min = self._get(TAG.TAG_TANK_PH_MIN)
        ph_max = self._get(TAG.TAG_TANK_PH_MAX)

        if ph_value < ph_min or ph_value > ph_max:
            self.report("Corrosive risk detected – shutting all valves", logging.CRITICAL)
            self._set(TAG.TAG_TANK_INPUT_VALVE_STATUS, 0)
            self._set(TAG.TAG_TANK_OUTPUT_VALVE_STATUS, 0)

        # --- Tank output valve control ---
        if not self._check_manual_input(TAG.TAG_TANK_OUTPUT_VALVE_MODE, TAG.TAG_TANK_OUTPUT_VALVE_STATUS):
            bottle_level = self._get(TAG.TAG_BOTTLE_LEVEL_VALUE)
            belt_position = self._get(TAG.TAG_BOTTLE_DISTANCE_TO_FILLER_VALUE)
            bottle_max = self._get(TAG.TAG_BOTTLE_LEVEL_MAX)

            if bottle_level > bottle_max:
                self.report("Bottle overflow risk – shutting output valve", logging.WARNING)
                self._set(TAG.TAG_TANK_OUTPUT_VALVE_STATUS, 0)
            elif belt_position > 1.0:
                self.report("Bottle out of position – shutting output valve", logging.WARNING)
                self._set(TAG.TAG_TANK_OUTPUT_VALVE_STATUS, 0)
            else:
                self._set(TAG.TAG_TANK_OUTPUT_VALVE_STATUS, 1)

    def _post_logic_update(self):
        super()._post_logic_update()
        # Optional: uncomment to log loop timing
        # self.report(f"Uptime: {self.get_alive_time() / 1000:.2f}s | Loop latency: {self.get_loop_latency() / 1000:.2f}ms", logging.INFO)


if __name__ == '__main__':
    plc1 = PLC1()
    plc1.set_record_variables(True)
    plc1.start()
