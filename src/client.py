#!/usr/bin/python3

import os
import pickle
import signal
import select
import socket
import time
from threading import Thread

from typing import Any, List, Optional, Tuple

from src.models.packet import Packet, PacketType


NetworkAddress: Tuple[str, int] = Any


class ClientTimeout(Thread):
    """
    Class controlling Client timeout from a server connection.
    """

    def __init__(self, timeout):
        Thread.__init__(self)
        self.timeout = timeout
        self.seconds = 0

    def reset(self):
        self.seconds = 0

    def run(self):
        while self.seconds <= self.timeout:
            time.sleep(1)
            self.seconds += 1

        print('[CLIENT] Connection timed out.')

        os.kill(os.getpid(), signal.SIGINT)

    def terminate(self):
        self.seconds = 0
        os.kill(os.getpid(), signal.SIGINT)


class Client(object):

    def __init__(
            self,
            host: str,
            port: int,
            timeout: int,
            retry_attempts: int,
            threshold: int,
            filename: str
    ) -> None:
        self.HOST: str = host
        self.PORT: int = port
        self.ADDR: Tuple[str, int] = (self.HOST, self.PORT)

        self.TIMEOUT: ClientTimeout = ClientTimeout(timeout)

        self.retry_attempts: int = retry_attempts
        self.threshold: int = threshold
        self.cnwd: int = 2048

        self.is_active: bool = False
        self.conn_id: int = 0
        self.filename: str = f'data/{filename}_{int(time.time())}.txt'

        self.CLIENT: socket.socket = self.init_udp_socket()

        self.TIMEOUT.start()
        self.start()


    @staticmethod
    def init_udp_socket() -> Optional[socket.socket]:
        """
        Create UDP socket and bind it to address.
        """
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setblocking(True)

        return udp_socket


    def close_connection(self) -> None:
        self.is_active = False

        fin_ack_packet = Packet(PacketType(5), 0, 0, 0, b'0')

        print(f'[CLIENT] Sending FIN-ACK packet to server.')

        self.CLIENT.sendto(fin_ack_packet.to_bytes(), self.ADDR)

        self.CLIENT.close()
        self.TIMEOUT.terminate()

        print('[CLIENT] Connection closed.')

        os.kill(os.getpid(), signal.SIGINT)


    def receive_data(self, packet_recv: Packet):
        """
        Receives data from server
            - Received data from server, write it to a file.
            - Control congestion window.
            - Send an ack back to the server.
        """
        if packet_recv.connection_id == self.conn_id:

            with open(self.filename, 'a') as f:
                f.write(packet_recv.payload.decode())

            if self.cnwd <= self.threshold:
                self.cnwd += 1
            else:
                self.cnwd = int(self.cnwd / 2)

            print(self.cnwd)
            ack_packet = Packet(PacketType(3), self.conn_id, 0, self.cnwd)

            self.CLIENT.sendto(ack_packet.to_bytes(), self.ADDR)


    def send_ack_syn(self, packet_recv: Packet) -> None:
        """
        Send back acknowledgement from packets received from server.
            - If it`s first time here, set connection id.
            - Controls packet size received from server through congestion window.
        """
        if self.conn_id == 0:
            self.conn_id = packet_recv.connection_id

        ack_packet = Packet(PacketType(3), self.conn_id, 0, self.cnwd)

        print(f'[CLIENT] Sending ACK synchronization packet to server.')

        self.CLIENT.sendto(ack_packet.to_bytes(), self.ADDR)


    def handle_recv_packet(self, recv_data, recv_addr) -> None:
        """
        Reset client timeout whenever a packet is received.
        Handles received packet from server.
        """
        self.TIMEOUT.reset()

        packet_recv: Optional[Packet] = pickle.loads(recv_data)

        if not isinstance(packet_recv, Packet) or not packet_recv.check_size() or recv_addr != self.ADDR:
            print(f'[SERVER] Dropping packet from {recv_addr}.')

        elif packet_recv.packet_type is PacketType.SYN_ACK:
            self.send_ack_syn(packet_recv)

        elif packet_recv.packet_type is PacketType.DATA:
            self.receive_data(packet_recv)

        elif packet_recv.packet_type is PacketType.FIN:
            self.close_connection()


    def start_recv_state(self):
        """
        Client enters on a receiving state.
            - Receives packet from server
            - Send Ack with congestion window
        """
        while True:
            (recv_data, recv_addr) = self.CLIENT.recvfrom(self.threshold * 2)
            if recv_data:
                self.TIMEOUT.reset()
                self.handle_recv_packet(recv_data, recv_addr)


    def send_syn(self) -> None:
        """
        Send SYN packet to server.
        """
        self.is_active = True

        syn_packet = Packet(PacketType(0), self.conn_id, 0, 0)

        print(f'[CLIENT] Sending SYN packet to server.')

        self.CLIENT.sendto(syn_packet.to_bytes(), self.ADDR)


    def start(self) -> None:
        """
        Tries to establish a connection to a server to request file by these steps.
            - Initial Handshake and Ack`s
            - Start requesting and acknowledging packets from server
            - Start congestion control protocol: cnwd and threshold
        """
        for i in range(self.retry_attempts):

            try:
                input_socket = [self.CLIENT]
                inputready, outputready, exceptready = select.select(input_socket, [], [], 1)

                if inputready is []:
                    continue
                else:
                    if not self.is_active:
                        self.send_syn()

                    self.start_recv_state()

                    self.close_connection()

            except ValueError:
                print('[CLIENT] Connection closed.')
                break
            except Exception as e:
                print(f'[CLIENT] Connection closed due to an exception: {e}')
                break
