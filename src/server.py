#!/usr/bin/python3

import sys
import socket
import pickle
from random import getrandbits
from threading import Thread

from typing import Any, Optional, Tuple, BinaryIO

from src.models.packet import Packet, PacketType


NetworkAddress: Tuple[str, int] = Any


class ClientHandle(Thread):
    pass


class Server(object):


    def __init__(
            self,
            port: int,
            buffer: int,
            filename: str
    ) -> None:
        self.HOST = self.get_host()
        self.PORT = port
        self.ADDR = (self.HOST, self.PORT)
        self.BUFFER = buffer
        self.SERVER = self.init_udp_socket()

        self.conn_id: int = 0

        self.filename = f'data/{filename}.txt'
        self.offset: int = 0

        self.start()


    @staticmethod
    def get_host() -> Optional[str]:
        return socket.gethostbyname(socket.gethostname())


    def recv_invalid_request(self, recv_addr) -> None:
        print(f'[SERVER] Received invalid request from {recv_addr[0]} on port {recv_addr[1]}. Dropped Packet. Connection ID: {self.conn_id}')


    def init_udp_socket(self) -> Optional[socket.socket]:
        """
        Create UDP socket and bind it to address.
        """
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.bind(self.ADDR)
        udp_socket.setblocking(True)

        return udp_socket


    def close_connection(self):
        """
        Close connection to a client. Reset parameters for accepting other connections.
        """
        self.conn_id: int = 0
        self.offset: int = 0


    def send_fin(self, recv_addr: NetworkAddress):
        """
        Send FIN packet to a client.
        """
        fin_packet: Packet = Packet(PacketType(4), self.conn_id, 0, 0)

        print(f'[SERVER] Sending FIN packet to client. Connection ID: {self.conn_id}')

        self.SERVER.sendto(fin_packet.to_bytes(), recv_addr)


    def send_data(self, packet_recv: Packet, recv_addr: NetworkAddress):
        """
        Sends DATA packet of a file to a client
            - Verifies the client connection id.
            - Defines the buffer of the data to be sent by subtracting the cnwd - packet_header.
            - Reads the buffer size of the file from the offset.
            - Load packet with data.
            - Send packet to client.
            - If file is over, send a FIN packet to client.
        """
        if packet_recv.connection_id == self.conn_id:

            client_cnwd: int = packet_recv.window

            data_packet: Packet = Packet(PacketType(2), self.conn_id, 0, 0)

            buffer: int = client_cnwd - sys.getsizeof(data_packet)

            try:
                f: BinaryIO = open(self.filename, "rb")
                f.seek(self.offset)
            except Exception as e:
                print(f'[SERVER] Error opening file: {e}. Sending big_transfer file. Connection ID: {self.conn_id}')
                self.filename = 'data/big_transfer.txt'
                f: BinaryIO = open(self.filename, "rb")
                f.seek(self.offset)

            data: bytes = f.read(buffer)
            if not data:
                f.close()
                self.send_fin(recv_addr)
                return

            data_packet.load(data)
            self.offset: int = f.tell()
            f.close()

            self.SERVER.sendto(data_packet.to_bytes(), recv_addr)


    def send_syn_ack(self, recv_addr: NetworkAddress):
        """
        Sends a handshake packet to a client for establishing a connection.
            - Generate a connection id for client.
            - Create a syn-ack packet.
            - Add that connection id to the list of unverified connection.
        """
        self.conn_id = getrandbits(62)

        syn_ack_packet = Packet(PacketType(1), self.conn_id, 0, 0, b'0')

        print(f'[SERVER] Sending SYN-ACK packet to client. Connection ID: {self.conn_id}')

        self.SERVER.sendto(syn_ack_packet.to_bytes(), recv_addr)


    def handle_recv_packet(self, recv_data, recv_addr) -> None:
        """
        Handles received packet from client.
        """
        packet_recv: Optional[Packet] = pickle.loads(recv_data)

        if not isinstance(packet_recv, Packet) or not packet_recv.check_size():
            print(f'[SERVER] Dropping packet from {recv_addr}.')

        elif packet_recv.packet_type is PacketType.SYN:
            self.send_syn_ack(recv_addr)

        elif packet_recv.packet_type is PacketType.ACK:
            self.send_data(packet_recv, recv_addr)

        elif packet_recv.packet_type is PacketType.FIN_ACK:
            self.close_connection()


    def start_recv_state(self):
        """
        Server starts receiving connections.
            - Receives packet from client
            - Handle packet
        """
        while True:
            (recv_data, recv_addr) = self.SERVER.recvfrom(self.BUFFER)
            if recv_data:
                self.handle_recv_packet(recv_data, recv_addr)

            else:
                self.recv_invalid_request(recv_addr)
                recv_data, recv_addr = None, None


    def start(self) -> None:
        """
        Start server on local IP and defined Port. Start receiving state.
        """
        print(f'[SERVER] Server is listening on {self.HOST}:{self.PORT}')
        self.start_recv_state()
