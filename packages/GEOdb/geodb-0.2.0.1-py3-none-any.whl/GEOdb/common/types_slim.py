from datetime import datetime
from dataclasses import dataclass


@dataclass
class GEOSample:
    title: str
    id: str
    date: datetime
    type: str  # sample type: SRA, etc.
    platform: str
    series: str


class GEOSeriesInfoExtra:
    # empty class
    def __init__(self):
        pass


@dataclass
class GEOSeriesInfo:
    title: str
    link: str
    organism: str
    type: str  # experiment type: array, high throughput sequencing, etc.
    summary: str
    platform: str
    samples_count: int
    id: str
    series_id: int

    date: datetime = None
    status: datetime = None  # alias for date
    design: str = None
    contributors: list[str] = None
    samples: list[GEOSample] = None
    citation: str = None
    extra: GEOSeriesInfoExtra = None
    ftp: str = None
    sra: str = None
