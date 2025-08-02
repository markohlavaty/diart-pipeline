import argparse
from diart import SpeakerDiarization
from diart.inference import StreamingInference

from custom_observers import StdoutWriter
from custom_sources import TCPAudioSource


def main(sample_rate: int, chunk_duration: float, host: str, port: int) -> None:
    """
    Main entry point for setting up and running speaker diarization
    on audio streamed over a TCP connection.

    Args:
        sample_rate (int): Sample rate of the incoming audio stream in Hz.
        chunk_duration (float): Duration (in seconds) of each buffered audio chunk.
        host (str): Host/IP address to listen on for the TCP stream.
        port (int): Port number to bind the TCP listener.
    """
    # Initialize the speaker diarization pipeline
    pipeline = SpeakerDiarization()

    # Create the custom TCP audio source
    recorder = TCPAudioSource(
        sample_rate,
        chunk_duration,
        host,
        port
    )

    # Set up streaming inference with the pipeline and audio source
    inference = StreamingInference(pipeline, recorder)

    # Attach observer to output results in RTTM format to stdout
    inference.attach_observers(StdoutWriter(recorder.uri))

    # Start the streaming inference, discard the returned prediction because it will be streamed
    _ = inference()


if __name__ == '__main__':
    # Argument parser to handle CLI arguments
    parser = argparse.ArgumentParser(
        description='Run speaker diarization over a TCP audio stream.'
    )

    parser.add_argument(
        '--sample-rate',
        type=int,
        required=True,
        help='Sample rate of the audio stream (e.g., 16000)'
    )
    parser.add_argument(
        '--chunk-duration',
        type=float,
        required=True,
        help='Duration of each buffered audio chunk in seconds (e.g., 0.1)'
    )
    parser.add_argument(
        '--host',
        type=str,
        required=True,
        help='Host address that DIART listens to for incoming audio'
    )
    parser.add_argument(
        '--port',
        type=int,
        required=True,
        help='Port number that DIART listens to for incoming audio'
    )

    # Parse CLI arguments and pass them to the main function
    args = parser.parse_args()
    main(args.sample_rate, args.chunk_duration, args.host, args.port)
