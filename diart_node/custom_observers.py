from typing import Union, Text, Tuple
import sys
from pyannote.core import Annotation
from diart.sinks import _extract_prediction
from rx.core import Observer


class StdoutWriter(Observer):
    def __init__(self, uri: Text):
        super().__init__()
        self.uri = uri

    def on_next(self, value: Union[Tuple, Annotation]):
        prediction = _extract_prediction(value)
        # Write prediction in RTTM format
        prediction.uri = self.uri

        prediction.write_rttm(sys.stdout)

    def on_error(self, error: Exception):
        return

    def on_completed(self):
        return
