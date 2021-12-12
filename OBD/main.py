# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import collections

import np as np
import serial
import time


# Press the green button in the gutter to run the script.
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation

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

    powers.popleft()
    powers.append(voltage * current / 1000)
    voltages.popleft()
    voltages.append(voltage)

    ax.cla()
    ax.plot(powers)
    ax.scatter(len(powers) - 1, powers[-1])
    ax.text(len(powers) - 1, powers[-1], "{:.2f}kW".format(powers[-1]))
    ax.set_ylim(min(0, min(powers)), max(0, max(powers)))

    ax1.cla()
    ax1.plot(voltages)
    ax1.scatter(len(voltages) - 1, voltages[-1])
    ax1.text(len(voltages) - 1, voltages[-1], "{:.2f}V".format(voltages[-1]))
    ax1.set_ylim(0, max(voltages))

if __name__ == '__main__':

    print('Running!')
    adapter = serial.Serial(port='COM7', timeout=1)
    if adapter.isOpen():
        print("Interface Open")

    print("init commands")
    print("ATD")
    adapter.write(b'ATD\r')  # defaults
    # read response
    print(adapter.read_until(expected=b'\r'))
    # wait for CLI
    print(adapter.read_until(expected=b'>'))

    print("ATZ")
    adapter.write(b'ATZ\r')  # reset
    # read response
    print(adapter.read_until(expected=b'\r'))
    # wait for CLI
    print(adapter.read_until(expected=b'>'))

    print("ATE0")
    adapter.write(b'ATE0\r')  # echo off
    # read response
    print(adapter.read_until(expected=b'\r'))
    # wait for CLI
    print(adapter.read_until(expected=b'>'))

    print("ATL0")
    adapter.write(b'ATL0\r')  # linefeeds off
    # read response
    print(adapter.read_until(expected=b'\r'))
    # wait for CLI
    print(adapter.read_until(expected=b'>'))

    print("ATSP7")
    adapter.write(b'ATSP7\r')  # set protocol 7
    # read response
    print(adapter.read_until(expected=b'\r'))
    # wait for CLI
    print(adapter.read_until(expected=b'>'))

    print("ATBI")
    adapter.write(b'ATBI\r')  # bypass initialization
    # read response
    print(adapter.read_until(expected=b'\r'))
    # wait for CLI
    print(adapter.read_until(expected=b'>'))

    # start config'ing for EV #

    print("ATSH FC007B")
    adapter.write(b'ATSH FC007B\r')  # set header FC 00 7B
    # read response
    print(adapter.read_until(expected=b'\r'))
    # wait for CLI
    print(adapter.read_until(expected=b'>'))

    print("ATCP 17")
    adapter.write(b'ATCP 17\r')  # can priority 17
    # read response
    print(adapter.read_until(expected=b'\r'))
    # wait for CLI
    print(adapter.read_until(expected=b'>'))

    print("ATCAF0")
    adapter.write(b'ATCAF0\r')  # can automatic formatting off
    # read response
    print(adapter.read_until(expected=b'\r'))
    # wait for CLI
    print(adapter.read_until(expected=b'>'))

    print("ATCF 17FE7")
    adapter.write(b'ATCF 17F\r')  # can id filter set to 17FE7
    # read response
    print(adapter.read_until(expected=b'\r'))
    # wait for CLI
    print(adapter.read_until(expected=b'>'))

    print("ATCRA 17FE007B")
    adapter.write(b'ATCRA 17FE007B\r')  # can id filter set to 17FE7
    # read response
    print(adapter.read_until(expected=b'\r'))
    # wait for CLI
    print(adapter.read_until(expected=b'>'))

    powers = collections.deque(np.zeros(60))
    voltages = collections.deque(np.zeros(60))
    # define and adjust figure
    fig = plt.figure(figsize=(6, 6), facecolor='#DEDEDE')
    ax = plt.subplot(121)
    ax1 = plt.subplot(122)
    ax.set_facecolor('#DEDEDE')
    ax1.set_facecolor('#DEDEDE')

    # while 1:
    #     getdata(0)
    #     time.sleep(1)

    ani = FuncAnimation(fig, getdata, interval=1000)
    plt.show()

    print("closing!")
    adapter.close()


# See PyCharm help at https://www.jetbrains.com/help/pycharm/
