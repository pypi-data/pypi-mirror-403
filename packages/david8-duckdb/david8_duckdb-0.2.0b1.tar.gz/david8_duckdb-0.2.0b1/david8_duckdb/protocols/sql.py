from david8.protocols.sql import SelectProtocol as _SelectProtocol


class SelectProtocol(_SelectProtocol):
    def from_csv(self, *file_names: str) -> 'SelectProtocol':
        """
        https://duckdb.org/docs/stable/data/csv/reading_faulty_csv_files
        """

    def from_json(self, *file_names: str) -> 'SelectProtocol':
        """
        https://duckdb.org/docs/stable/data/json/loading_json#the-read_json-function
        """

    def from_json_objects(self, *file_names: str) -> 'SelectProtocol':
        """
        https://duckdb.org/docs/stable/data/json/loading_json#functions-for-reading-json-objects
        """

    def from_ndjson_objects(self, *file_names: str) -> 'SelectProtocol':
        """
        https://duckdb.org/docs/stable/data/json/loading_json#functions-for-reading-json-objects
        """

    def from_json_objects_auto(self, *file_names: str) -> 'SelectProtocol':
        """
        https://duckdb.org/docs/stable/data/json/loading_json#functions-for-reading-json-objects
        """

    def from_parquet(self, *file_names: str) -> 'SelectProtocol':
        """
        read_parquet(): https://duckdb.org/docs/stable/data/parquet/overview
        """

    def from_xlsx(self, file_name: str) -> 'SelectProtocol':
        """
        read_xlsx(): https://duckdb.org/docs/stable/core_extensions/excel
        """
