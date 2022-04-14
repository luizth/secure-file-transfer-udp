#!/usr/bin/python3

import sys
import pickle
from enum import Enum
from typing import Optional


class PacketType(Enum):
    """
    Enum class describing packet types.
    """
    SYN = 0
    SYN_ACK = 1
    DATA = 2
    ACK = 3
    FIN = 4
    FIN_ACK = 5


class Packet:
    """
    General packet class, for exchanging data.
    """
    def __init__(
            self,
            packet_type: Optional[PacketType],
            connection_id: int,
            packet_number,
            window: int,
            payload: bytes = b'0'
    ) -> None:
        self.packet_type = packet_type
        self.connection_id = connection_id
        self.packet_number = packet_number
        self.window = window

        self.payload = payload
        self.length = self.payload_size()


    def load(self, payload) -> None:
        self.payload = payload
        self.length = self.payload_size()


    def payload_size(self) -> Optional[int]:
        return sys.getsizeof(self.payload)


    def to_bytes(self) -> Optional[bytes]:
        return pickle.dumps(self)


    def check_size(self) -> Optional[bool]:
        return sys.getsizeof(self.payload) == self.length


    def __str__(self) -> Optional[str]:
        return "packet_type: " + str(self.packet_type) + ", connection_id: " + str(self.connection_id) + \
               ", packet_number: " + str(self.packet_number) + ", ack_flag: " + str(self.ack_flag) + \
               ", window: " + str(self.window) + ", length: " + str(self.length) + ", payload: " + str(self.payload)
