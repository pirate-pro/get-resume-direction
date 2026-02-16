from enum import Enum


class SourceType(str, Enum):
    platform = "platform"
    university = "university"


class JobType(str, Enum):
    full_time = "full_time"
    intern = "intern"
    campus = "campus"
    part_time = "part_time"
    experienced = "experienced"
    unknown = "unknown"


class RemoteType(str, Enum):
    onsite = "onsite"
    hybrid = "hybrid"
    remote = "remote"
    unknown = "unknown"


class EducationLevel(str, Enum):
    unknown = "unknown"
    college = "college"
    bachelor = "bachelor"
    master = "master"
    phd = "phd"


class CrawlRunStatus(str, Enum):
    running = "running"
    success = "success"
    failed = "failed"
    paused = "paused"
