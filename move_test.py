#!/usr/bin/env python3

import os
import argparse
from scservo_sdk import *  # Uses SCServo SDK library

# Control table address
ADDR_SCS_TORQUE_ENABLE = 40
ADDR_SCS_GOAL_POSITION = 42
ADDR_SCS_GOAL_SPEED = 46

# Default setting
BAUDRATE = 1000000  # SCServo default baudrate : 1000000
DEVICENAME = "/dev/serial0"
SCS_MOVING_STATUS_THRESHOLD = 20  # SCServo moving status threshold
protocol_end = 0  # SCServo bit end(STS/SMS=0, SCS=1)
motor_velocity = 300
move_range = 80
badurate_list = [1000000, 500000, 250000, 128000, 115200, 76800, 57600, 38400]

def main() -> None:
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        "--port",
        help="シリアルポートを指定します",
        default="/dev/serial0",
        type=str,
    )
    parser.add_argument(
        "-i",
        "--id",
        help="feetechサーボのidを指定します",
        default=1,
        type=int,
    )
    parser.add_argument(
        "-m",
        "--move_pos",
        help="移動先のfeetechサーボのposを指定します",
        default=2048,
        type=int,
    )
    args = parser.parse_args()

    if os.name == "nt":
        import msvcrt

    else:
        import sys, tty, termios

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)

    portHandler = PortHandler(DEVICENAME)
    packetHandler = PacketHandler(protocol_end)

    # Open port
    if portHandler.openPort():
        print("シリアルポートを開きました。")
    else:
        print("[ERROR] シリアルポートのOpenに失敗しました。")
        quit()

    cur_baudrate = None
    for baudrate in badurate_list:
        # Set port baudrate
        if portHandler.setBaudRate(baudrate):
            print(f"シリアルポートをbaudrate: {baudrate} にセットしました。feetechサーボを探索します。")
        else:
            print(f"シリアルポートがbaudrate: {baudrate}に対応していません。スキップします。")
            continue
        scs_model_number, scs_comm_result, scs_error = packetHandler.ping(
                    portHandler, args.id
                )
        if scs_comm_result == COMM_SUCCESS and scs_error == 0:
            cur_baudrate = baudrate
            print(f"baudrate: {baudrate} にfeetechサーボID: {args.id}を発見しました。")
            break
    if cur_baudrate is None:
        print(f"[ERROR] サーボID: {args.id}が見つかりませんでした")
        return

    # サーボON
    scs_comm_result, scs_error = packetHandler.write1ByteTxRx(
        portHandler, args.id, ADDR_SCS_TORQUE_ENABLE, 1
    )
    if scs_comm_result != COMM_SUCCESS:
        print(f"[ERROR] ID: {args.id} のサーボONに失敗しました。ID, Baudrateが正しいか、接続が正しいか確認してください。")
        print("[ERROR] %s" % packetHandler.getTxRxResult(scs_comm_result))
        return
    elif scs_error != 0:
        print(f"[ERROR] ID: {args.id} のサーボONに失敗しました。ID, Baudrateが正しいか、接続が正しいか確認してください。")
        print("[ERROR] %s" % packetHandler.getRxPacketError(scs_error))
        return

    print()
    print(f"ENTERキーを入力すると、サーボID{args.id}が{args.move_pos}に動きます。")
    input()

    # 速度を落とす
    scs_comm_result, scs_error = packetHandler.write2ByteTxRx(
        portHandler, args.id, ADDR_SCS_GOAL_SPEED, motor_velocity
    )
    # 0pos
    scs_comm_result, scs_error = packetHandler.write2ByteTxRx(
        portHandler, args.id, ADDR_SCS_GOAL_POSITION, args.move_pos
    )
    if scs_comm_result != COMM_SUCCESS:
        print("%s" % packetHandler.getTxRxResult(scs_comm_result))
        print(f"{args.move_pos}に動きました。")
    elif scs_error != 0:
        print("%s" % packetHandler.getRxPacketError(scs_error))

    print(f"ENTERキーを入力をすると、サーボID{args.id}が少し動きます。正しいサーボが動くか確認してください。")
    input()

    # +40動く
    scs_comm_result, scs_error = packetHandler.write2ByteTxRx(
        portHandler, args.id, ADDR_SCS_GOAL_POSITION, args.move_pos + move_range
    )
    time.sleep(1)
    # -40動く
    scs_comm_result, scs_error = packetHandler.write2ByteTxRx(
        portHandler, args.id, ADDR_SCS_GOAL_POSITION, args.move_pos - move_range
    )
    time.sleep(1)
    # 元の位置へ
    scs_comm_result, scs_error = packetHandler.write2ByteTxRx(
        portHandler, args.id, ADDR_SCS_GOAL_POSITION, args.move_pos
    )
    time.sleep(0.5)

    print("ENTERキーを入力をするとサーボOFFします。")
    input()

    # サーボOFF
    scs_comm_result, scs_error = packetHandler.write1ByteTxRx(
        portHandler, args.id, ADDR_SCS_TORQUE_ENABLE, 0
    )
    if scs_comm_result == COMM_SUCCESS:
        print(f"id:{args.id} サーボOFFしました。")
    else:
        print("[ERROR] %s" % packetHandler.getTxRxResult(scs_comm_result))
    if scs_error != 0:
        print("[ERROR] %s" % packetHandler.getRxPacketError(scs_error))

    print("------------------------")
    print("テスト完了！")
    print("------------------------")
    # Close port
    portHandler.closePort()

if __name__ == "__main__":
    main()
