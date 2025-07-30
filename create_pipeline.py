import sys
from pathlib import Path
from pipeliner_module.src.pipeliner import Pipeliner


def main():
    PROJECT_PATH = Path(sys.argv[0]).resolve().parent

    SIMULSTREAMING_MAIN_PATH = PROJECT_PATH / 'simulstreaming_node' / 'simulstreaming_whisper_server.py'
    DIART_MAIN_PATH = PROJECT_PATH / 'diart_node' / 'run_diart.py'
    MERGER_MAIN_PATH = PROJECT_PATH / 'merger_node' / 'merge_diarization.py'

    RECORDER_PORT = 8000
    SIMULSTREAMING_INPUT_PORT = 8001
    DIART_INPUT_PORT = 8002
    MERGER_TRANSCRIPTION_INPUT_PORT = 8003
    MERGER_DIARIZATION_INPUT_PORT = 8004
    REPORTER_PORT = 8008


    


    p = Pipeliner()
    recorder_node = p.addLocalNode('recorder', {}, {'audio': 'stdout'}, f'nc -lk {RECORDER_PORT}')
    whisper_node = p.addLocalNode('whisper', {'audio': f'{SIMULSTREAMING_INPUT_PORT}'}, {'timestamped_transcription': 'stdout'}, f'python3 {SIMULSTREAMING_MAIN_PATH} --host localhost --port {SIMULSTREAMING_INPUT_PORT} --min-chunk-size 1.0 --task transcribe --vac --vac-chunk-size 0.5')
    diart_node = p.addLocalNode('diart', {'audio': f'{DIART_INPUT_PORT}'}, {'speaker_timestamps': 'stdout'}, f'python3 {DIART_MAIN_PATH} --sample_rate 16000 --chunk_duration 0.1 --host localhost --port {DIART_INPUT_PORT}')
    merger_node = p.addLocalNode('diarization_merger', {'timestamped_transcription': f'{MERGER_TRANSCRIPTION_INPUT_PORT}', 'speaker_timestamps': f'{MERGER_DIARIZATION_INPUT_PORT}'}, {'merged_transcription': 'stdout'}, f'python3 {MERGER_MAIN_PATH} --transcription_port {MERGER_TRANSCRIPTION_INPUT_PORT} --diarization_port {MERGER_DIARIZATION_INPUT_PORT} --diarization_buffer_size 120 --maximum_diarization_delay 0.5')
    reporter_node = p.addLocalNode('reporter', {'merged_output': 'stdout'}, {}, f'nc localhost {REPORTER_PORT}')

    p.addSimpleEdge(recorder_node, whisper_node)
    p.addSimpleEdge(recorder_node, diart_node)
    p.addEdge(whisper_node, 'timestamped_transcription', merger_node, 'timestamped_transcription')
    p.addEdge(diart_node, 'speaker_timestamps', merger_node, 'speaker_timestamps')
    p.addSimpleEdge(merger_node, reporter_node)

    p.createPipeline()


if __name__ == '__main__':
    main()
