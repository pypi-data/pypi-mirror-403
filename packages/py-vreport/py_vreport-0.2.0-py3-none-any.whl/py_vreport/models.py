from dataclasses import dataclass, field
from typing import Any, List, Optional, Dict


@dataclass
class TestStep:
    timestamp: float
    result: str
    level: int
    type: str
    ident: Optional[str] = None
    description: Optional[str] = None
    diagnostic_data: List[Dict[str, str]] = field(default_factory=list)
    custom_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FailureContext:
    message: str
    context_logs: List[str] = field(default_factory=list)
    diagnostic_table: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class TestCase:
    title: str
    verdict: str
    start_time: float
    end_time: float
    steps: List[TestStep] = field(default_factory=list)
    failure_reason: Optional[str] = None
    rich_failure: List[FailureContext] = field(default_factory=list)

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time

    def is_failed(self) -> bool:
        return self.verdict.lower() == "fail"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "verdict": self.verdict,
            "duration": self.duration,
            "failure_reason": self.failure_reason,
            "rich_failure_count": len(self.rich_failure),
        }


@dataclass
class TestGroup:
    title: str
    groups: List["TestGroup"] = field(default_factory=list)
    test_cases: List[TestCase] = field(default_factory=list)

    def get_all_test_cases(self) -> List[TestCase]:
        cases = self.test_cases[:]
        for group in self.groups:
            cases.extend(group.get_all_test_cases())
        return cases


@dataclass
class TestModule:
    name: str
    file_path: str
    start_time: str
    root_groups: List[TestGroup] = field(default_factory=list)

    def get_all_failures(self) -> List[TestCase]:
        all_cases = []
        for group in self.root_groups:
            all_cases.extend(group.get_all_test_cases())
        return [case for case in all_cases if case.is_failed()]

    def to_pandas(self):
        import pandas as pd

        data = []
        for group in self.root_groups:
            for tc in group.get_all_test_cases():
                row = tc.to_dict()
                row["module_name"] = self.name
                row["group"] = group.title
                data.append(row)
        return pd.DataFrame(data)
