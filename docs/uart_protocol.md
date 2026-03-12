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

### Packet Types
```text
| Type | Description |
|-----|-------------|
| 0x01 | Sensor Data Packet |
| 0x02 | STAND Event |
| 0x03 | SIT Event |
| 0x04 | System Status |
```

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

### Payload Size

센서 데이터 패킷의 예상 크기

- seq: 2 bytes
- timestamp: 4 bytes
- loadcells: 8 bytes
- IMU acc: 6 bytes
- IMU gyro: 6 bytes
- ToF sensors: 12 bytes

Total payload ≈ 38 bytes

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

### Command Payload
```text
| Command | Payload |
|-------|--------|
| vibration on | none |
| vibration off | none |
| buzzer short | none |
| buzzer long | none |
| start calibration | none |
| set mode | uint8 mode_id |
```
---

## Example Sensor Packet

Example (hex)

AA 55
01
26 00
01 00
12 34 56 78
10 00 12 00 11 00 10 00
05 00 02 00 FF 00
03 00 04 00 05 00 02 00 01 00 07 00
AB CD

---

## Error Handling

다음 조건에서 패킷을 폐기한다.

- header mismatch
- payload length mismatch
- CRC mismatch
- sequence jump

RPi는 sequence number를 기반으로 packet loss를 감지할 수 있다.

---

## Notes
- VL53L8CX raw 8x8 전체를 그대로 보내지 않고,
  upper/mid/lower/left/right/neck summary 값으로 먼저 전송한다.
- 실제 구현 시 CRC16 및 sequence number 기반 packet loss 체크를 추가한다.
- loadcell / IMU / ToF 스케일링 단위는 STM32 펌웨어와 반드시 일치시킨다.