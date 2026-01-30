from .nsys_event import NsysEvent
from pandas import read_sql_table, DataFrame
from sqlalchemy import text
import time
import os

event_type_metrics_base = 9400


class GPUMetricsSemantic(NsysEvent):
    def __init__(self, report) -> None:
        self.metrics_event_names = DataFrame()
        super().__init__(report)
    
    def Setup(self):
        if self.check_table("GPU_METRICS"):
            with open(os.path.join(os.path.dirname(__file__), '../scripts/gpu-metrics.sql'), 'r') as query:
                self.query = text(query.read())
            return True
        else:
            self._empty = True
            return False
    
    def _preprocess(self):
        #print(f"Start preprocessing GPU metrics of report {self._dbfile}")
        #t = time.time()
        metrics_description = read_sql_table("TARGET_INFO_GPU_METRICS", self._dbcon)
        self._df.drop(self._df[self._df["timestamp"] < 0].index, inplace=True) # drop negative time
        self.metrics_event_names = metrics_description.groupby(["metricId"]).agg({'metricName': 'first'}).reset_index()
        self.metrics_event_names["metricId"] = self.metrics_event_names["metricId"] + event_type_metrics_base
        self._df["deviceId"] = self._df["typeId"].astype("int64") & 0xFF
        #self._df.loc[self._df["value"] < 0, "value"] = 0 # Workaround for bug #33 (https://gitlab.pm.bsc.es/beppp/nsys2prv/-/issues/33)
        #self._df = self._df.groupby(["timestamp", "typeId"]).agg({'metricId': lambda x: list(x+event_type_metrics_base),
        #                                                                'value': lambda x: list(x),
        #                                                                'deviceId': 'first'})
        # ISSUE #36 : Performance degradation at large number of rows because opf python object explosion
        # Recommended Fix: Expand the values to columns, spliting into as many metricIds as columns
        # Temporal workaround as of 16/01/2026: Move this spliting at serialization time. We will pay the performance price still, but memory won't blow up.
        # self._df["metricId"] = self._df["metricId"].str.split(';')
        # self._df["metric_values"] = self._df["metric_values"].str.split(';')

        self._df = self._df.reset_index()
        #t_end = time.time() - t
        #print(f"End of preprocessing. Time: {t_end: .3f}")
        return super()._preprocess()
    
    def get_names(self):
        return self.metrics_event_names