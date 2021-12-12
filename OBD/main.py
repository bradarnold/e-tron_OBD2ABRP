# Assumes ODBLink MX on Bluetooth COM port, attached to 2019 Audi e-tron. Should also work with other ELM327 adapters.

import collections
import np as np
import serial
import time
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation
import logging, sys


def getdata(i):
    adapter.write(b'03221e3b55555555\r')  #
    voltage = int((adapter.read_until(expected=b'\r').replace(b' ', b''))[8:12], 16) / 10
    # wait for CLI
    adapter.read_until(expected=b'>')

    adapter.write(b'03221e3d55555555\r')  #
    current = -1 * (int((adapter.read_until(expected=b'\r').replace(b' ', b''))[8:14], 16) - 150000) / 100
    # wait for CLI
    adapter.read_until(expected=b'>')

    adapter.write(b'0322028C55555555\r')  #
    soc = int((adapter.read_until(expected=b'\r').replace(b' ', b''))[8:10], 16)
    # wait for CLI
    adapter.read_until(expected=b'>')

    adapter.write(b'03221e0e55555555\r')  #
    batt_temp_max = (int((adapter.read_until(expected=b'\r').replace(b' ', b''))[8:10], 16) - 100)
    # wait for CLI
    adapter.read_until(expected=b'>')

    adapter.write(b'03221e0f55555555\r')  #
    batt_temp_min = (int((adapter.read_until(expected=b'\r').replace(b' ', b''))[8:10], 16) - 100)
    # wait for CLI
    adapter.read_until(expected=b'>')

    adapter.write(b'0322744855555555\r')  #
    state = int((adapter.read_until(expected=b'\r').replace(b' ', b''))[8:10], 16)
    # wait for CLI
    adapter.read_until(expected=b'>')
    ignition_on = bool(state & 0x1)
    charging = bool(state & 0x4)
    fast_charging = bool(state & 0x2)

    print("Voltage:  " + str(voltage) + "V")
    print("Current:  %.2fA" % current)
    print("Power:    %.2fkW" % (voltage * current / 1000))
    print("SoC:      " + str(soc) + "%")
    print("Batt Temp min/max: " + str(batt_temp_min) + "/" + str(batt_temp_max) + "°C")
    print("Ignition: " + str(ignition_on))
    print("Charging: " + str(charging))
    print("DCFC:     " + str(fast_charging))
    print()

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
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    print('Running!')

    adapter = serial.Serial(port='COM7', timeout=1)
    if adapter.isOpen():
        logging.info("Interface Open")

    logging.info("Sending init commands")
    logging.debug("ATD")
    adapter.write(b'ATD\r')  # defaults
    # read response
    logging.debug(adapter.read_until(expected=b'\r'))
    # wait for CLI
    logging.debug(adapter.read_until(expected=b'>'))

    logging.debug("ATZ")
    adapter.write(b'ATZ\r')  # reset
    # read response
    logging.debug(adapter.read_until(expected=b'\r'))
    # wait for CLI
    logging.debug(adapter.read_until(expected=b'>'))

    logging.debug("ATE0")
    adapter.write(b'ATE0\r')  # echo off
    # read response
    logging.debug(adapter.read_until(expected=b'\r'))
    # wait for CLI
    logging.debug(adapter.read_until(expected=b'>'))

    logging.debug("ATL0")
    adapter.write(b'ATL0\r')  # linefeeds off
    # read response
    logging.debug(adapter.read_until(expected=b'\r'))
    # wait for CLI
    logging.debug(adapter.read_until(expected=b'>'))

    logging.debug("ATSP7")
    adapter.write(b'ATSP7\r')  # set protocol 7
    # read response
    logging.debug(adapter.read_until(expected=b'\r'))
    # wait for CLI
    logging.debug(adapter.read_until(expected=b'>'))

    logging.debug("ATBI")
    adapter.write(b'ATBI\r')  # bypass initialization
    # read response
    logging.debug(adapter.read_until(expected=b'\r'))
    # wait for CLI
    logging.debug(adapter.read_until(expected=b'>'))

    # start config'ing for EV #

    logging.debug("ATSH FC007B")
    adapter.write(b'ATSH FC007B\r')  # set header FC 00 7B
    # read response
    logging.debug(adapter.read_until(expected=b'\r'))
    # wait for CLI
    logging.debug(adapter.read_until(expected=b'>'))

    logging.debug("ATCP 17")
    adapter.write(b'ATCP 17\r')  # can priority 17
    # read response
    logging.debug(adapter.read_until(expected=b'\r'))
    # wait for CLI
    logging.debug(adapter.read_until(expected=b'>'))

    logging.debug("ATCAF0")
    adapter.write(b'ATCAF0\r')  # can automatic formatting off
    # read response
    logging.debug(adapter.read_until(expected=b'\r'))
    # wait for CLI
    logging.debug(adapter.read_until(expected=b'>'))

    logging.debug("ATCF 17FE7")
    adapter.write(b'ATCF 17F\r')  # can id filter set to 17FE7
    # read response
    logging.debug(adapter.read_until(expected=b'\r'))
    # wait for CLI
    logging.debug(adapter.read_until(expected=b'>'))

    logging.debug("ATCRA 17FE007B")
    adapter.write(b'ATCRA 17FE007B\r')  # can receive address to 17FE007B
    # read response
    logging.debug(adapter.read_until(expected=b'\r'))
    # wait for CLI
    logging.debug(adapter.read_until(expected=b'>'))

    # set up graphing
    powers = collections.deque(np.zeros(60))
    voltages = collections.deque(np.zeros(60))
    # define and adjust figure
    fig = plt.figure(figsize=(6, 6), facecolor='#DEDEDE')
    ax = plt.subplot(121)
    ax1 = plt.subplot(122)
    ax.set_facecolor('#DEDEDE')
    ax1.set_facecolor('#DEDEDE')

    ani = FuncAnimation(fig, getdata, interval=1000)
    plt.show()

    print("closing!")
    adapter.close()


# See PyCharm help at https://www.jetbrains.com/help/pycharm/
