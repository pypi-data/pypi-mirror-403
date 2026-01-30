from .nsys_event import NsysEvent
import os.path
from sqlalchemy import text

class OSRTSemantic(NsysEvent):
    def __init__(self, report) -> None:
        super().__init__(report)

    def Setup(self):
        with open(os.path.join(os.path.dirname(__file__), '../scripts/osrt.sql'), 'r') as query:
            self.query = text(query.read())