from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from typing import List
from .models import TestModule, TestCase, FailureContext

console = Console()


class SummaryFormatter:
    @staticmethod
    def print_summary(report: TestModule, console: Console = console):
        total_cases = sum(
            len(group.get_all_test_cases()) for group in report.root_groups
        )
        failures = report.get_all_failures()

        table = Table(title=f"Module: {report.name}", box=box.ROUNDED)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="magenta")

        table.add_row("File", report.file_path)
        table.add_row("Start Time", report.start_time)
        table.add_row("Total Tests", str(total_cases))

        failure_style = "red" if failures else "green"
        table.add_row("Failures", str(len(failures)), style=failure_style)

        console.print(table)

        if failures:
            console.print("\n[bold red]Failed Tests:[/bold red]")
            for fail in failures:
                console.print(
                    f"  [red]•[/red] {fail.title}: [italic]{fail.failure_reason}[/italic]"
                )


class FailureFormatter:
    @staticmethod
    def print_failures(report: TestModule, console: Console = console):
        failures = report.get_all_failures()
        if not failures:
            console.print(
                f"[green]✔[/green] No failures in module: [bold]{report.name}[/bold]"
            )
            return

        console.print(
            Panel(
                f"[bold red]{report.name}[/bold red] - Found {len(failures)} failures",
                box=box.DOUBLE,
                border_style="red",
            )
        )

        for fail in failures:
            console.print(f"\n[bold red]✖ {fail.title}[/bold red]")
            console.print(f"  [italic]{fail.failure_reason}[/italic]")

            for rf in fail.rich_failure:
                FailureFormatter._print_rich_failure(rf, console=console)

    @staticmethod
    def _print_rich_failure(rf: FailureContext, console: Console = console):
        if rf.context_logs:
            log_text = Text("\nContext:\n", style="bold yellow")
            for log in rf.context_logs[-5:]:
                log_text.append(f"  - {log}\n", style="dim")
            console.print(log_text)

        if rf.diagnostic_table:
            diag_table = Table(
                title="Diagnostic Data", box=box.SIMPLE, title_style="bold blue"
            )
            diag_table.add_column("Parameter")
            diag_table.add_column("Value")
            diag_table.add_column("Raw")

            for row in rf.diagnostic_table:
                diag_table.add_row(row["parameter"], row["value"], row["raw"])
            console.print(diag_table)

        console.print(Panel(rf.message, title="ERROR", border_style="red"))


class DetailedFormatter:
    @staticmethod
    def print_test_case(
        report_name: str, test_cases: List[TestCase], console: Console = console
    ):
        for case in test_cases:
            console.print(f"\n[bold blue]TEST CASE:[/bold blue] {case.title}")
            console.print(
                f"[bold]VERDICT:[/bold] {DetailedFormatter._format_verdict(case.verdict)}"
            )
            console.print(f"[bold]DURATION:[/bold] {case.duration:.4f}s")

            table = Table(
                box=box.MINIMAL_DOUBLE_HEAD, show_header=True, header_style="bold"
            )
            table.add_column("Timestamp", width=12)
            table.add_column("Result", width=8)
            table.add_column("Description")

            for step in case.steps:
                ts_str = f"{step.timestamp:.6f}"
                res_label = DetailedFormatter._format_verdict(step.result)

                indent = "  " * step.level
                indent_str = f"[bold][{step.ident}][/bold] " if step.ident else ""

                table.add_row(
                    ts_str, res_label, f"{indent}{indent_str}{step.description}"
                )

                if step.diagnostic_data:
                    diag_info = ""
                    for row in step.diagnostic_data:
                        raw_val = f" (Raw: {row['raw']})" if row["raw"] else ""
                        diag_info += (
                            f"{indent}  - {row['parameter']}: {row['value']}{raw_val}\n"
                        )
                    table.add_row("", "", f"[dim blue]{diag_info.strip()}[/dim blue]")

            console.print(table)
            console.print("-" * 80)

    @staticmethod
    def _format_verdict(verdict: str) -> Text:
        v_upper = verdict.upper()
        if v_upper == "PASS":
            return Text(v_upper, style="bold green")
        if v_upper == "FAIL":
            return Text(v_upper, style="bold red")
        if v_upper == "SKIPPED":
            return Text(v_upper, style="bold yellow")
        return Text(v_upper if v_upper != "NA" else "")
