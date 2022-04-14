#!/usr/bin/python3

import argparse
import sys

from src.server import Server


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Server Args")

    try:
        parser.add_argument(
            "--port", type=int, default=5050, help="Server's port number to bind."
        )
        parser.add_argument(
            "--buffer", type=int, default=65536, help="Server's buffer size."
        )
        parser.add_argument(
            "--filename", type=str, default='big_transfer', help="Server's file to transfer."
        )
    except Exception as e:
        print(f'[Server] Error receiving args: {e}')
        sys.exit()

    args = parser.parse_args()
    server = Server(args.port, args.buffer, args.filename)
