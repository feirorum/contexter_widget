"""Context detector implementations"""

from .window_title_detector import WindowTitleDetector
from .ide_project_detector import IdeProjectDetector
from .working_dir_detector import WorkingDirectoryDetector
from .git_repo_detector import GitRepoDetector
from .process_detector import ProcessDetector

__all__ = [
    'WindowTitleDetector',
    'IdeProjectDetector',
    'WorkingDirectoryDetector',
    'GitRepoDetector',
    'ProcessDetector'
]
