BAUD_RATE = 921600

# Binary sensor packet framing
STX1 = 0x02
STX2 = 0xAA
ETX = 0x03

PACKET_TYPE_SENSOR = 0x01
SENSOR_VALUE_COUNT = 22

# ASCII control messages
MSG_READY = "READY"
MSG_ACK = "ACK"
MSG_LINK_OK = "LINK_OK"

# Seat / calibration / measurement flow
MSG_CHK_SIT = "CHK_SIT"   # RPi -> STM32 : 착석 확인 시작
MSG_SIT = "SIT"           # STM32 -> RPi : 착석 확인됨
MSG_CAL = "CAL"           # RPi -> STM32 : 캘리브레이션 시작
MSG_GO = "GO"             # RPi -> STM32 : 일반 측정 시작
MSG_STOP = "STOP"         # RPi -> STM32 : 측정 일시중지 / 준비 상태 해제
MSG_QUIT = "QUIT"         # RPi -> STM32 : 오늘 세션 완전 종료
MSG_STAND = "STAND"       # STM32 -> RPi : 사용자 일어섬 확인