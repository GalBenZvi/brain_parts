import logging

SUMMARY_MESSAGE = """
Found {num_valid} available subjects and {num_missing} ones.
Valids subjects' table can be found at {destination}/valid.csv.
Missing subjects' table can be found at {destination}/missing.csv.
"""

LOGGER_CONFIG = dict(
    filemode="w",
    format="%(asctime)s - %(message)s",
    level=logging.INFO,
)
