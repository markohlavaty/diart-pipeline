import socket
import numpy as np
from diart.sources import AudioSource
import sys


class TCPAudioSourceError(Exception):
    """Raised when TCPAudioSource fails to initialize."""
    pass


# test:     ffmpeg -f dshow -i audio="Microphone Array (Technológia Intel® Smart Sound)" -acodec pcm_s16le -ac 1 -ar 16000 -f s16le tcp://localhost:7007
class TCPAudioSource(AudioSource):
    def __init__(self, sample_rate, chunk_duration, host, port):
        uri = 'tcp_audio'
        dtype=np.int16
        super().__init__(uri, sample_rate)
        self.dtype = dtype
        self.chunk_size = int(sample_rate * chunk_duration)
        self.bytes_per_sample = np.dtype(dtype).itemsize
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.server.bind((host, port))
            self.server.listen()
        except socket.error as e:
            raise TCPAudioSourceError(f'Socket error during TCPAudioSource initialization: {e}') from e

    def read(self):
        try:
            conn, addr = self.server.accept()
            with conn:
                while True:
                    chunk = conn.recv(self.chunk_size * self.bytes_per_sample)
                    if not chunk:
                        break
                    array = np.frombuffer(chunk, dtype=self.dtype).astype(np.float32).reshape(1, -1) #/ 32768
                    self.stream.on_next(array)
        except Exception as e:
            self.stream.on_error(e)
        finally:
            self.stream.on_completed()
            self.close()

    def close(self):
        self.server.close()


class StdinAudioSource(AudioSource):
    def __init__(self, uri='stdin_audio', sample_rate=16000, dtype=np.int16, chunk_duration=0.5):
        super().__init__(uri, sample_rate)
        self.dtype = dtype
        self.chunk_size = int(sample_rate * chunk_duration)
        self.bytes_per_sample = np.dtype(dtype).itemsize

    def read(self):
        try:
            while True:
                chunk = sys.stdin.buffer.read(self.chunk_size * self.bytes_per_sample)
                if not chunk:
                    break
                array = np.frombuffer(chunk, dtype=self.dtype).astype(np.float32).reshape(1, -1) #/ 32768
                self.stream.on_next(array)
        except Exception as e:
            self.stream.on_error(e)
        finally:
            self.stream.on_completed()
            self.close()

    def close(self):
        pass
