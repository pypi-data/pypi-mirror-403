from textual.screen import ModalScreen
from textual.widgets import RichLog, Static, Footer
from algoflex.questions import questions
from algoflex.db import get_db
from algoflex.utils import fmt_secs
from tinydb import Query
import tempfile
import subprocess
import os
import time

KV = Query()


class ResultModal(ModalScreen):
    BINDINGS = [("s", "dismiss", "dismiss")]
    DEFAULT_CSS = """
    ResultModal {
        &>* {
            max-width: 90;
        }
        align: center middle;
        RichLog {
            width: 1fr;
            height: 12;
            padding: 1 0;
            padding-left: 2;
            overflow-x: auto;
            background: $boost;
        }
    }
    """
    TEST_CODE = """
import sys

def run_tests():
    total, passed = len(test_cases), 0
    for i, [input, expected] in enumerate(test_cases):
        try:
            if input == expected:
                print(f"[green][b]✓[/] test case {i+1} passed![/]")
                passed += 1
            else:
                print(f"[red][b]x[/] test case {i+1} failed![/]\\n\\t[b]got[/]: [red]{input}[/]\\n\\t[b]expected[/]: [green]{expected}[/]")
                return 1
        except Exception as e:
            print(f"[red][b]x[/] test case {i+1} error![/]\\n\\t[b]error[/]: {e}")
            return 1
    if passed == total:
        print(f"\\n{passed}/{total} passed!")
        return 0
    if passed < total:
        print(f"\\n {total - passed} failing.")
    return 1

if __name__ == "__main__":
    sys.exit(run_tests())
    """

    def __init__(self, problem_id, user_code, elapsed, best):
        super().__init__()
        self.problem_id = problem_id
        self.user_code = user_code
        self.elapsed = elapsed
        self.best = best

    def on_mount(self):
        self.run_user_code()

    def compose(self):
        yield RichLog(markup=True, wrap=True, max_lines=1_000)
        yield Footer()

    def run_user_code(self):
        attempts, passed, now = get_db(), False, time.time()
        user_code = self.user_code.strip()
        output_log = self.query_one(RichLog)
        question = questions.get(self.problem_id, {})
        test_cases = question.get("test_cases", [])
        test_code = question.get("test_code", self.TEST_CODE)
        full_code = f"{user_code}\n\n{test_cases}\n\n{test_code}"
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".py", mode="w+", encoding="utf-8"
        ) as tmp_file:
            tmp_file.write(full_code)
        try:
            result = subprocess.run(
                ["python", tmp_file.name], capture_output=True, text=True, timeout=9
            )
            if result.stdout:
                output_log.write(result.stdout, animate=True)
            if result.stderr:
                return output_log.write(result.stderr, animate=True)
            if result.returncode == 0:
                passed = True
                if not self.best or self.elapsed < self.best:
                    self.new_best()
        except subprocess.TimeoutExpired:
            output_log.write(
                "[red]Execution timed out[/]\\n\\tYour solution must run within 9 seconds"
            )
        except Exception as e:
            return output_log.write(f"[red]Error running code[/]\\n\\t{e}")
        finally:
            os.remove(tmp_file.name)

        attempts.insert(
            {
                "problem_id": self.problem_id,
                "passed": passed,
                "elapsed": self.elapsed,
                "created_at": now,
                "code": user_code if passed else "",
            },
        )

    def new_best(self):
        widget = Static(f"[b]New best time! --> {fmt_secs(self.elapsed)}[/]")
        widget.styles.height = 3
        widget.styles.content_align = ("center", "middle")
        widget.styles.background = "#303134"
        self.mount(widget)
