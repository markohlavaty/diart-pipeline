import argparse

from diarization_merger import DiarizationMerger


def main(transcription_port, diarization_port, diarization_buffer_size, maximum_diarization_delay):
    merger = DiarizationMerger(
        transcription_port,
        diarization_port,
        diarization_buffer_size,
        maximum_diarization_delay
    )
    merger.start_merging()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Merge transcription and diarization streams.')
    parser.add_argument('--transcription_port', type=int, required=True, help='Port for receiving transcription data.')
    parser.add_argument('--diarization_port', type=int, required=True, help='Port for receiving diarization data.')
    parser.add_argument('--diarization_buffer_size', type=int, required=True, help='Buffer size for diarization stream.')
    parser.add_argument('--maximum_diarization_delay', type=float, required=True, help='Maximum delay to wait for diarization in seconds.')

    args = parser.parse_args()
    main(
        args.transcription_port,
        args.diarization_port,
        args.diarization_buffer_size,
        args.maximum_diarization_delay
    )
