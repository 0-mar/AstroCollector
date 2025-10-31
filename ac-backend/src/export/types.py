from enum import Enum


class ExportOption(Enum):
    single_file = "SINGLE_FILE"
    by_sources = "BY_SOURCES"
    raw_data = "RAW_DATA"
