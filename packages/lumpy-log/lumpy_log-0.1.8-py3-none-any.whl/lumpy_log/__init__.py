"""Lumpy Log - Prettified Git Logs for Non-Experts"""

__version__ = "0.1.0"

from .changelump import ChangeLump
from .languages import Languages, Language


# Program-wide constants for output subdirectories
OUTPUT_JOURNAL_DIR = "journal"
OUTPUT_CHANGELOGS_DIR = "change_logs"
OUTPUT_TESTRESULTS_DIR = "test_results"

# Constants for item types
ITEM_TYPE_CHANGELOG = "changelog"
ITEM_TYPE_TEST = "test"
ITEM_TYPE_ENTRY = "journal"


__all__ = [
	"ChangeLump",
	"Languages",
	"Language",
	"OUTPUT_JOURNAL_DIR",
	"OUTPUT_CHANGELOGS_DIR",
	"OUTPUT_TESTRESULTS_DIR",
    "ITEM_TYPE_CHANGELOG",
    "ITEM_TYPE_TEST",
    "ITEM_TYPE_ENTRY",
]
