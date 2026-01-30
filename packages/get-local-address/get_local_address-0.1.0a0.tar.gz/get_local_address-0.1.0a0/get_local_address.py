# Copyright (c) 2025 Jifeng Wu
# Licensed under the MIT License. See LICENSE file in the project root for full license information.
import socket

DEFAULT_ADDRESS = '1.1.1.1'
DEFAULT_PORT = 53


def get_local_address(
        target_address,  # type: str
        target_port,  # type: int
):
    # type: (...) -> str
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # connect() doesn't send data, but sets destination for send and fills in local address
    sock.connect((target_address, target_port))
    local_address, _ = sock.getsockname()
    return local_address


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Get the local IP address used to reach a remote host (UDP).')
    parser.add_argument(
        '-a',
        '--address',
        default=DEFAULT_ADDRESS,
        help='Target address (default: %s)' % (DEFAULT_ADDRESS,)
    )
    parser.add_argument(
        '-p',
        '--port',
        type=int,
        default=DEFAULT_PORT,
        help='Target port (default: %d)' % (DEFAULT_PORT,)
    )
    args = parser.parse_args()

    print(get_local_address(args.address, args.port))
