import pandas as pd

REPLACEMENT_COLUMNS = {
    "ID": "id",
    "Questionnaire": "questionnaire_id",
    "Height": "height",
    "Weight": "weight",
    "Gender": "gender",
}

SUMMARY_MESSAGE = """
Found {num_valid} available subjects and {num_missing} ones.
Valids subjects' table can be found at {destination}/valid.csv.
Missing subjects' table can be found at {destination}/missing.csv.
"""


def transform_row(
    row: pd.Series, replacements: dict = REPLACEMENT_COLUMNS
) -> pd.Series:
    """
    Replaces columns according to *replacements*

    Parameters
    ----------
    row : pd.Series
        A row to be transformed
    replacements : dict, optional
        Replacements dictionary, containing columns from *row*, by default REPLACEMENT_COLUMNS

    Returns
    -------
    pd.Series
        A transformed series.
    """
    transformed_row = row[[key for key in replacements.keys()]]
    transformed_row.index = [val for val in replacements.values()]
    return transformed_row
