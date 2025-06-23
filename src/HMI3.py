import logging
import os
import sys
import time
import random

from ics_sim.Device import HMI
#from Configs import TAG, Controllers
from Configs import TAG, Controllers, SimulationConfig


class HMI3(HMI):
    def __init__(self):
        super().__init__('HMI3', TAG.TAG_LIST, Controllers.PLCs)


def _before_start(self):
    HMI._before_start(self)

    # --- Detect network interface fallback ---
    interfaces = os.listdir('/sys/class/net')
    if 'eth0' not in interfaces and 'wlan0' in interfaces:
        self.report("RJ45 (eth0) not available – switching to WiFi (wlan0)", logging.WARNING)
        self._send(TAG.TAG_HMI3_NETWORK_FALLBACK, 1)
    elif 'eth0' in interfaces:
        self.report("Connected via RJ45 (eth0)", logging.INFO)
        self._send(TAG.TAG_HMI3_NETWORK_FALLBACK, 1)
    elif 'wlan0' in interfaces:
        self.report("Only WiFi (wlan0) available", logging.WARNING)
        self._send(TAG.TAG_HMI3_NETWORK_FALLBACK, 1)
    else:
        self.report("No known network interfaces found", logging.ERROR)
        self._send(TAG.TAG_HMI3_NETWORK_FALLBACK, 0)

    # --- Authenticated access setup ---
    attempts = 0
    while True:
        response = input("Do you want to start auto manipulation of factory setting? \n").lower()
        if response not in ('y', 'yes'):
            continue
        code = os.getenv('HMI3_CODE') or input('Enter HMI3 access code: ')
        if code != SimulationConfig.HMI3_ACCESS_CODE:
            self.report('Invalid HMI3 access code', logging.ERROR)
            attempts += 1
            if attempts >= 3:
                raise RuntimeError('Maximum authentication attempts reached')
            continue
        self._set_clear_scr(False)
        self.random_values = [["TANK LEVEL MIN" , 1 , 4.5],
                              ["TANK LEVEL MAX" , 5.5 , 9],
                              ["BOTTLE LEVEL MAX" , 1 , 1.9]]
        break


    def _display(self):
        n = random.randint(5, 20)
        print("Sleep for {} seconds \n".format(n))
        time.sleep(n)


    def _operate(self):
        try:
            choice = self.__get_choice()
            input1, input2 = choice
            if input1 == 1:
                self._send(TAG.TAG_TANK_LEVEL_MIN, input2)

            elif input1 == 2:
                self._send(TAG.TAG_TANK_LEVEL_MAX, input2)

            elif input1 == 3:
                self._send(TAG.TAG_BOTTLE_LEVEL_MAX, input2)

        except ValueError as e:
            self.report(e.__str__())
        except Exception as e:
            self.report('The input is invalid' + e.__str__())

        print('set {} to the {} automatically'.format(self.random_values[input1-1][0], input2))

    def __get_choice(self):
        input1 = random.randint(1, len(self.random_values))
        print(self.random_values)
        print(input1)
        input2 = random.uniform(self.random_values[input1-1][1] , self.random_values[input1-1][2])
        print (input2)
        return input1, input2



if __name__ == '__main__':
    hmi3= HMI3()
    hmi3.start()
