import socket
import select


class PortReader:
    """
    A simple TCP socket-based line reader that listens on a specified port
    and reads incoming text line by line from a connected client.

    This class is useful for scenarios where line-delimited text is streamed
    over a network connection and needs to be processed one line at a time.

    Attributes:
        _port (int): The TCP port to bind and listen for incoming connections.
        _buffer (str): A buffer to hold partial data (currently unused but present for extensibility).
        _server (socket.socket): The server socket used to accept connections.
        _conn (socket.socket): The connected client socket used for reading data.
    """

    def __init__(self, port: int) -> None:
        """
        Initialize a PortReader instance.

        Args:
            port (int): The port number to listen on.
        """
        self._port = port
        self._buffer = ""
        self._server = None
        self._conn = None

    def open(self) -> None:
        """
        Open the server socket, bind it to localhost and the specified port,
        and wait for a single incoming connection.
        """
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.bind(('localhost', self._port))
        self._server.listen()
        self._conn, _ = self._server.accept()

    def close(self) -> None:
        """
        Close the client and server sockets if they are open.
        """
        if self._conn:
            self._conn.close()
        if self._server:
            self._server.close()

    def has_data(self) -> bool:
        """
        Check if the client has sent any data, without removing it from the buffer.

        Returns:
            bool: True if data is available to read, False if the connection
                  is closed or no data is present.
        """
        readable, _, _ = select.select([self._conn], [], [], 0)
        if readable:
            # Use MSG_PEEK to look at the data without removing it from the buffer
            data = self._conn.recv(1, socket.MSG_PEEK)
            if data:
                return True  # Data is available
            else:
                return False  # Connection is closed (recv returned b'')
        return False  # No data available

    def read_line(self) -> str:
        """
        Read a single line (ending with a newline character) from the client.

        This is a blocking call that reads one byte at a time until a newline
        is encountered. If the client disconnects before a newline is received,
        any accumulated data will be returned. If no data is received at all,
        returns None to indicate end of stream.

        Returns:
            str: The decoded line without the newline character,
                 an empty string if the line was empty, or
                 None if the connection was closed and no data was read.
        """
        line = bytearray()

        char = self._conn.recv(1)  # blocking read, one byte
        while char != b'\n':
            if not char:  # connection closed
                if line:
                    return line.decode('utf8')  # return remaining characters
                else:
                    return None  # signal end of stream
            line += char
            char = self._conn.recv(1)
        return line.decode('utf8')
