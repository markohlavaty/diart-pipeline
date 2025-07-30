import argparse
from diart import SpeakerDiarization
from diart.inference import StreamingInference

from custom_observers import StdoutWriter
from custom_sources import TCPAudioSource, StdinAudioSource


def main(sample_rate, chunk_duration, host, port):
    pipeline = SpeakerDiarization()
    recorder = TCPAudioSource(
        sample_rate,
        chunk_duration,
        host,
        port
    )
    inference = StreamingInference(pipeline, recorder)
    inference.attach_observers(StdoutWriter(recorder.uri))
    prediction = inference()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run speaker diarization over a TCP audio stream.')
    parser.add_argument('--sample_rate', type=int, required=True, help='Sample rate of the audio stream (e.g., 16000)')
    parser.add_argument('--chunk_duration', type=float, required=True, help='Duration of each buffered audio chunk in seconds (e.g., 0.1)')  # chunk_duration 0.1s worked fine
    parser.add_argument('--host', type=str, required=True, help='Host address that diart takes input from')
    parser.add_argument('--port', type=int, required=True, help='Port number that diart takes input from')

    args = parser.parse_args()
    main(args.sample_rate, args.chunk_duration, args.host, args.port)
