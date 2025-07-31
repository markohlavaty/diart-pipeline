from typing import Union, Text, Tuple
import sys
from pyannote.core import Annotation
from diart.sinks import _extract_prediction
from rx.core import Observer


class StdoutWriter(Observer):
    """
    A custom observer that takes in predictions from Diart
    and writes them to the standard output.

    The writer does not do any patching - that is, if more subsequent
    audio chunks are parts of the same utterance, the output contains
    a line for each of those chunks (not for the whole utterance).

    Attributes:
        uri (Text): A string to identify the audio stream.
    """

    def __init__(self, uri: Text) -> None:
        """
        Initialize the StdoutWriter.

        Args:
            uri (Text): The URI string to identify the audio stream being processed.
        """
        super().__init__()
        self.uri = uri

    def on_next(self, value: Union[Tuple, Annotation]) -> None:
        """
        Called when the observer receives a new value.

        Args:
            value (Union[Tuple, Annotation]): The diarization result,
            either as an Annotation object or as a tuple containing
            the annotation object as the first element.
        """
        prediction = _extract_prediction(value)
        # Write prediction in RTTM format
        prediction.uri = self.uri
        prediction.write_rttm(sys.stdout)
