from port_reader import PortReader
from collections import deque
import time


class DiarizationMerger:

    def __init__(self, transcription_port, diarization_port, diarization_buffer_size, maximum_diarization_delay):
        self._transcription_reader = PortReader(transcription_port)
        self._diarization_reader = PortReader(diarization_port)
        self._diarization_buffer = deque(maxlen=diarization_buffer_size)
        self._maximum_diarization_delay = maximum_diarization_delay

    @staticmethod
    def _get_word_information(word_line):

        parts = word_line.strip().split(' ', maxsplit=2)
        
        word = parts[2]
        word_start = int(parts[0]) / 1000
        word_end = int(parts[1]) / 1000

        if word_end < word_start:
            raise ValueError('The start of a word must come before its end.')
        return word, word_start, word_end

    @staticmethod
    def _get_speaker_information(rttm_line):
        parts = rttm_line.strip().split()
    
        if len(parts) != 10 or parts[0] != 'SPEAKER':
            raise ValueError('Invalid RTTM line format.')

        speaker = parts[7]
        speaker_start = float(parts[3])
        duration = float(parts[4])
        speaker_end = speaker_start + duration
        
        if speaker_end < speaker_start:
            raise ValueError('The start of a speaker turn must come before its end.')
        
        return speaker, speaker_start, speaker_end


    
    def _output_diarization(self, speaker, word):
        print(f'{speaker}\t{word}')

    def _load_new_word_lines(self):
        first_word_line = self._transcription_reader.read_line()  # wait and block until at least one word arrives
        if first_word_line is None:  # the client has disconnected
            return None  # signal end of stream
        word_lines = [first_word_line]
        while self._transcription_reader.has_data():
            word_lines.append(
                self._transcription_reader.read_line()
            )
        return word_lines

    def _update_diarization_buffer(self):
        while self._diarization_reader.has_data():
            self._diarization_buffer.append(
                self._diarization_reader.read_line()
            )
    
    def _find_speaker(self, word_start, word_end):
        overlaps = {}
        closest_speaker = 'unknown_speaker'
        closest_speaker_distance = float('inf')

        for speaker_line in self._diarization_buffer:
            speaker, speaker_start, speaker_end = self._get_speaker_information(speaker_line)

            if speaker_end < word_start:
                speaker_distance = word_start - speaker_end
                if speaker_distance < closest_speaker_distance:
                    closest_speaker = speaker
                    closest_speaker_distance = speaker_distance
            elif word_end < speaker_start:
                speaker_distance = speaker_start - word_end
                if speaker_distance < closest_speaker_distance:
                    closest_speaker = speaker
                    closest_speaker_distance = speaker_distance
            else:  # word and speaker overlap
                overlap_start = max(word_start, speaker_start)
                overlap_end = min(word_end, speaker_end)
                if speaker not in overlaps:
                    overlaps[speaker] = 0
                overlaps[speaker] += overlap_end - overlap_start
        if overlaps:
            # return speaker with the biggest overlap
            return max(overlaps, key=overlaps.get)
        else:
            return closest_speaker
    
    def start_merging(self):
        self._transcription_reader.open()
        self._diarization_reader.open()
        
        while True:
            print(True)
            # load all new words
            word_lines = self._load_new_word_lines()
            print(word_lines)
            if word_lines is None:  # end of stream
                break

            # wait for diarization to catch up and load new speaker turns
            time.sleep(self._maximum_diarization_delay)
            self._update_diarization_buffer()

            # attribute each word to a speaker
            for word_line in word_lines:
                word, word_start, word_end = self._get_word_information(word_line)
                speaker = self._find_speaker(word_start, word_end)
                self._output_diarization(speaker, word)
                
        self._transcription_reader.close()
        self._diarization_reader.close()
