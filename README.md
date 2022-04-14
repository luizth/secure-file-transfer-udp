## Description
Secure file transfer implementation over UDP protocol.
___

### Implemented Features:
- Multiple connections
- Client-Server handshake
- Network congestion control (cnwd)
- Client timeout control
___

#### Server args:

    --port --buffer --filename

- Server maps filename to './data' directory.

#### Client args:

    --host --port --timeout --retry --threshold --filename

- Client defines filename to save the file downloaded from server.
___

## Usage
Execute following commands on root folder:

    Server: 
        $ python3 server.py --port --buffer --filename
    Client:
        $ python3 client.py --host --port --timeout --retry --threshold --filename