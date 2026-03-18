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


def _rand_list(count, low, high):
    return [random.randint(low, high) for _ in range(count)]


def read_mock_sensor(posture=None):
    if posture is None:
        posture = random.choice(POSTURE_LABELS)

    # ------------------------------------------------------------------
    # Packet structure target
    # {
    #   "loadcell": [12],
    #   "tof_1d": [4],
    #   "tof_3d": [32],
    #   "mpu": [2],
    # }
    # ------------------------------------------------------------------

    # 기본값
    loadcell = [0] * 12
    tof_1d = [0] * 4
    tof_3d = [0] * 32
    mpu = [0] * 2

    if posture == "normal":
        # back right 0~3
        loadcell[0:4] = _rand_list(4, 8, 12)
        # back left 4~7
        loadcell[4:8] = _rand_list(4, 8, 12)
        # seat 8~11
        loadcell[8] = random.randint(10, 14)   # rear right
        loadcell[9] = random.randint(10, 14)   # front right
        loadcell[10] = random.randint(10, 14)  # rear left
        loadcell[11] = random.randint(10, 14)  # front left

        tof_1d = _rand_list(4, 18, 22)
        tof_3d = _rand_list(32, 18, 22)
        mpu = [random.randint(-2, 2), random.randint(-2, 2)]

    elif posture == "turtle_neck":
        loadcell[0:4] = _rand_list(4, 8, 12)
        loadcell[4:8] = _rand_list(4, 8, 12)
        loadcell[8:12] = _rand_list(4, 10, 14)

        tof_1d = _rand_list(4, 18, 22)
        # head distance 증가 느낌
        tof_3d = _rand_list(32, 30, 36)
        mpu = [random.randint(1, 4), random.randint(2, 5)]

    elif posture == "forward_lean":
        loadcell[0:4] = _rand_list(4, 6, 10)
        loadcell[4:8] = _rand_list(4, 6, 10)

        loadcell[8] = random.randint(7, 10)    # rear right
        loadcell[9] = random.randint(14, 18)   # front right
        loadcell[10] = random.randint(7, 10)   # rear left
        loadcell[11] = random.randint(14, 18)  # front left

        # 상체 전체가 앞으로 기운 느낌
        tof_1d[0] = random.randint(31, 37)
        tof_1d[1] = random.randint(27, 33)
        tof_1d[2] = random.randint(23, 29)
        tof_1d[3] = random.randint(19, 25)

        # 목 3D ToF는 normal보다 아주 조금만 증가
        # turtle_neck처럼 neck_mean_delta가 크게 뛰지 않게 제한
        tof_3d = _rand_list(32, 20, 24)

        # 전방 기울기만 강하게
        mpu = [random.randint(8, 14), random.randint(8, 14)]

    elif posture == "reclined":
        loadcell[0:4] = _rand_list(4, 13, 18)
        loadcell[4:8] = _rand_list(4, 13, 18)

        loadcell[8] = random.randint(13, 16)
        loadcell[9] = random.randint(8, 11)
        loadcell[10] = random.randint(13, 16)
        loadcell[11] = random.randint(8, 11)

        tof_1d[0] = random.randint(14, 18)
        tof_1d[1] = random.randint(15, 19)
        tof_1d[2] = random.randint(16, 20)
        tof_1d[3] = random.randint(17, 21)

        tof_3d = _rand_list(32, 16, 20)
        mpu = [random.randint(-12, -6), random.randint(-12, -6)]

    elif posture == "side_slouch":
        direction = random.choice(["right", "left"])

        if direction == "right":
            loadcell[0:4] = _rand_list(4, 11, 16)
            loadcell[4:8] = _rand_list(4, 5, 9)

            loadcell[8] = random.randint(12, 16)
            loadcell[9] = random.randint(12, 16)
            loadcell[10] = random.randint(7, 10)
            loadcell[11] = random.randint(7, 10)

            tof_3d[:16] = _rand_list(16, 21, 27)
            tof_3d[16:] = _rand_list(16, 17, 22)
        else:
            loadcell[0:4] = _rand_list(4, 5, 9)
            loadcell[4:8] = _rand_list(4, 11, 16)

            loadcell[8] = random.randint(7, 10)
            loadcell[9] = random.randint(7, 10)
            loadcell[10] = random.randint(12, 16)
            loadcell[11] = random.randint(12, 16)

            tof_3d[:16] = _rand_list(16, 17, 22)
            tof_3d[16:] = _rand_list(16, 21, 27)

        tof_1d = _rand_list(4, 18, 24)
        mpu = [random.randint(-5, 5), random.randint(-5, 5)]

    elif posture == "leg_cross_suspect":
        direction = random.choice(["right", "left"])

        loadcell[0:4] = _rand_list(4, 7, 11)
        loadcell[4:8] = _rand_list(4, 7, 11)

        if direction == "right":
            loadcell[8] = random.randint(12, 15)
            loadcell[9] = random.randint(12, 15)
            loadcell[10] = random.randint(8, 10)
            loadcell[11] = random.randint(8, 10)
        else:
            loadcell[8] = random.randint(8, 10)
            loadcell[9] = random.randint(8, 10)
            loadcell[10] = random.randint(12, 15)
            loadcell[11] = random.randint(12, 15)

        tof_1d = _rand_list(4, 18, 23)
        tof_3d = _rand_list(32, 18, 23)
        mpu = [random.randint(-2, 2), random.randint(-2, 2)]

    elif posture == "thinking_pose":
        # 등판은 normal과 비슷하거나 약간만 감소
        loadcell[0:4] = _rand_list(4, 8, 11)
        loadcell[4:8] = _rand_list(4, 8, 11)

        # 좌판은 아주 약한 전방 쏠림만
        loadcell[8] = random.randint(9, 11)   # rear right
        loadcell[9] = random.randint(11, 13)  # front right
        loadcell[10] = random.randint(9, 11)  # rear left
        loadcell[11] = random.randint(11, 13) # front left

        # 상부만 약간 앞으로, forward_lean처럼 전체 붕괴는 아님
        tof_1d[0] = random.randint(22, 24)
        tof_1d[1] = random.randint(21, 23)
        tof_1d[2] = random.randint(20, 22)
        tof_1d[3] = random.randint(19, 21)

        # 목 전방은 normal보다 조금만 크게
        tof_3d = _rand_list(32, 22, 24)

        # 약한~중간 정도 기울기
        mpu = [random.randint(2, 4), random.randint(2, 4)]

    elif posture == "perching":
        # 등판 접촉 거의 없음
        loadcell[0:4] = _rand_list(4, 0, 2)
        loadcell[4:8] = _rand_list(4, 0, 2)

        # 좌판 앞쪽에 강하게 걸터앉음
        loadcell[8] = random.randint(2, 4)    # rear right
        loadcell[9] = random.randint(17, 21)  # front right
        loadcell[10] = random.randint(2, 4)   # rear left
        loadcell[11] = random.randint(17, 21) # front left

        # 상체는 전방으로 기울지만 spine 전체 붕괴는 forward_lean보다 약간 덜하게
        tof_1d[0] = random.randint(23, 28)
        tof_1d[1] = random.randint(20, 25)
        tof_1d[2] = random.randint(18, 22)
        tof_1d[3] = random.randint(16, 20)

        tof_3d = _rand_list(32, 20, 24)
        mpu = [random.randint(7, 10), random.randint(7, 10)]

    else:
        raise ValueError(f"Unknown posture: {posture}")

    return {
        "loadcell": loadcell,
        "tof_1d": tof_1d,
        "tof_3d": tof_3d,
        "mpu": mpu,
    }