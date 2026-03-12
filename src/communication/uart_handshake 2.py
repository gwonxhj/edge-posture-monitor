import serial
import time

READY_MSG = b"READY\n"
ACK_MSG = b"ACK\n"
START_MSG = b"START\n"

def wait_for_ready(ser):
    print("Waiting STM32 READY...")

    while True:
        line = ser.readline()

        if b"READY" in line:
            print("STM32 READY received")
            return


def send_ack(ser):
    print("Sending ACK to STM32")
    ser.write(ACK_MSG)


def wait_for_start(ser):
    print("Waiting START signal")

    while True:
        line = ser.readline()

        if b"START" in line:
            print("STM32 START received")
            return