# UART Protocol

## Link
- STM32 <-> Raspberry Pi
- UART bi-directional
- Baud rate: 921600

---

## STM32 -> RPi Sensor Packet

### Header
- 0xAA 0x55

### Packet Structure
- header: 2 bytes
- type: 1 byte
- length: 2 bytes
- payload: variable

### Payload Fields
- seq: uint16
- timestamp: uint32

- loadcell_fl: int16
- loadcell_fr: int16
- loadcell_bl: int16
- loadcell_br: int16

- acc_x: int16
- acc_y: int16
- acc_z: int16

- gyro_x: int16
- gyro_y: int16
- gyro_z: int16

- tof_upper: int16
- tof_mid: int16
- tof_lower: int16
- tof_left: int16
- tof_right: int16
- tof_neck: int16

- crc16: uint16 (추후 추가/고정)

---

## RPi -> STM32 Command Packet

### Header
- 0x55 0xAA

### Packet Structure
- header: 2 bytes
- type: 1 byte
- length: 2 bytes
- payload: variable

### Command IDs
- 0x01: vibration on
- 0x02: vibration off
- 0x03: buzzer short
- 0x04: buzzer long
- 0x05: start calibration
- 0x06: set mode

---

## Notes
- VL53L8CX raw 8x8 전체를 그대로 보내지 않고,
  upper/mid/lower/left/right/neck summary 값으로 먼저 전송한다.
- 실제 구현 시 CRC16 및 sequence number 기반 packet loss 체크를 추가한다.
- loadcell / IMU / ToF 스케일링 단위는 STM32 펌웨어와 반드시 일치시킨다.