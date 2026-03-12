from src.communication.uart_protocol import (
    MSG_ACK,
    MSG_CAL,
    MSG_GO,
    MSG_STOP,
    MSG_QUIT,
    MSG_CHK_SIT,
)


class CommandSender:
    def __init__(self, serial_conn):
        self.ser = serial_conn

    def _send_line(self, msg: str):
        data = (msg + "\n").encode("utf-8")
        self.ser.write(data)
        self.ser.flush()

    def send_ack(self):
        self._send_line(MSG_ACK)

    def send_check_sit(self):
        self._send_line(MSG_CHK_SIT)

    def send_cal(self):
        self._send_line(MSG_CAL)

    def send_go(self):
        self._send_line(MSG_GO)

    def send_stop(self):
        self._send_line(MSG_STOP)

    def send_quit(self):
        self._send_line(MSG_QUIT)