#!/usr/bin/env python3

import os
import argparse
from scservo_sdk import *  # Uses SCServo SDK library

protocol_end = 0  # SCServo bit end(STS/SMS=0, SCS=1)
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
        help="現在のfeetechサーボのidを指定します",
        default=1,
        type=int,
    )
    parser.add_argument(
        "-c",
        "--changed_id",
        help="変更後のfeetechサーボのidを指定します",
        type=int,
    )
    args = parser.parse_args()

    if os.name == "nt":
        import msvcrt

    else:
        import sys, tty, termios

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)

    portHandler = PortHandler(args.port)
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

    print()
    # EEPROM ROCK解除
    scs_comm_result, scs_error = packetHandler.write1ByteTxRx(
        portHandler, args.id, 55, 0
    )
    if scs_comm_result == COMM_SUCCESS:
        print(f"EEPROMロック解除しました。")
    else:
        print(f"[ERROR] EPROMロック解除に失敗しました。")
        return

    # IDの変更
    for i in range(0, 3):
        time.sleep(0.5)
        scs_comm_result, scs_error = packetHandler.write1ByteTxRx(
            portHandler, args.id, 5, args.changed_id
        )
        if scs_comm_result == COMM_SUCCESS or COMM_RX_TIMEOUT:
            print(f"サーボのidを {args.id} から {args.changed_id} に変更しました。")
            break
        else:
            if i == 2:
                print(
                    "[ERROR] サーボのidの変更に失敗しました。current_idの間違い、モータの接続間違いがないか確認してください。"
                )
                return

    time.sleep(0.5)
    print()
    print("変更したidでpingを試します。")

    # Try to ping the SCServo
    # Get SCServo model number
    for i in range(0, 3):
        scs_model_number, scs_comm_result, scs_error = packetHandler.ping(
            portHandler, args.changed_id
        )
        if scs_comm_result != COMM_SUCCESS:
            if i == 2:
                print("[ERROR] %s" % packetHandler.getTxRxResult(scs_comm_result))
                print("------------------------")
                print("pingに失敗しました")
                print("------------------------")
                break
            continue
        elif scs_error != 0:
            if i == 2:
                print("[ERROR] %s" % packetHandler.getRxPacketError(scs_error))
                print("------------------------")
                print("pingに失敗しました")
                print("------------------------")
                break
            continue
        else:
            print(
                "Pingに成功しました。 [ID:%03d]. モータモデル : %d"
                % (args.changed_id, scs_model_number)
            )
            # EEPROM ROCK
            scs_comm_result, scs_error = packetHandler.write1ByteTxRx(
                portHandler, args.changed_id, 55, 1
            )
            if scs_comm_result == COMM_SUCCESS:
                print(f"EEPROMロックしました。")
            else:
                print(f"[ERROR] EPROMロックに失敗しました。")
                return
            print("------------------------")
            print("idの変更OK!")
            print("------------------------")
            break

    # Close port
    portHandler.closePort()


if __name__ == "__main__":
    main()
