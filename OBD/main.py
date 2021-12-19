# Assumes ODBLink MX on Bluetooth COM port, attached to 2019 Audi e-tron. Should also work with other ELM327 adapters.

import collections
import json
import numpy as np
import serial
import time
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation
import logging
import sys
import requests

liveplot = False
voltage = 0
current = 0
soc = 0
batt_temp_min = 0
batt_temp_max = 0
batt_temp = 0
ignition_on = False
charging = False
fast_charging = False
curtime = int(time.time())

def send_elm_cmd(command):
    logging.debug(b'Sending ' + command)
    adapter.write(command + b'\r')
    # read response
    response = adapter.read_until(expected=b'\r')
    logging.debug(response)
    # wait for CLI
    logging.debug(adapter.read_until(expected=b'>'))
    return response


def get_data(i=0):
    global liveplot
    global voltage
    global current
    global soc
    global batt_temp_min
    global batt_temp_max
    global ignition_on
    global charging
    global fast_charging
    global curtime
    global batt_temp
    global APIKEY
    global TOKEN

    try:
        voltage = int((send_elm_cmd(b'03221e3b55555555').replace(b' ', b''))[8:12], 16) / 10
    except ValueError:
        logging.error("Unexpected value received from ECU")
    try:
        current = -1 * (int((send_elm_cmd(b'03221e3d55555555').replace(b' ', b''))[8:14], 16) - 150000) / 100
    except ValueError:
        logging.error("Unexpected value received from ECU")
    try:
        soc = int((send_elm_cmd(b'0322028C55555555').replace(b' ', b''))[8:10], 16)
        # note: doesn't match dash. I think this is "true" SOC, and might need to be scaled by min and max SOC to match
        # the dash
    except ValueError:
        logging.error("Unexpected value received from ECU")
    #try:
    #    batt_temp_min = (int((send_elm_cmd(b'03221e0f55555555').replace(b' ', b''))[8:10], 16) - 100)
    #except ValueError:
    #    logging.error("Unexpected value received from ECU")
    try:
        batt_temp = (int((send_elm_cmd(b'03222a0b55555555').replace(b' ', b''))[8:10], 16) - 100)
    except ValueError:
        logging.error("Unexpected value received from ECU")
    try:
        state = int((send_elm_cmd(b'0322744855555555').replace(b' ', b''))[8:10], 16)
        ignition_on = bool(state & 0x1)
        charging = bool(state & 0x4)
        fast_charging = bool(state & 0x2)
    except ValueError:
        logging.error("Unexpected value received from ECU")
    curtime = int(time.time())

    tlm = {
        "utc": curtime,
        "soc": soc,
        "power": "{:.3f}".format(voltage * current / 1000),
        "is_charging": charging,
        "is_dcfc": fast_charging,
        "batt_temp": batt_temp,
        "voltage": voltage,
        "current": current
    }
    url = f"https://api.iternio.com/1/tlm/send?api_key={APIKEY}&token={TOKEN}&tlm={json.dumps(tlm)}"
    logging.debug(url)
    result = requests.post(url)
    logging.debug(result.text)

    # capacity: try unit 17 Header 714/77E, 22 22 E4	(aa*2^8+bb)/10	kWh
    # outside temp: try unit 01 Header 7E0/7E8, 22 F4 46	aa-40	°C	Outside temperature
    # speed: try unit 01, 22 F4 0D	aa	km/h	Vehicle speed
    # parked: try unit 01, 22 14 CB	 	 	(Only for the 2020 model) Gear direction: -1 = backwards,
    # 0 = neutral, 1 = forwards
    # odometer: try unit 17, 22 22 03	(aa*2^8+bb)*10	km	Distance
    # rnge: try unit 17, 22 22 E0	aa*2^8+bb	km	Range indicated, electric drive
    # 22 22 E1	aa*2^8+bb	km	Range calculated, electric drive

    print("Voltage:  " + str(voltage) + "V")
    print("Current:  %.2fA" % current)
    print("Power:    %.2fkW" % (voltage * current / 1000))
    print("SoC:      " + str(soc) + "%")
    print("Batt Temp: " + str(batt_temp) + "°C")
    print("Ignition: " + str(ignition_on))
    print("Charging: " + str(charging))
    print("DCFC:     " + str(fast_charging))
    print("Time:     " + str(curtime))
    print()

    if liveplot:
        # append power and voltage for plotting
        powers.popleft()
        powers.append(voltage * current / 1000)
        voltages.popleft()
        voltages.append(voltage)

        # configure power plot
        ax.cla()
        ax.plot(powers)
        ax.scatter(len(powers) - 1, powers[-1])
        ax.text(len(powers) - 1, powers[-1], "{:.2f}kW".format(powers[-1]))
        ax.set_ylim(min(0, min(powers)), max(0, max(powers)))

        # configure voltage plot
        ax1.cla()
        ax1.plot(voltages)
        ax1.scatter(len(voltages) - 1, voltages[-1])
        ax1.text(len(voltages) - 1, voltages[-1], "{:.2f}V".format(voltages[-1]))
        ax1.set_ylim(0, max(voltages))


if __name__ == '__main__':
    # setup logging
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    print('Starting up...')

    # read API Key and Token
    f = open("APIKEY", "r")
    APIKEY = f.read().replace("\n", "")
    logging.info("APIKEY: " + APIKEY)
    f = open("TOKEN", "r")
    TOKEN = f.read().replace("\n", "")
    logging.info("TOKEN: " + TOKEN)

    adapter = serial.Serial(port='COM7', timeout=1)
    if adapter.isOpen():
        logging.info("Interface Open")

    logging.info("Sending init commands")
    send_elm_cmd(b'ATD') # defaults
    send_elm_cmd(b'ATZ')  # reset
    send_elm_cmd(b'ATE0')  # echo off
    send_elm_cmd(b'ATL0')  # linefeeds off
    send_elm_cmd(b'ATSP7')  # set protocol 7
    send_elm_cmd(b'ATBI')  # bypass initialization
    send_elm_cmd(b'ATSH FC007B')  # set header FC 00 7B
    send_elm_cmd(b'ATCP 17')  # can priority 17
    send_elm_cmd(b'ATCAF0')  # can automatic formatting off
    send_elm_cmd(b'ATCF 17F')  # can id filter set to 17F
    send_elm_cmd(b'ATCRA 17FE007B')  # can receive address to 17FE007B


    if liveplot:
        # set up graphing
        powers = collections.deque(np.zeros(60))
        voltages = collections.deque(np.zeros(60))
        # define and adjust figure
        fig = plt.figure(figsize=(6, 6), facecolor='#DEDEDE')
        ax = plt.subplot(121)
        ax1 = plt.subplot(122)
        ax.set_facecolor('#DEDEDE')
        ax1.set_facecolor('#DEDEDE')

        ani = FuncAnimation(fig, get_data, interval=1000)
        plt.show()
    else:
        while 1:
            get_data()
            time.sleep(10)

    print("closing!")
    adapter.close()
