from sqlalchemy import Boolean, create_engine, exc, inspect
import pandas as pd
import os.path
from enum import Enum
from typing import Any, TypedDict, TypeAlias
from functools import reduce

ESD = TypedDict('ESD', {'name': str, 'type': int, 'names': pd.DataFrame | None})
RecordCol: TypeAlias = tuple[int | str, str]

class InvalidProcessModelApplication(Exception):
        def __init__(self, type, df_class):
            super().__init__(f'Trying to apply {type} process model to event type class {df_class}, which does not support it.')

class NsysEvent:

    class MissingDatabaseFile(Exception):
        def __init__(self, filename):
            super().__init__(f'Database file {filename} does not exist.')

    class InvalidDatabaseFile(Exception):
        def __init__(self, filename):
            super().__init__(f'Database file {filename} could not be opened and appears to be invalid.')
    
    class InvalidSQL(Exception):
        def __init__(self, sql):
            super().__init__(f'Bad SQL statement: {sql}')

    class EventClassNotPresent(Exception):
        table = ""
        report_file = ""
        class ErrorType(Enum):
            ENOTABLE = 1
            EEMPTY = 2
        
        def __init__(self, etype: ErrorType, rf, ec = ""):
            self.report_file = rf
            self.type = etype
            if self.type == self.ErrorType.ENOTABLE:
                self.table = ec
                super().__init__(f'This event class is not present in this trace because table {ec} does not exist.')
            else:
                super().__init__(f'This event class is not present in the specified tables.')

    query = "SELECT 1 AS 'ONE'"

    with_paraver_pm: bool = False
    _df: pd.DataFrame | list[pd.DataFrame]

    def __init__(self, report) -> None:
        if isinstance(report, str):
            self._dbcon = None
            self._dbfile = f"{os.path.join(os.getcwd(), os.path.splitext(os.path.basename(report))[0])}.sqlite"
            self._df = pd.DataFrame()
            self._empty = False
            self.prepare_statements = []

            if not os.path.exists(self._dbfile):
                raise self.MissingDatabaseFile(self._dbfile)

            try:
                self._dbcon = create_engine(f"sqlite:///{self._dbfile}")
            except exc.SQLAlchemyError:
                self._dbcon = None
                raise self.InvalidDatabaseFile(self._dbfile)
        else:
            self._dbcon = None
            self._dbfile = None
            self._df = None
            self._empty = False
            self.prepare_statements = []
        
    def check_table(self, table_name):
        insp = inspect(self._dbcon)
        return insp.has_table(table_name)

    def get_value(self, table, column, key):
        tab = pd.read_sql_table(table, self._dbcon)
        return tab.loc[tab[column] == key]

    def Setup(self):
        pass

    def _preprocess(self):
        pass

    def postprocess(self):
        pass

    def load_data(self):
        if not self._empty:
            try:
                if len(self.prepare_statements) > 0:
                    cursor = self._dbcon.raw_connection().cursor()
                    for statement in self.prepare_statements:
                        cursor.execute(statement)
                self._df = pd.read_sql_query(self.query, self._dbcon)
                # if self._df.empty(): TODO: If we do this, then we need to check for exception in all semantic object creation and still allow those that have multiple data frames (like MPI) and that some of them can still be empty.
                #     raise self.EventClassNotPresent(self.EventClassNotPresent.ErrorType.EEMPTY, self._dbfile)
            except pd.errors.DatabaseError:
                raise self.InvalidSQL(self.query)
            except exc.OperationalError as oerr:
                str_err = str(oerr)
                if "no such table:" in str_err:
                    start = str_err.find("no such table:") + 15
                    end = str_err.find('\n', start)
                    self._empty = True
                    raise self.EventClassNotPresent(self.EventClassNotPresent.ErrorType.ENOTABLE, self._dbfile, str_err[start:end])
                else:
                    raise oerr
            self._preprocess()

    def load_from_dataframes_and_align(self, dfs: list[pd.DataFrame], deltas: list[int], hostnames: list[str]):
        for i, df in enumerate(dfs):
            df['hostname'] = hostnames[i]
            df['Start:ts_ns'] += deltas[i]
            df['End:ts_ns'] += deltas[i]
        self._df = pd.concat(dfs, ignore_index=True)


    def apply_cpu_process_model(self, threads: pd.DataFrame):
        if("Device" in self._df.columns):
            raise InvalidProcessModelApplication("thread", self.__class__.__name__)
        self._df["thread"] = self._df["Tid"].map(threads.set_index('Tid')["thread"])
        self._df["task"] = self._df["Tid"].map(threads.set_index('Tid')["task"])
        if 'Rank' in threads.columns:
            self._df["Rank"] = self._df["Tid"].map(threads.set_index('Tid')["Rank"])

    def apply_gpu_process_model(self, streams: pd.DataFrame):
        raise NotImplementedError()

    def get_threads(self):
        return self._df[['Pid', 'Tid']].drop_duplicates()
    
    def get_df(self):
        return self._df.copy()

    def get_event_semantic_definition_dictionary(self) -> list[ESD]:
        raise NotImplementedError(f'Generalization of semantics definition for class {self.__class__.__name__} still not implemented.')
    
    def get_record_columns(self) -> list[list[RecordCol]] | list[RecordCol]:
        raise NotImplementedError(f'Generalization of columns to serialize records for class {self.__class__.__name__} still not implemented.')
    
    def get_max_time(self) -> int:
        if isinstance(self._df, list):
            reduce(max, [t["End:ts_ns"].max() for t in self._df], 0)
        else:
            return self._df["End:ts_ns"].max()
