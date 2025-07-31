import socket
import numpy as np
from diart.sources import AudioSource
import sys


class TCPAudioSourceError(Exception):
    """Raised when TCPAudioSource fails to initialize."""
    pass


class TCPAudioSource(AudioSource):
    """
    A custom audio source that receives audio data streamed through a TCP connection.

    This class is designed to accept a single incoming connection and stream audio
    data in real time, chunked based on the specified duration.

    Attributes:
        chunk_size (int): Number of samples per audio chunk.
        dtype (np.dtype): Data type of incoming audio samples (set to np.int16).
        bytes_per_sample (int): Size in bytes of one audio sample.
        host (str): Host/IP address to bind the TCP server.
        port (int): Port number to bind the TCP server.
        server (socket.socket): TCP server socket.
    """

    def __init__(self, sample_rate: int, chunk_duration: float, host: str, port:int) -> None:
        """
        Initialize the TCPAudioSource.

        Args:
            sample_rate (int): Audio sample rate in Hz.
            chunk_duration (float): Duration of each chunk in seconds.
            host (str): Hostname or IP address to bind the server socket.
            port (int): Port number to bind the server socket.
        """
        super().__init__(uri='tcp_audio', sample_rate=sample_rate)  # uri is a unique identifier of the audio source
        self.chunk_size = int(sample_rate * chunk_duration)
        self.dtype = np.int16
        self.bytes_per_sample = np.dtype(self.dtype).itemsize
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
    def _connect(self) -> socket.socket:
        """
        Bind and accept a single incoming TCP connection.

        Returns:
            socket.socket: Connected client socket.

        Raises:
            TCPAudioSourceError: If an error occurs during socket setup or connection.
        """
        try:
            self.server.bind((self.host, self.port))
            self.server.listen()
            conn, _ = self.server.accept()
        except socket.error as e:
            raise TCPAudioSourceError(f'Socket error during TCPAudioSource initialization: {e}') from e
        return conn

    def read(self) -> None:
        """
        Start reading audio data from the TCP connection and stream it chunk by chunk.

        Converts the byte stream into a NumPy array of shape (1, N) with dtype float32.
        Emits each array to the stream's observer.
        """
        try:
            conn = self._connect()
            with conn:
                while True:
                    chunk = conn.recv(self.chunk_size * self.bytes_per_sample)
                    if not chunk:
                        break
                    array = np.frombuffer(chunk, dtype=self.dtype).astype(np.float32).reshape(1, -1)
                    self.stream.on_next(array)
        except Exception as e:
            self.stream.on_error(e)
        finally:
            self.stream.on_completed()
            self.close()

    def close(self):
        """Close the TCP server socket."""
        self.server.close()


class StdinAudioSource(AudioSource):
    """
    A custom audio source that reads audio data from standard input (stdin).

    This is useful for piping raw audio data into the application, such as via
    `ffmpeg` or similar tools.

    Attributes:
        dtype (np.dtype): Data type of incoming audio samples (default: np.int16).
        chunk_size (int): Number of samples per audio chunk.
        bytes_per_sample (int): Size in bytes of one audio sample.
    """
    
    def __init__(self, sample_rate: int, chunk_duration: float) -> None:
        """
        Initialize the StdinAudioSource.

        Args:
            sample_rate (int): Audio sample rate in Hz.
            chunk_duration (float): Duration of each chunk in seconds.
        """
        super().__init__(uri='stdin_audio', sample_rate=sample_rate)
        self.dtype = np.int16
        self.chunk_size = int(sample_rate * chunk_duration)
        self.bytes_per_sample = np.dtype(self.dtype).itemsize

    def read(self) -> None:
        """
        Start reading audio data from stdin and stream it chunk by chunk.

        Converts the byte stream into a NumPy array of shape (1, N) with dtype float32.
        Emits each array to the stream's observer.
        """
        try:
            while True:
                chunk = sys.stdin.buffer.read(self.chunk_size * self.bytes_per_sample)
                if not chunk:
                    break
                array = np.frombuffer(chunk, dtype=self.dtype).astype(np.float32).reshape(1, -1)
                self.stream.on_next(array)
        except Exception as e:
            self.stream.on_error(e)
        finally:
            self.stream.on_completed()
            self.close()

    def close(self) -> None:
        """
        Close the source. Included for compatibility.

        Since stdin does not require cleanup, this is a no-op.
        """
        pass
