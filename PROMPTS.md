# Prompts

The prompts that shaped this repository, taken from the Claude Code session transcripts. Times are UTC. Quotes are trimmed and edited for spelling and tone; the meaning is unchanged. Prompts about other topics (interview logistics, other repositories) are left out.

Involvement: Claude Code proposed the project and wrote the code. I chose its scope, reviewed it, then reread `checks.py` and `bench.py` line by line and had them changed. I can explain `trajectories.py` in words but not its math.

## 7 November 2026: proposal and build

- 12:17 Starting prompt, about preparing a technical interview on sandbox evasion: "is it worth making a presentation or an HTML file? Find advice on the web." Claude suggested the PoC itself, as an optional item in its plan.
- 12:28 Answer to Claude's scoping question, "include the optional Windows recorder that adds your own real mouse as a human baseline?": "Yes, with recorder".
- 12:39 Plan rejected with: "Is it worth doing the PoC with the Glassdoor information gathered?"
- 12:40 Plan approved. Claude wrote the code, tests and CI. First commits at 12:45.
- 12:48 "Code review the PoC." The review found 10 defects, including that `GetLastInputInfo` ignores `SetCursorPos`, which made the `jumps` row wrong.
- 13:08 After recording my own mouse: "I had to read the instructions before moving my mouse", then "add a timer before the recording starts".
- 13:13 "'Use the mouse as usual' should be the first thing printed."
- 13:22 On the recorded trace failing the 2 s check: "Nobody moves their mouse every 2 seconds; I was reading emails during the recording."

## 8 November 2026: reading the code

- 11:18 "Add a hard rule to AGENTS.md against list comprehensions such as `[(int(r["t_ms"]), int(r["x"]), int(r["y"])) for r in csv.DictReader(f)]`; they are hard to read."
- 11:26 "What does `bisect_right` on line 23 do?"
- 11:37 "Is `Sequence` like a linked list?", then "why is it typed `Sequence`?"
- 11:39 "Change it to `list`. What does the star in `math.hypot(*u) * math.hypot(*v)` do?"
- 11:51 "What is LummaC2? What is `pairwise`? I want to understand how `looks_human` works."
- 11:57 "What does `GetLastInputInfo` do? I do not understand the `LASTINPUTINFO` struct."
- 12:01 "I understand `checks.py`, but `bench.py` is less clear."
- 12:03 "Add blank lines to separate logical steps, for example between lines 128 and 129, everywhere."
- 12:10 "Add a one-line docstring to each function, and add that rule to AGENTS.md."
- 12:16 "Does a leading underscore mean a private function?"
- 12:20 "What does `yield` do?"
- 12:24 "How is `LASTINPUTINFO` filled in?", then "so we model the behaviour of `GetLastInputInfo`?"
- 12:25 "I read `checks.py` and `bench.py`; I think I understand them."
- 12:30 Explaining it back: "since it models an auto-clicker and not a real keyboard or mouse, `GetLastInputInfo` does not register it."
- 12:34 "`looks_human` models the LummaC2 check: no deviation above 45 degrees over 5 points. I am not sure why they picked that threshold."
- 12:50 "I do not understand the math behind the linear and Bezier generators."
- 17:10 "My human recording makes sense while the cursor is idle; LummaC2 only needs one valid set of readings to detonate, right?"
