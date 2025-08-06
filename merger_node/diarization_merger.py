from port_reader import PortReader
from collections import deque
import time
from typing import Tuple
from concurrent.futures import ThreadPoolExecutor


class DiarizationMerger:
    """
    Merges transcription and diarization data from two streaming sources (ports). 
    Transcriptions contain words with timestamps, and diarization provides speaker 
    turns in RTTM format. The class aligns each word with its most likely speaker.

    Attributes:
        _transcription_reader (PortReader): Reader for the transcription stream.
        _diarization_reader (PortReader): Reader for the diarization stream.
        _diarization_buffer (deque): Buffer holding recent diarization lines.
        _maximum_diarization_delay (float): Time to wait to allow diarization to catch up.
    """

    def __init__(self, transcription_port: int, diarization_port: int, diarization_buffer_size: int, maximum_diarization_delay: float) -> None:
        """
        Initializes the DiarizationMerger with ports and buffer parameters.

        Args:
            transcription_port (int): Port number for transcription stream.
            diarization_port (int): Port number for diarization stream.
            diarization_buffer_size (int): Max number of speaker lines to buffer.
            maximum_diarization_delay (float): Max delay (in seconds) to wait for diarization data.
        """
        self._transcription_reader = PortReader(transcription_port)
        self._diarization_reader = PortReader(diarization_port)
        self._diarization_buffer = deque(maxlen=diarization_buffer_size)
        self._maximum_diarization_delay = maximum_diarization_delay

    @staticmethod
    def _get_word_information(word_line: str) -> Tuple[str, float, float]:
        """
        Parses a transcription line to extract the word and its start/end times.

        Args:
            word_line (str): Line containing transcription in format "start end word".

        Returns:
            Tuple[str, float, float]: A tuple containing the word and its start and end times in seconds.

        Raises:
            ValueError: If the end time is earlier than the start time.
        """
        parts = word_line.strip().split(' ', maxsplit=2)
        word = parts[2]
        word_start = float(parts[0]) / 1000  # divide by 1000 to convert to seconds
        word_end = float(parts[1]) / 1000

        # ensure word_start <= word_end
        # could also be done by word_end = max(word_start, word_end)
        word_start = min(word_start, word_end)
        return word, word_start, word_end

    @staticmethod
    def _get_speaker_information(rttm_line: str) -> Tuple[str, float, float]:
        """
        Parses an RTTM line to extract the speaker and their time segment.

        Args:
            rttm_line (str): RTTM formatted line indicating a speaker segment.

        Returns:
            Tuple[str, float, float]: A tuple containing the speaker ID, start time, and end time in seconds.

        Raises:
            ValueError: If the RTTM format is invalid or end time is earlier than start.
        """
        parts = rttm_line.strip().split()
        if len(parts) != 10 or parts[0] != 'SPEAKER':
            return None

        speaker = parts[7]
        speaker_start = float(parts[3])
        duration = float(parts[4])
        speaker_end = speaker_start + duration

        # ensure speaker_start <= speaker_end
        # could also be done by speaker_end = max(speaker_start, speaker_end)
        speaker_start = min(speaker_start, speaker_end)
        return speaker, speaker_start, speaker_end

    def _output_diarization(self, speaker: str, word: str) -> None:
        """
        Outputs the word and associated speaker.

        Args:
            speaker (str): The identified speaker for the word.
            word (str): The transcribed word.
        """
        print(f'{speaker}\t{word}')

    def _load_new_word_lines(self):
        """
        Reads all new word lines from the transcription stream.

        Returns:
            list[str] or None: A list of transcription lines, or None if the stream has ended.
        """
        first_word_line = self._transcription_reader.read_line()
        if first_word_line is None:
            return None
        word_lines = [first_word_line]
        while self._transcription_reader.has_data():
            word_lines.append(
                self._transcription_reader.read_line()
            )
        return word_lines

    def _update_diarization_buffer(self) -> None:
        """
        Reads all available diarization lines from the diarization stream and appends them to the buffer.
        The size of the buffer is limited to a fixed number of diarization lines. 
        """
        while self._diarization_reader.has_data():
            speaker_line = self._diarization_reader.read_line()
            speaker_turn = self._get_speaker_information(speaker_line)
            if speaker_turn is not None:
                self._diarization_buffer.append(speaker_turn)

    def _find_speaker(self, word_start: float, word_end: float) -> str:
        """
        Finds the best matching speaker for a word based on time overlap or proximity.

        Args:
            word_start (float): The start time of the word in seconds.
            word_end (float): The end time of the word in seconds.

        Returns:
            str: The speaker label most likely associated with the word.
        """
        overlaps = {}
        closest_speaker = 'unknown_speaker'
        closest_speaker_distance = float('inf')

        for speaker, speaker_start, speaker_end in self._diarization_buffer:

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
            # handle cases with speaker overlap (overlaps of length 0 also count)
            else:
                overlap_start = max(word_start, speaker_start)
                overlap_end = min(word_end, speaker_end)
                if speaker not in overlaps:
                    overlaps[speaker] = 0
                overlaps[speaker] += overlap_end - overlap_start

        if overlaps:
            return max(overlaps, key=overlaps.get)
        else:
            return closest_speaker

    def start_merging(self) -> None:
        """
        Starts the merging process by continuously reading transcription and diarization lines,
        assigning each word to the most appropriate speaker, and outputting the result.

        This function blocks indefinitely until the transcription stream ends.

        The algorithm works as follows:
        
        ```
        - repeat:
            - load all new lines with incoming words from the transcription reader
            - wait for `self._maximum_diarization_delay` seconds for the diarization to catch up
            - update the buffer with all new lines with speaker turns from the diarization reader
              (throw away first elements of the buffer to limit buffer size if needed)
            - assign speaker to each word and output the word with the assigned speaker in a normalized format
        ```
        """
        with ThreadPoolExecutor() as executor:
            executor.submit(self._transcription_reader.open)
            executor.submit(self._diarization_reader.open)

        while True:
            word_lines = self._load_new_word_lines()
            if word_lines is None:
                break

            time.sleep(self._maximum_diarization_delay)
            self._update_diarization_buffer()

            for word_line in word_lines:
                word, word_start, word_end = self._get_word_information(word_line)
                speaker = self._find_speaker(word_start, word_end)
                self._output_diarization(speaker, word)

        self._transcription_reader.close()
        self._diarization_reader.close()
