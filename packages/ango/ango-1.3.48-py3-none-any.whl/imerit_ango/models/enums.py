from enum import Enum


class Metrics(Enum):
    LabelStageGroups = 'LabelStageGroups'
    TimePerTask = 'TimePerTask'
    AnnotationStatus = 'AnnotationStatus'
    AnswerDistribution = 'AnswerDistribution'
    ConsensusRanges = 'ConsensusRanges'
    AssetSize = 'AssetSize'


class OrganizationRoles(Enum):
    Member = 'member'
    Admin = 'admin'


class ProjectRoles(Enum):
    Manager = 'Manager'
    Labeler = 'Labeler'
    Reviewer = 'Reviewer'
    Lead = 'Lead'


class StorageProvider(Enum):
    AWS = 'AWS'
    GCP = 'GCP'
    AZURE = 'AZURE'


class StorageFileTypes(Enum):
    BRUSH = 'brushes'
    MEDICAL_BRUSH = 'medicalBrushes'
    ASSET = 'assets'
    EXPORT = 'exports'
    INSTRUCTION = 'instructions'


class ExportTypes(Enum):
    TASK = 'task'
    ISSUE = 'issue'


class ExportFormats(Enum):
    JSON = 'json'
    NDJSON = 'ndjson'


class TaskTypes(Enum):
    CONSENSUS = 'consensus'
    DEFAULT = 'default'
    BENCHMARK = 'benchmark'


class ProjectType(Enum):
    Ango = 'ango'
    PCT = 'pct'
    IFrame = 'iframe'


class ReviewStatus(Enum):
    ACCEPTED = 'Accepted'
    REJECTED = 'Rejected'
    TODO = 'Todo'
    FIXED = 'Fixed'


class TaskStatus(Enum):
    READY = 'READY'
    PCT_REQUEUE_WAITING = 'PCT_REQUEUE_WAITING'
    PCT_SUBMIT_WAITING = 'PCT_SUBMIT_WAITING'


class TaskType(Enum):
    DEFAULT = 'default'
    CONSENSUS = 'consensus'
    BENCHMARK = 'benchmark'


class SortOrder(Enum):
    ASC = 'asc'
    DESC = 'desc'


class StageType(Enum):
    Start = 'Start'
    Label = 'Label'
    Review = 'Review'
    Logic = 'Logic'
    Plugin = 'Plugin'
    Webhook = 'Webhook'
    Complete = 'Complete'
    Archive = 'Archive'
    Consensus = 'Consensus'
    Hold = 'Hold'
