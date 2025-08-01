import argparse
from diarization_merger import DiarizationMerger


def main(transcription_port: int, diarization_port: int, diarization_buffer_size: int, maximum_diarization_delay: float) -> None:
    """
    Main entry point for merging transcription and diarization data streams.

    Args:
        transcription_port (int): Port number for receiving transcription data.
        diarization_port (int): Port number for receiving diarization data.
        diarization_buffer_size (int): Number of items to buffer for the diarization stream.
        maximum_diarization_delay (float): Maximum delay (in seconds) to wait for diarization
                                           before proceeding with merging.
    """
    # Initialize and run the merger
    merger = DiarizationMerger(
        transcription_port,
        diarization_port,
        diarization_buffer_size,
        maximum_diarization_delay
    )
    merger.start_merging()


if __name__ == '__main__':
    # Create argument parser for command-line use
    parser = argparse.ArgumentParser(
        description='Merge transcription and diarization streams.'
    )

    parser.add_argument(
        '--transcription_port',
        type=int,
        required=True,
        help='Port for receiving transcription data.'
    )

    parser.add_argument(
        '--diarization_port',
        type=int,
        required=True,
        help='Port for receiving diarization data.'
    )

    parser.add_argument(
        '--diarization_buffer_size',
        type=int,
        required=True,
        help='Buffer size for diarization stream (number of utterances).'
    )

    parser.add_argument(
        '--maximum_diarization_delay',
        type=float,
        required=True,
        help='Maximum delay (in seconds) to wait for diarization results.'
    )

    # Parse CLI arguments and invoke main function
    args = parser.parse_args()
    main(
        args.transcription_port,
        args.diarization_port,
        args.diarization_buffer_size,
        args.maximum_diarization_delay
    )
