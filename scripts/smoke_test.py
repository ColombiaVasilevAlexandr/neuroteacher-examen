from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib import parse, request


ROOT = Path(__file__).resolve().parent.parent
API = "http://127.0.0.1:8000/api"
FRONTEND = "http://127.0.0.1:5173/"
MODULES = ("География", "История", "Конституция", "Испанский", "Культура", "Натурализация", "Микротемы")


def get_json(url: str) -> object:
    with request.urlopen(url, timeout=10) as response:
        if response.status != 200:
            raise AssertionError(f"{url} returned HTTP {response.status}")
        return json.load(response)


def get_text(url: str) -> str:
    with request.urlopen(url, timeout=10) as response:
        if response.status != 200:
            raise AssertionError(f"{url} returned HTTP {response.status}")
        return response.read().decode("utf-8")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    health = get_json(f"{API}/health")
    assert_true(isinstance(health, dict) and health.get("status") == "ok", "backend health is not ok")

    module_counts: dict[str, int] = {}
    for module in MODULES:
        url = f"{API}/questions?limit=3&topic={parse.quote(module)}"
        questions = get_json(url)
        assert_true(isinstance(questions, list), f"{module}: response is not a list")
        assert_true(len(questions) == 3, f"{module}: expected 3 questions, got {len(questions)}")
        module_counts[module] = len(questions)

    plan = get_json(f"{API}/study-plan/today?exam_date=2026-12-01")
    assert_true(isinstance(plan, dict), "study plan is not an object")
    assert_true(plan.get("total_available") == 646, f"expected 646 questions, got {plan.get('total_available')}")
    assert_true(len(plan.get("modules", [])) == 7, "study plan does not expose 7 modules")
    assert_true(bool(plan.get("audio_lesson")), "study plan does not expose audio_lesson")

    html = get_text(FRONTEND)
    for marker in ("colombia-exam-static", "/runtime-config.js", "/legacy-app.bundle.js", "/study-plan.js", "/audio-library.js"):
        assert_true(marker in html, f"frontend missing marker: {marker}")

    runtime_config = get_text(f"{FRONTEND}runtime-config.js")
    assert_true("COLOMBIA_API_BASE" in runtime_config, "runtime config does not define API base")
    assert_true("window.location.port === '5173'" in runtime_config, "runtime config does not support LAN dev port")

    audit = (ROOT / "docs" / "DATABASE_AUDIT.md").read_text(encoding="utf-8")
    assert_true("Suspicious sample count: `0`" in audit, "database audit has suspicious samples")
    if "same_as_current" in audit:
        assert_true("same_as_current `false`" not in audit, "database backup is not marked identical")

    print("Smoke test passed")
    print(f"Modules: {module_counts}")
    print(f"Plan: total={plan['total_available']} modules={len(plan['modules'])} audio={plan['audio_lesson']['id']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"Smoke test failed: {error}", file=sys.stderr)
        raise SystemExit(1)
