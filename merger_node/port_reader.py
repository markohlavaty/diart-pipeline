import socket
import select


class PortReader:
    def __init__(self, port):
        self.port = port
        self.buffer = ""
        self.server = None
        self.conn = None

    def open(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(('localhost', self.port))
        self.server.listen()
        self.conn, _ = self.server.accept()

    def close(self):
        if self.conn:
            self.conn.close()
        if self.server:
            self.server.close()

    def has_data(self):  # returns False if the client has disconnected or is waiting to send more data after the time has run out
        """Wait up to `timeout` seconds for data on the socket.
        Returns True if actual data is available, False if timed out or disconnected.
        """
        readable, _, _ = select.select([self.conn], [], [], 0)
        if readable:
            # Use MSG_PEEK to look at the data without removing it from the buffer
            data = self.conn.recv(1, socket.MSG_PEEK)
            if data:
                return True  # Real data is available
            else:
                return False  # Connection is closed (recv returned b'')
        return False  # Timed out waiting for data

    def read_line(self):  # returns '' in case of empty line, None if the stream has ended
        line = bytearray()

        char = self.conn.recv(1)  # blocking read, one byte
        while char != b'\n':
            if not char:  # connection closed
                if line:
                    return line.decode('utf8')  # return remaining characters
                else:
                    return None  # signal end of stream
            line += char
            char = self.conn.recv(1)
        return line.decode('utf8')
