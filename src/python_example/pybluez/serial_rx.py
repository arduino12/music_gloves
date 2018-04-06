
# show all serial ports and open the given one
# Arad Eizen 2018-04-06

import sys
import bluetooth # pip install pybluez OR https://github.com/karulis/pybluez -> python setup.py install

BT_SCAN_TIMEOUT = 3
BT_READ_SIZE = 1024
BT_RFCOMM_CHANNEL = 2
BT_NEWLINE = b'\r\n'


def main():
    sep = '\n' + '=' * 80 + '\n'
    
    print(sep)
    print('show all bluetooth devices and connect the given one')
    print('scannig for %s seconds...' % (BT_SCAN_TIMEOUT,))
    print(sep)

    # list all available devices
    devices = bluetooth.discover_devices(duration=BT_SCAN_TIMEOUT, lookup_names=True)
    for address, name in devices:
        print('%s -> %s' % (address, name))
    print(sep)

    # connect to the given device
    address = input('enter device address (like 00:11:22:33:44:55): ')
    bt_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    bt_socket.connect((address, BT_RFCOMM_CHANNEL))
    bt_socket.settimeout(0.01)
    bt_socket_buff = b''

    print('press ctrl+c to exit')
    print(sep)
    while True:
        try:
            # read full line and print it on top of the previous line
            bt_socket_buff += bt_socket.recv(BT_READ_SIZE)
            if BT_NEWLINE in bt_socket_buff:
                line, bt_socket_buff = bt_socket_buff.split(BT_NEWLINE, 1)
                sys.stdout.write('\r' + ' ' * 80)
                sys.stdout.write('\r%s' % (line.decode().strip(),))
                sys.stdout.flush()
        except KeyboardInterrupt:
            break
        except Exception:
            continue

    bt_socket.close()


if __name__ == '__main__':
    main()
