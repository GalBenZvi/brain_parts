"""
Provides a dictionary mapping atlas string IDs to a dictionary of files
required for parcellation.
"""
from typing import Dict

from connecticity.managers.parcellation.atlases.brainnetome import BRAINNETOME

#: Available atlases to use for parcellation.
PARCELLATION_FILES: Dict[str, Dict] = {"brainnetome": BRAINNETOME}
