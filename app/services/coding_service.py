from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

from app.services.json_utils import parse_json_object
from app.services.llm_client import call_llm


async def generate_coding_problem(resume: dict, jd: dict, difficulty: str = "junior", language: str = "cpp") -> dict:
    system = "You generate concise interview coding problems. Return only valid JSON."
    prompt = f"""
Create one LeetCode-style coding problem for a {difficulty} candidate.
Target language: {language}.
The candidate must submit a COMPLETE C++17 program that reads from stdin and writes to stdout.

Use the resume and job description context when useful.

RESUME_JSON:
{json.dumps(resume)}

JD_JSON:
{json.dumps(jd)}

Return JSON with:
{{
  "id": "string",
  "category": "dsa",
  "title": "string",
  "text": "problem statement",
  "constraints": ["string"],
  "examples": [{{"input": "string", "output": "string", "explanation": "string"}}],
  "sample_tests": [{{"stdin": "string", "expected_stdout": "string"}}],
  "expected_points": ["data structure", "complexity", "edge cases"],
  "starter_code": "complete C++17 program with TODO comments"
}}
"""
    fallback = {
        "id": str(uuid.uuid4()),
        "category": "dsa",
        "title": "Two Sum Variant",
        "text": "Read n, then n integers, then target. Print two zero-based indices whose values sum to target, or -1 -1 if no pair exists.",
        "constraints": ["2 <= n <= 100000", "Input values fit in signed 32-bit integers."],
        "examples": [{"input": "4\n2 7 11 15\n9", "output": "0 1", "explanation": "2 + 7 = 9"}],
        "sample_tests": [
            {"stdin": "4\n2 7 11 15\n9\n", "expected_stdout": "0 1"},
            {"stdin": "5\n1 4 6 8 10\n14\n", "expected_stdout": "2 3"},
        ],
        "expected_points": ["hash map", "O(n) time", "edge cases"],
        "starter_code": "#include <bits/stdc++.h>\nusing namespace std;\n\nint main() {\n    ios::sync_with_stdio(false);\n    cin.tie(nullptr);\n\n    int n;\n    cin >> n;\n    vector<int> nums(n);\n    for (int i = 0; i < n; i++) cin >> nums[i];\n    int target;\n    cin >> target;\n\n    // TODO: implement an O(n) hash-map solution.\n    cout << -1 << \" \" << -1 << \"\\n\";\n    return 0;\n}\n",
    }
    data = parse_json_object(await call_llm(system, prompt), fallback)
    data.setdefault("id", str(uuid.uuid4()))
    data.setdefault("category", "dsa")
    data.setdefault("examples", fallback["examples"])
    data.setdefault("sample_tests", data.get("examples") or fallback["sample_tests"])
    data.setdefault("starter_code", fallback["starter_code"])
    return data


async def evaluate_code_answer(
    problem: dict,
    code: str,
    spoken_answer: str = "",
    complexity_claim: str | None = None,
    sample_runs: list[dict] | None = None,
) -> dict:
    system = "You are a senior DSA interviewer. Return only valid JSON."
    prompt = f"""
Evaluate this C++ coding interview submission. Do not execute the code.

PROBLEM:
{json.dumps(problem)}

CODE:
{code}

SPOKEN_EXPLANATION:
{spoken_answer}

CANDIDATE_COMPLEXITY_CLAIM:
{complexity_claim or "Not provided"}

SAMPLE_RUN_HISTORY:
{json.dumps(sample_runs or [])}

Return JSON:
{{
  "code_score": number between 0 and 1,
  "correctness_notes": ["string"],
  "complexity": "string",
  "edge_cases": ["string"],
  "followup_topics": ["string"],
  "complexity_questions": ["specific follow-up questions about time complexity, space complexity, optimization, and failed sample tests"],
  "concise_feedback": "2-3 sentences"
}}

Evaluation rules:
- If the candidate did not provide time/space complexity, add at least one complexity question.
- If any sample run failed, add a follow-up about the failing case.
- If all samples passed, still ask about hidden edge cases and asymptotic complexity.
"""
    fallback = {
        "code_score": 0.0,
        "correctness_notes": ["Code review unavailable because the model returned invalid JSON."],
        "complexity": "Unknown",
        "edge_cases": [],
        "followup_topics": [],
        "complexity_questions": [],
        "concise_feedback": "Code evaluation could not be completed.",
    }
    result = parse_json_object(await call_llm(system, prompt), fallback)
    result["code"] = code
    return result


