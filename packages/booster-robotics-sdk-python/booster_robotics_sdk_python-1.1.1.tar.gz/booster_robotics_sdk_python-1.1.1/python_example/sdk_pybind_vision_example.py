#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time

# 假设编译出的 .so 名字是 _core，在 python 中作为 booster_robotics_sdk_python 导入
import booster_robotics_sdk_python as br


def print_help():
    print(
        """
Available commands (Vision Service):
  help                              - Show this help
  start <pos> <color> <face>        - Start service (bools: 1/0 or true/false). 
                                      Example: start 1 0 1 (Enable Pos & Face, Disable Color)
  stop                              - Stop Vision Service
  detect                            - Get Detection Objects (Center 30% area)
  quit / exit                       - Exit
"""
    )


def parse_bool(s):
    return s.lower() in ["true", "1", "yes", "on"]


def main():
    net_if = "" 
    robot_name = None

    if len(sys.argv) > 1:
        net_if = sys.argv[1]

    if len(sys.argv) > 2:
        robot_name = sys.argv[2]

    if not net_if:
        print("Network interface not specified.")
    else:
        print(f"Initializing ChannelFactory on {net_if}...")

    br.ChannelFactory.Instance().Init(0, net_if)

    # 2. 初始化 VisionClient
    vision_client = br.VisionClient()
    if robot_name:
        print(f"Initializing VisionClient for robot: {robot_name}...")
        vision_client.InitWithName(robot_name)
    else:
        print("Initializing VisionClient with default name...")
        vision_client.Init()

    print("Vision Service CLI started.")
    print_help()

    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExit.")
            break

        if not line:
            continue

        parts = line.split()
        cmd = parts[0].lower()
        args = parts[1:]

        try:
            # ---------- Help ----------
            if cmd in ("help", "?"):
                print_help()

            # ---------- Start Service ----------
            elif cmd == "start":
                if len(args) != 3:
                    print("Usage: start <enable_pos> <enable_color> <enable_face>")
                    print("Example: start 1 0 1")
                    continue
                
                pos = parse_bool(args[0])
                color = parse_bool(args[1])
                face = parse_bool(args[2])

                # 调用 C++ 绑定的 StartVisionService
                vision_client.StartVisionService(pos, color, face)
                print(f"[OK] StartVisionService sent: Pos={pos}, Color={color}, Face={face}")

            # ---------- Stop Service ----------
            elif cmd == "stop":
                vision_client.StopVisionService()
                print("[OK] StopVisionService sent.")

            # ---------- Get Detection Objects ----------
            elif cmd == "detect":
                print("Requesting detection results...")
                # 调用绑定的 GetDetectionObject，它会返回一个 list
                results = vision_client.GetDetectionObject()
                
                if not results:
                    print("[INFO] No objects detected.")
                else:
                    print(f"[OK] Detected {len(results)} objects:")
                    for i, obj in enumerate(results):
                        print(f"  Object #{i + 1}:")
                        print(f"    Tag: {obj.tag}")
                        print(f"    Conf: {obj.conf:.2f}")
                        print(f"    BBox: ({obj.xmin}, {obj.ymin}) - ({obj.xmax}, {obj.ymax})")
                        if obj.position:
                            print(f"    Position 3D: {obj.position}")
                        if obj.rgb_mean:
                            print(f"    RGB Mean: {obj.rgb_mean}")
                        print("-" * 20)

            # ---------- Exit ----------
            elif cmd in ("quit", "exit"):
                print("Bye.")
                break

            else:
                print(f"Unknown command: {cmd}")
                print("Type 'help' to show available commands.")

        except Exception as e:
            # 捕获 C++ 抛出的异常 (std::runtime_error)
            print(f"[ERROR] Request failed: {e}")


if __name__ == "__main__":
    main()