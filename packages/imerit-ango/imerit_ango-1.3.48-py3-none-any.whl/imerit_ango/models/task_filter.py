import json
from datetime import datetime
from typing import Dict, Any, Optional, List, Union


class DateRange:
    def __init__(self, gt: datetime = None, gte: datetime = None,
                 lt: datetime = None, lte: datetime = None):
        self.gt = gt
        self.gte = gte
        self.lt = lt
        self.lte = lte

    def toDict(self) -> Dict[str, str]:
        result = {}
        if self.gt:
            result["$gt"] = self.gt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        if self.gte:
            result["$gte"] = self.gte.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        if self.lt:
            result["$lt"] = self.lt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        if self.lte:
            result["$lte"] = self.lte.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        return result

    def is_empty(self) -> bool:
        return not any([self.gt, self.gte, self.lt, self.lte])


class NumberRange:
    def __init__(self, eq: Union[int, float] = None, ne: Union[int, float] = None,
                 gt: Union[int, float] = None, gte: Union[int, float] = None,
                 lt: Union[int, float] = None, lte: Union[int, float] = None):
        self.eq = eq
        self.ne = ne
        self.gt = gt
        self.gte = gte
        self.lt = lt
        self.lte = lte

    def toDict(self) -> Dict[str, Union[int, float]]:
        result = {}
        if self.eq is not None:
            result["$eq"] = self.eq
        if self.ne is not None:
            result["$ne"] = self.ne
        if self.gt is not None:
            result["$gt"] = self.gt
        if self.gte is not None:
            result["$gte"] = self.gte
        if self.lt is not None:
            result["$lt"] = self.lt
        if self.lte is not None:
            result["$lte"] = self.lte
        return result

    def is_empty(self) -> bool:
        return not any([
            self.eq is not None, self.ne is not None,
            self.gt is not None, self.gte is not None,
            self.lt is not None, self.lte is not None
        ])


class StringFilter:
    def __init__(self, eq: str = None, ne: str = None, regex: str = None,
                 in_list: List[str] = None, nin: List[str] = None, exists: bool = None):
        self.eq = eq
        self.ne = ne
        self.regex = regex
        self.in_list = in_list
        self.nin = nin
        self.exists = exists

    def toDict(self) -> Dict[str, Any]:
        result = {}
        if self.eq is not None:
            result["$eq"] = self.eq
        if self.ne is not None:
            result["$ne"] = self.ne
        if self.regex is not None:
            result["$regex"] = self.regex
        if self.in_list is not None:
            result["$in"] = self.in_list
        if self.nin is not None:
            result["$nin"] = self.nin
        if self.exists is not None:
            result["$exists"] = self.exists
        return result

    def is_empty(self) -> bool:
        return not any([
            self.eq is not None, self.ne is not None,
            self.regex is not None, self.in_list is not None,
            self.nin is not None, self.exists is not None
        ])


class TaskFilter:
    def __init__(self,
                 stage: Union[str, List[str], StringFilter] = None,
                 batches: Union[List[str], StringFilter] = None,
                 status=None,
                 review_status=None,
                 task_type=None,
                 assignee: Union[str, StringFilter] = None,
                 external_id: Union[str, StringFilter] = None,
                 created_at: DateRange = None,
                 updated_at: DateRange = None,
                 created_by: Union[str, StringFilter] = None,
                 updated_by: Union[str, StringFilter] = None,
                 priority: Union[int, NumberRange] = None,
                 duration: NumberRange = None,
                 total_duration: NumberRange = None,
                 open_issues_count: Union[int, NumberRange] = None,
                 is_draft: bool = None,
                 is_skipped: bool = None,
                 is_benchmark: bool = None):
        self.stage = stage
        self.batches = batches
        self.status = status
        self.review_status = review_status
        self.task_type = task_type
        self.assignee = assignee
        self.external_id = external_id
        self.created_at = created_at
        self.updated_at = updated_at
        self.created_by = created_by
        self.updated_by = updated_by
        self.priority = priority
        self.duration = duration
        self.total_duration = total_duration
        self.open_issues_count = open_issues_count
        self.is_draft = is_draft
        self.is_skipped = is_skipped
        self.is_benchmark = is_benchmark

    def _process_string_field(self, value, field_name: str, filter_dict: Dict[str, Any]):
        if value is None:
            return
        if isinstance(value, StringFilter):
            if not value.is_empty():
                filter_dict[field_name] = value.toDict()
        elif hasattr(value, 'value'):
            filter_dict[field_name] = {"$eq": value.value}
        else:
            filter_dict[field_name] = {"$eq": value}

    def toDict(self) -> Dict[str, Any]:
        filter_dict = {}

        if self.stage is not None:
            if isinstance(self.stage, StringFilter):
                if not self.stage.is_empty():
                    filter_dict["stage"] = self.stage.toDict()
            elif isinstance(self.stage, list):
                filter_dict["stage"] = {"$in": self.stage}
            else:
                filter_dict["stage"] = self.stage

        if self.batches is not None:
            if isinstance(self.batches, StringFilter):
                if not self.batches.is_empty():
                    filter_dict["batches"] = self.batches.toDict()
            else:
                filter_dict["batches"] = {"$in": self.batches}

        self._process_string_field(self.status, "status", filter_dict)
        self._process_string_field(self.review_status, "reviewStatus", filter_dict)
        self._process_string_field(self.task_type, "type", filter_dict)
        self._process_string_field(self.assignee, "assignee", filter_dict)
        self._process_string_field(self.external_id, "externalId", filter_dict)

        if self.created_at is not None and not self.created_at.is_empty():
            filter_dict["createdAt"] = self.created_at.toDict()

        if self.updated_at is not None and not self.updated_at.is_empty():
            filter_dict["updatedAt"] = self.updated_at.toDict()

        self._process_string_field(self.created_by, "createdBy", filter_dict)
        self._process_string_field(self.updated_by, "updatedBy", filter_dict)

        if self.priority is not None:
            if isinstance(self.priority, NumberRange):
                if not self.priority.is_empty():
                    filter_dict["priority"] = self.priority.toDict()
            else:
                filter_dict["priority"] = {"$eq": self.priority}

        if self.duration is not None and not self.duration.is_empty():
            filter_dict["duration"] = self.duration.toDict()

        if self.total_duration is not None and not self.total_duration.is_empty():
            filter_dict["totalDuration"] = self.total_duration.toDict()

        if self.open_issues_count is not None:
            if isinstance(self.open_issues_count, NumberRange):
                if not self.open_issues_count.is_empty():
                    filter_dict["openIssuesCount"] = self.open_issues_count.toDict()
            else:
                filter_dict["openIssuesCount"] = {"$eq": self.open_issues_count}

        if self.is_draft is not None:
            filter_dict["isDraft"] = {"$eq": self.is_draft}

        if self.is_skipped is not None:
            filter_dict["isSkipped"] = {"$eq": self.is_skipped}

        if self.is_benchmark is not None:
            filter_dict["isBenchmark"] = {"$eq": self.is_benchmark}

        return filter_dict

    def to_json(self) -> str:
        return json.dumps(self.toDict())

    def is_empty(self) -> bool:
        return len(self.toDict()) == 0
