# Task — Run 3

## Goal
Build version 1 of this project as described in SPEC.md, including BOTH
"Decisions" sections and the "New feature" section — working code, passing
tests, pushed to GitHub, with an open pull request.

## Sources
- Use only SPEC.md and samples/inventory_sample.csv.
- "Decisions (added after Run 2)" overrides "Decisions (added after Run 1)",
  which overrides anything unclear elsewhere in the spec.
- Ignore anything else in the folder, including the feature/v1 and
  feature/v1-run2 branches.

## Output
- Start from the latest main (git pull first). Create a branch called
  feature/v1-run3 and do all work there. If it already exists, delete it
  and create it fresh from main.
- Code in app/, tests in tests/, and a README.md with install and usage steps.
- Add tests for every Decision and for the update command, including its
  error cases and the .bak backup.
- PROCESS.md: every step you took, commands you ran, decisions you made,
  and anything you were unsure about.
- PROMPTS.md: copy the full contents of this TASK.md into it, with today's
  date and the heading "Run 3".
- When done, push the branch and open a pull request into main using gh.

## Standard
I'll accept it only if:
- all tests pass
- every Decision and the update command are implemented and tested
- no test depends on the machine running it
- it follows the conventions in SPEC.md
- nothing outside the spec is built
- nothing is pushed to main
- no secrets, .env, .venv, .bak or .inventory_state files are committed

If you're unsure about anything, write it in PROCESS.md instead of guessing.