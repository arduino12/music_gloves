
# show all serial ports and open the given one
# Arad Eizen 2018-03-28

import sys
import serial # pip install pyserial (3.4)
from serial.tools import list_ports


def main():
    sep = '\n' + '=' * 80 + '\n'
    
    print(sep)
    print('show all serial ports and open the given one')
    print(sep)

    # list all available serial ports
    for i in list_ports.comports():
        print(str(i))
    print(sep)

    # open the given port
    serial_port_name = input('enter serial port name (like COM1): ')
    serial_port = serial.Serial(serial_port_name, timeout=1)

    print('press ctrl+c to exit')
    print(sep)
    while True:
        try:
            # read full line and print it on top of the previous line
            line = serial_port.read_until(b'\r\n')
            if line:
                sys.stdout.write('\r' + ' ' * 80)
                sys.stdout.write('\r%s' % (line.decode().strip(),))
                sys.stdout.flush()
        except KeyboardInterrupt:
            break
        except Exception:
            continue

    serial_port.close()


if __name__ == '__main__':
    main()
