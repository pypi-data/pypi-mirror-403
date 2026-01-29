"""
EduBridge Resources
"""

from .analytics import AnalyticsResource
from .applications import ApplicationsResource
from .enrollments import EnrollmentsResource
from .learning_reports import LearningReportsResource
from .subject_track import SubjectTrackResource
from .users import UsersResource

__all__ = [
    "AnalyticsResource",
    "ApplicationsResource",
    "EnrollmentsResource",
    "LearningReportsResource",
    "SubjectTrackResource",
    "UsersResource",
]
