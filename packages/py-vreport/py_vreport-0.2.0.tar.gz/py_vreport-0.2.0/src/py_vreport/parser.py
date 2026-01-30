"""Canoe XML Report Parser Module"""

__author__ = "Mohamed Hamed Othman"
__email__ = "mohamedahamed1915@gmail.com"

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict

from .models import TestModule, TestGroup, TestCase, TestStep, FailureContext


class CanoeReportParser:
    def __init__(self, xml_file: str) -> None:
        self.file_path = Path(xml_file)
        if not self.file_path.exists():
            raise FileNotFoundError(f"File {xml_file} does not exist.")
        if not self.file_path.is_file():
            raise IsADirectoryError(f"Path {xml_file} is a directory, not a file.")

    def parse(self) -> TestModule:
        """Parses the Canoe XML report and returns a TestModule object."""
        try:
            tree = ET.parse(self.file_path)
            root = tree.getroot()
        except ET.ParseError as e:
            raise ValueError(f"Failed to parse XML file: {e}")

        module_name_node = root.find(
            'testsetup/xinfo[@name="Test Module Name"]/description'
        )

        module_name = (
            module_name_node.text if module_name_node is not None else "Unknown Module"
        )

        start_time_str = root.get("starttime", "")

        test_module = TestModule(
            name=module_name,
            file_path=str(self.file_path),
            start_time=start_time_str,
        )

        # Recursively parse test groups
        for child in root:
            if child.tag == "testgroup":
                test_module.root_groups.append(self._parse_group(child))

        return test_module

    def _parse_group(self, group_node: ET.Element) -> TestGroup:
        """Parases a test group node and returns a TestGroup object."""
        title = group_node.findtext("title", default="Untitled Group")
        group = TestGroup(title=title)

        for child in group_node:
            if child.tag == "testgroup":
                group.groups.append(self._parse_group(child))
            elif child.tag == "testcase":
                group.test_cases.append(self._parse_test_case(child))
            elif child.tag == "skipped":
                skipped_case = TestCase(
                    title=child.findtext("title", default="Skipped Case"),
                    verdict="skipped",
                    start_time=0,
                    end_time=0,
                )
                group.test_cases.append(skipped_case)
        return group

    def _parse_tabular_info(self, node: ET.Element) -> List[Dict[str, str]]:
        """Extracts key-value pairs from UDS/Tabular Info nodes."""
        tabular_data = []
        tabular = node.find("tabularinfo")
        if tabular is not None:
            # We assume standard CANoe structure: Parameter | Value | Raw
            for row in tabular.iter("row"):
                cells = row.findall("cell")
                if len(cells) >= 2:
                    param = cells[0].text.strip() if cells[0].text else ""
                    value = cells[1].text.strip() if cells[1].text else ""
                    raw = (
                        cells[2].text.strip()
                        if len(cells) > 2 and cells[2].text
                        else ""
                    )

                    if param:
                        tabular_data.append(
                            {"parameter": param, "value": value, "raw": raw}
                        )
        return tabular_data

    def _parse_test_case(self, case_node: ET.Element) -> TestCase:
        title = case_node.findtext("title", default="Untitled Case")
        verdict_node = case_node.find("verdict")
        result = (
            verdict_node.get("result", "inconclusive")
            if verdict_node is not None
            else "inconclusive"
        )

        start_ts = float(case_node.get("timestamp", "0"))
        end_ts = (
            float(verdict_node.get("timestamp", start_ts))
            if verdict_node is not None
            else start_ts
        )

        steps = []
        rich_failures = []

        current_context_logs = []

        for node in case_node.iter():
            tag = node.tag

            # 1. Reset context when entering a new high level pattern
            if tag == "testpattern":
                current_context_logs = []
                # if pattern has a title, add it as context
                pat_title = node.findtext("title")
                if pat_title:
                    current_context_logs.append(f"Pattern: {pat_title}")
                continue

            # 2. Process test steps
            if tag == "teststep":
                step_result = node.get("result", "unknown")
                step_text = node.text.strip() if node.text else ""
                step_ident = node.get("ident", "")

                # A. Parse Table Data (if any)
                table_data = self._parse_tabular_info(node)

                # B. Create TestStep object
                step = TestStep(
                    timestamp=float(node.get("timestamp", "0")),
                    result=step_result,
                    level=int(node.get("level", "0")),
                    type=node.get("type", "info"),
                    ident=step_ident,
                    description=step_text,
                    diagnostic_data=table_data,
                )
                steps.append(step)

                # C. Context Collection Logic
                # Collect if it's informatioinal ( start with I-, Description, or type=user/auto pass)
                is_info = (
                    step_ident.startswith("I-")
                    or step_ident in ["Description", "INFO"]
                    or ("=" in step_text and step_result != "fail")
                )

                if is_info and step_text:
                    log_entry = (
                        f"{step_ident}: {step_text}" if step_ident else step_text
                    )
                    current_context_logs.append(log_entry)

                # D. Failure Detection
                if step_result.lower() == "fail":
                    msg = (
                        step_text
                        if step_text
                        else (step_ident if step_ident else "Unknown Failure")
                    )

                    failure_ctx = FailureContext(
                        message=msg,
                        context_logs=list(
                            current_context_logs
                        ),  # snapshot current logs
                        diagnostic_table=table_data,
                    )
                    rich_failures.append(failure_ctx)

        # Legacy String for backward compatibility
        legacy_reason = (
            " | ".join([f.message for f in rich_failures]) if rich_failures else None
        )

        return TestCase(
            title=title,
            verdict=result,
            start_time=start_ts,
            end_time=end_ts,
            steps=steps,
            failure_reason=legacy_reason,
            rich_failure=rich_failures,
        )
