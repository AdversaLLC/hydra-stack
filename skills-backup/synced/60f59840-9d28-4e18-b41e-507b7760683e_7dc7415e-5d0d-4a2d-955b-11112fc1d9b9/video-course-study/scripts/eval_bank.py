"""Held-out multiple-choice eval for a knowledge skill.

    python3 -I eval_bank.py lint BANK.jsonl                       # refuse banks that leak the answer
    python3 -I eval_bank.py split BANK.jsonl QUESTIONS.jsonl     # strip answers for the test-taker
    python3 -I eval_bank.py grade BANK.jsonl ANSWERS.json         # ANSWERS = {"1": "B", ...}

Grading prints totals only (no question text), per domain, with docs-conflict items scored
separately: for those the course's answer key may itself be outdated.

Why lint exists: the first bank built from a course had the right answer as "B" in 58/60
questions and as the longest option in 59/60, so a no-skill control scored 60/60.
"""
import json
import sys
from collections import Counter, defaultdict


def load(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def lint(bank_path):
    """Exit 1 if the answer letter or option length gives the answer away."""
    rows = [r for r in load(bank_path) if r.get("recoverable", True)]
    n = len(rows)
    letters = Counter(r["course_answer"].strip().upper()[:1] for r in rows)
    longest = sum(max(r["options"], key=lambda o: len(r["options"][o])) == r["course_answer"].strip().upper()[:1]
                  for r in rows)
    top_letter_share = max(letters.values()) / n
    longest_share = longest / n
    print(json.dumps({"questions": n, "letters": dict(sorted(letters.items())),
                      "correct_is_longest": f"{longest}/{n}"}))
    # With 4 options, chance is 25%; allow generous slack for small banks.
    if top_letter_share > 0.40 or longest_share > 0.40:
        print("LEAKY: a test-taker can score well without knowing the material")
        sys.exit(1)
    print("ok")


def split(bank_path, out_path):
    rows = [r for r in load(bank_path) if r.get("recoverable", True)]
    with open(out_path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps({"id": r["id"], "question": r["question"], "options": r["options"]}) + "\n")
    print(f"wrote {len(rows)} questions (answers stripped)")


def grade(bank_path, answers_path):
    key = {str(r["id"]): r for r in load(bank_path) if r.get("recoverable", True)}
    answers = {str(k): str(v).strip().upper()[:1] for k, v in json.load(open(answers_path)).items()}
    by_dom = defaultdict(lambda: [0, 0])
    plain, conflict = [0, 0], [0, 0]
    for qid, r in key.items():
        ok = answers.get(qid) == r["course_answer"].strip().upper()[:1]
        bucket = conflict if r.get("docs_note") else plain
        bucket[0] += ok
        bucket[1] += 1
        by_dom[r["domain"]][0] += ok
        by_dom[r["domain"]][1] += 1
    missing = sorted(set(key) - set(answers), key=int)
    total = plain[0] + conflict[0], plain[1] + conflict[1]
    print(json.dumps({
        "total": f"{total[0]}/{total[1]}",
        "no_docs_conflict": f"{plain[0]}/{plain[1]}",
        "docs_conflict_items_matching_course_key": f"{conflict[0]}/{conflict[1]}",
        "by_domain": {d: f"{a}/{b}" for d, (a, b) in sorted(by_dom.items())},
        "unanswered": len(missing),
    }, indent=1))


if __name__ == "__main__":
    {"lint": lint, "split": split, "grade": grade}[sys.argv[1]](*sys.argv[2:])
