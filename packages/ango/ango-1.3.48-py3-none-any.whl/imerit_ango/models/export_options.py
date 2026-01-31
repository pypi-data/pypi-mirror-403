import json
from datetime import datetime

from imerit_ango.models.enums import ExportTypes, ExportFormats, TaskTypes
from typing import List, Dict, Any, Optional


class TimeFilter:
    def __init__(self, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None):
        self.from_date = from_date
        self.to_date = to_date

    def toDict(self) -> Dict[str, Any]:
        if self.from_date and self.to_date:
            return {
                "$gt": f"{self.from_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')}",
                "$lt": f"{self.to_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')}"
            }
        elif self.from_date:
            return {"$gt": f"{self.from_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')}"}
        elif self.to_date:
            return {"$lt": f"{self.to_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')}"}
        return {}

    def to_json(self) -> str:
        return json.dumps(self.toDict())


class ExportOptions:
    def __init__(self,
                 stage: List[str] = None,
                 batches: List[str] = None,
                 task_type: TaskTypes = None,
                 export_format: ExportFormats = ExportFormats.JSON,
                 export_type: ExportTypes = ExportTypes.TASK,
                 include_key_frames_only: bool = False,
                 include_idle_blur_durations: bool = False,
                 send_email: bool = False,
                 include_metadata: bool = True,
                 include_history: bool = True,
                 notify: bool = False,
                 updated_at: TimeFilter = None,
                 created_at: TimeFilter = None
                 ):
        if task_type is None:
            task_type = TaskTypes.DEFAULT
        if stage is None and task_type is TaskTypes.DEFAULT:
            stage =  ['Complete']
        self.stage = stage
        self.batches = batches
        self.task_types = [task_type]
        self.export_format = export_format
        self.export_type = export_type
        self.include_key_frames_only = include_key_frames_only
        self.send_email = send_email
        self.include_metadata = include_metadata
        self.include_history = include_history
        self.notify = notify
        self.updated_at = updated_at
        self.created_at = created_at
        self.include_idle_blur_durations = include_idle_blur_durations

    def toDict(self) -> Dict[str, Any]:
        result = {
            "sendEmail": str(self.send_email).lower(),
            "includeMetadata": str(self.include_metadata).lower(),
            "includeHistory": str(self.include_history).lower(),
            "doNotNotify": str(not self.notify).lower(),
            "format": self.export_format.value,
            "type": self.export_type.value,
            "includeOnlyKeyFrames": str(self.include_key_frames_only).lower(),
            "includeIdleBlurDurations": str(self.include_idle_blur_durations).lower()
        }
        if self.batches:
            result["batches"] = json.dumps(self.batches)
        if self.task_types:
            result["taskTypes"] = json.dumps([t.value for t in self.task_types])
        if self.stage and self.export_type == ExportTypes.TASK:
            result["stage"] = json.dumps(self.stage)
        if self.updated_at:
            result["updatedAt"] = self.updated_at.to_json()
        if self.created_at:
            result["createdAt"] = self.created_at.to_json()

        return result