def run_sample_tests(problem: dict, code: str, timeout_seconds: int = 3, compile_timeout_seconds: int = 15) -> dict:
    """
    Compile and run a complete C++17 program against problem sample tests.
    This is intentionally timeout-bound and uses a temporary directory.
    """
    compiler = os.getenv("CXX_COMPILER") or shutil.which("g++")
    if not compiler:
        return {
            "ok": False,
            "status": "compiler_unavailable",
            "message": "g++ was not found. Install MinGW/MSYS2 g++ or set CXX_COMPILER.",
            "tests": [],
            "passed": 0,
            "total": len(problem.get("sample_tests") or []),
            "elapsed_ms": 0,
        }

    tests = problem.get("sample_tests") or []
    if not tests:
        return {
            "ok": False,
            "status": "no_sample_tests",
            "message": "This problem does not define executable sample tests.",
            "tests": [],
            "passed": 0,
            "total": 0,
            "elapsed_ms": 0,
        }

    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="mock_interview_cpp_") as tmp:
        tmp_path = Path(tmp)
        source = tmp_path / "main.cpp"
        exe = tmp_path / ("main.exe" if os.name == "nt" else "main")
        source.write_text(code, encoding="utf-8")

        compile_cmd = [
            compiler,
            "-std=c++17",
            "-O2",
            "-pipe",
            str(source),
            "-o",
            str(exe),
        ]
        try:
            compile_result = subprocess.run(
                compile_cmd,
                capture_output=True,
                text=True,
                timeout=compile_timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            return {
                "ok": False,
                "status": "compile_timeout",
                "message": "Compilation timed out.",
                "compiler_stderr": "Compilation exceeded the time limit.",
                "tests": [],
                "passed": 0,
                "total": len(tests),
                "elapsed_ms": round((time.perf_counter() - started) * 1000),
            }
        if compile_result.returncode != 0:
            return {
                "ok": False,
                "status": "compile_error",
                "message": "Compilation failed.",
                "compiler_stderr": compile_result.stderr[-4000:],
                "tests": [],
                "passed": 0,
                "total": len(tests),
                "elapsed_ms": round((time.perf_counter() - started) * 1000),
            }

        results = []
        passed = 0
        for index, test in enumerate(tests, start=1):
            test_started = time.perf_counter()
            stdin = str(test.get("stdin", test.get("input", "")))
            expected_stdout = str(test.get("expected_stdout", test.get("output", "")))
            try:
                run_result = subprocess.run(
                    [str(exe)],
                    input=stdin,
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds,
                )
                actual = normalize_output(run_result.stdout)
                expected = normalize_output(expected_stdout)
                ok = run_result.returncode == 0 and actual == expected
                passed += 1 if ok else 0
                results.append({
                    "index": index,
                    "ok": ok,
                    "stdin": stdin,
                    "expected_stdout": expected,
                    "actual_stdout": actual,
                    "stderr": run_result.stderr[-1000:],
                    "returncode": run_result.returncode,
                    "elapsed_ms": round((time.perf_counter() - test_started) * 1000),
                })
            except subprocess.TimeoutExpired:
                results.append({
                    "index": index,
                    "ok": False,
                    "stdin": stdin,
                    "expected_stdout": normalize_output(expected_stdout),
                    "actual_stdout": "",
                    "stderr": "Time limit exceeded.",
                    "returncode": None,
                    "elapsed_ms": timeout_seconds * 1000,
                })

    return {
        "ok": passed == len(tests),
        "status": "passed" if passed == len(tests) else "failed",
        "message": f"{passed}/{len(tests)} sample tests passed.",
        "tests": results,
        "passed": passed,
        "total": len(tests),
        "elapsed_ms": round((time.perf_counter() - started) * 1000),
    }


def normalize_output(value: str) -> str:
    lines = [line.rstrip() for line in (value or "").replace("\r\n", "\n").split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines).strip()
