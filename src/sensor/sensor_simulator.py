import random


POSTURE_LABELS = [
    "normal",
    "turtle_neck",
    "forward_lean",
    "reclined",
    "side_slouch",
    "leg_cross_suspect",
    "thinking_pose",
    "perching",
]


def read_mock_sensor(posture=None):
    if posture is None:
        posture = random.choice(POSTURE_LABELS)

    values = [0.0] * 22

    if posture == "normal":
        for i in range(0, 8):
            values[i] = random.uniform(8.0, 12.0)

        for i in range(8, 12):
            values[i] = random.uniform(10.0, 14.0)

        values[12] = random.uniform(18.0, 22.0)
        values[13] = random.uniform(18.0, 22.0)

        for i in range(14, 18):
            values[i] = random.uniform(18.0, 22.0)

        values[18] = random.uniform(-3.0, 3.0)
        values[19] = random.uniform(-3.0, 3.0)
        values[20] = random.uniform(-3.0, 3.0)
        values[21] = random.uniform(-2.0, 2.0)

    elif posture == "turtle_neck":
        for i in range(0, 8):
            values[i] = random.uniform(8.0, 12.0)

        for i in range(8, 12):
            values[i] = random.uniform(10.0, 14.0)

        values[12] = random.uniform(30.0, 36.0)
        values[13] = random.uniform(30.0, 36.0)

        for i in range(14, 18):
            values[i] = random.uniform(18.0, 22.0)

        values[18] = random.uniform(-2.0, 2.0)
        values[19] = random.uniform(2.0, 5.0)
        values[20] = random.uniform(-2.0, 2.0)
        values[21] = random.uniform(2.0, 5.0)

    elif posture == "forward_lean":
        for i in range(0, 8):
            values[i] = random.uniform(6.0, 10.0)

        values[8] = random.uniform(7.0, 10.0)    # seat right rear
        values[9] = random.uniform(13.0, 17.0)   # seat right front
        values[10] = random.uniform(7.0, 10.0)   # seat left rear
        values[11] = random.uniform(13.0, 17.0)  # seat left front

        values[12] = random.uniform(24.0, 30.0)
        values[13] = random.uniform(24.0, 30.0)

        values[14] = random.uniform(30.0, 36.0)
        values[15] = random.uniform(26.0, 32.0)
        values[16] = random.uniform(22.0, 28.0)
        values[17] = random.uniform(18.0, 24.0)

        values[18] = random.uniform(-3.0, 3.0)
        values[19] = random.uniform(8.0, 15.0)
        values[20] = random.uniform(-3.0, 3.0)
        values[21] = random.uniform(8.0, 14.0)

    elif posture == "reclined":
        for i in range(0, 8):
            values[i] = random.uniform(13.0, 18.0)

        values[8] = random.uniform(13.0, 16.0)   # rear
        values[9] = random.uniform(8.0, 11.0)    # front
        values[10] = random.uniform(13.0, 16.0)  # rear
        values[11] = random.uniform(8.0, 11.0)   # front

        values[12] = random.uniform(16.0, 20.0)
        values[13] = random.uniform(16.0, 20.0)

        values[14] = random.uniform(14.0, 18.0)
        values[15] = random.uniform(15.0, 19.0)
        values[16] = random.uniform(16.0, 20.0)
        values[17] = random.uniform(17.0, 21.0)

        values[18] = random.uniform(-3.0, 3.0)
        values[19] = random.uniform(-12.0, -6.0)
        values[20] = random.uniform(-3.0, 3.0)
        values[21] = random.uniform(-12.0, -6.0)

    elif posture == "side_slouch":
        direction = random.choice(["right", "left"])

        if direction == "right":
            for i in range(0, 4):
                values[i] = random.uniform(11.0, 16.0)
            for i in range(4, 8):
                values[i] = random.uniform(5.0, 9.0)

            values[8] = random.uniform(12.0, 16.0)
            values[9] = random.uniform(12.0, 16.0)
            values[10] = random.uniform(7.0, 10.0)
            values[11] = random.uniform(7.0, 10.0)

            values[12] = random.uniform(21.0, 27.0)
            values[13] = random.uniform(17.0, 22.0)
        else:
            for i in range(0, 4):
                values[i] = random.uniform(5.0, 9.0)
            for i in range(4, 8):
                values[i] = random.uniform(11.0, 16.0)

            values[8] = random.uniform(7.0, 10.0)
            values[9] = random.uniform(7.0, 10.0)
            values[10] = random.uniform(12.0, 16.0)
            values[11] = random.uniform(12.0, 16.0)

            values[12] = random.uniform(17.0, 22.0)
            values[13] = random.uniform(21.0, 27.0)

        for i in range(14, 18):
            values[i] = random.uniform(18.0, 24.0)

        values[18] = random.uniform(-3.0, 3.0)
        values[19] = random.uniform(-6.0, 6.0)
        values[20] = random.uniform(-3.0, 3.0)
        values[21] = random.uniform(-5.0, 5.0)

    elif posture == "leg_cross_suspect":
        direction = random.choice(["right", "left"])

        for i in range(0, 8):
            values[i] = random.uniform(7.0, 11.0)

        if direction == "right":
            values[8] = random.uniform(12.0, 15.0)
            values[9] = random.uniform(12.0, 15.0)
            values[10] = random.uniform(8.0, 10.0)
            values[11] = random.uniform(8.0, 10.0)
        else:
            values[8] = random.uniform(8.0, 10.0)
            values[9] = random.uniform(8.0, 10.0)
            values[10] = random.uniform(12.0, 15.0)
            values[11] = random.uniform(12.0, 15.0)

        values[12] = random.uniform(18.0, 23.0)
        values[13] = random.uniform(18.0, 23.0)

        for i in range(14, 18):
            values[i] = random.uniform(18.0, 23.0)

        values[18] = random.uniform(-2.0, 2.0)
        values[19] = random.uniform(-2.0, 2.0)
        values[20] = random.uniform(-2.0, 2.0)
        values[21] = random.uniform(-2.0, 2.0)

    elif posture == "thinking_pose":
        for i in range(0, 8):
            values[i] = random.uniform(5.0, 9.0)

        values[8] = random.uniform(7.0, 10.0)
        values[9] = random.uniform(12.0, 16.0)
        values[10] = random.uniform(7.0, 10.0)
        values[11] = random.uniform(12.0, 16.0)

        values[12] = random.uniform(28.0, 34.0)
        values[13] = random.uniform(28.0, 34.0)

        values[14] = random.uniform(28.0, 34.0)
        values[15] = random.uniform(24.0, 30.0)
        values[16] = random.uniform(20.0, 26.0)
        values[17] = random.uniform(16.0, 22.0)

        values[18] = random.uniform(-3.0, 3.0)
        values[19] = random.uniform(5.0, 10.0)
        values[20] = random.uniform(-3.0, 3.0)
        values[21] = random.uniform(4.0, 9.0)

    elif posture == "perching":
        for i in range(0, 8):
            values[i] = random.uniform(3.0, 6.0)

        values[8] = random.uniform(5.0, 8.0)
        values[9] = random.uniform(15.0, 19.0)
        values[10] = random.uniform(5.0, 8.0)
        values[11] = random.uniform(15.0, 19.0)

        values[12] = random.uniform(24.0, 30.0)
        values[13] = random.uniform(24.0, 30.0)

        values[14] = random.uniform(26.0, 32.0)
        values[15] = random.uniform(22.0, 28.0)
        values[16] = random.uniform(18.0, 24.0)
        values[17] = random.uniform(14.0, 20.0)

        values[18] = random.uniform(-3.0, 3.0)
        values[19] = random.uniform(7.0, 12.0)
        values[20] = random.uniform(-3.0, 3.0)
        values[21] = random.uniform(7.0, 12.0)

    else:
        raise ValueError(f"Unknown posture: {posture}")

    return {
        "seq": random.randint(0, 65535),
        "timestamp_ms": random.randint(100000, 999999),
        "values": values,
    }