# Run 1 review

## Verified correct
- 51 tests pass (same as agent claimed)
- Invalid rows 14, 15, 16 reported with clear reasons, not dropped
- Low-stock list and summary totals correct (checked by hand)

## Problems
1. import doesn't remember the file. search/low-stock/summary silently use
   a hardcoded default sample file. Lever: instructions (my spec contradicted
   itself: "no database" vs import-then-search example).
2. Invalid-row warnings repeat on every command, noisy. Lever: instructions
   (I never said where warnings should appear).
3. summary can't be exported. Lever: instructions (ambiguous wording).
4. Duplicate SKU policy and "total items" meaning were guessed.
   Lever: instructions (never defined).
5. Stray blank line at start of import/low-stock output. Minor.
6. Machine had Python 3.10, spec needs 3.11. Lever: workspace.
   Agent handled it by finding python3.11.

## Trajectory
- PROCESS.md matched what I saw when I ran it myself.
- Agent fixed a wrong test fixture, not the code. Correct call.
- Run was interrupted once (Esc) and resumed.