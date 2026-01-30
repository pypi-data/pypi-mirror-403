from .nsys_event import NsysEvent
import os.path
from sqlalchemy import text
from .pthread_event_encoding import *

class PthreadSemantic(NsysEvent):
    def __init__(self, report) -> None:
        super().__init__(report)

    def Setup(self):
        with open(os.path.join(os.path.dirname(__file__), '../scripts/pthreads.sql'), 'r') as query:
            self.query = text(query.read())