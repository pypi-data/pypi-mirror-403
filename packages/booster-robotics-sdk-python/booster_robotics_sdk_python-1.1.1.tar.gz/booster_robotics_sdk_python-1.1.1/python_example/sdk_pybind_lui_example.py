#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time

import booster_robotics_sdk_python as br


def print_help():
    print(
        """
Available commands (AI control):
  help                  - Show this help
  start_asr             - Start ASR Service
  stop_asr              - Stop ASR Service
  start_tts             - Start TTS Service
  stop_tts              - Stop TTS Service
  send_tts_text         - Send TTS text
  quit / exit           - Exit
"""
    )


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} networkInterface [robotName]")
        sys.exit(-1)

    net_if = sys.argv[1]
    robot_name = sys.argv[2] if len(sys.argv) > 2 else None

    br.ChannelFactory.Instance().Init(0, net_if)

    lui = br.LuiClient()
    if robot_name:
        lui.InitWithName(robot_name)
    else:
        lui.Init()

    print("LUI CLI started.")
    print_help()

    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExit.")
            break

        if not line:
            continue

        parts = line.split(maxsplit=1)
        cmd = parts[0]
        arg = parts[1] if len(parts) > 1 else ""

        try:
            # ---------- Help ----------
            if cmd in ("help", "?"):
                print_help()

            # ---------- Start / stop AI Chat ----------
            elif cmd == "start_asr":
                lui.StartAsr()
                print("[OK] StartAsr sent.")

            elif cmd == "stop_asr":
                lui.StopAsr()
                print("[OK] StopAsr sent.")

            elif cmd == "start_tts":
                tts_conf = br.LuiTtsConfig("zh_female_vv_uranus_bigtts")
                lui.StartTts(tts_conf)
                print("[OK] StartTts sent.")

            elif cmd == "stop_tts":
                lui.StopTts()
                print("[OK] StopTts sent.")
            
            elif cmd == "send_tts_text":
                if not arg:
                    print("Usage: send_tts_text <text>")
                    continue
                tts_param = br.LuiTtsParameter(arg)
                lui.SendTtsText(tts_param)
                print(f"[OK] SendTtsText sent: {arg}")
            # ---------- Exit ----------
            elif cmd in ("quit", "exit"):
                print("Bye.")
                break

            else:
                print(f"Unknown command: {cmd}")
                print("Type 'help' to show available commands.")

        except Exception as e:
            # Catch pybind-wrapped runtime_error when underlying API returns non-zero
            print(f"[ERROR] Request failed: {e}")


if __name__ == "__main__":
    main()
