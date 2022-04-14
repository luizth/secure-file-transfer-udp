#!/usr/bin/python3

import argparse
import sys

from src.client import Client


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Client Args")

    try:
        parser.add_argument(
            "--host", type=str, default="localhost", help="Server's host name or IP address."
        )
        parser.add_argument(
            "--port", type=int, default=5050, help="Server's port number."
        )
        parser.add_argument(
            "--timeout", type=int, default=10, help="Client's timeout from receiving packets."
        )
        parser.add_argument(
            "--retry", type=int, default=5, help="Client's initial handshake retries."
        )
        parser.add_argument(
            "--threshold", type=int, default=32768, help="Client's threshold for congestion control."
        )
        parser.add_argument(
            "--filename", type=str, default='copy', help="Name of the file downloaded from server."
        )
    except Exception as e:
        print(f'[CLIENT] Error receiving args: {e}')
        sys.exit()

    args = parser.parse_args()
    client = Client(args.host, args.port, args.timeout, args.retry, args.threshold, args.filename)
