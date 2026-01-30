from dotenv import load_dotenv
load_dotenv(".env")

from timescaler.main import Timescaler, Hypertable
from timescaler.decorator import snap_stats
from timescaler.logger import setup_loki_logging

setup_loki_logging()