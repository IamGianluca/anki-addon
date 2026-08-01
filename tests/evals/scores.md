# Eval scores

run: 20260801T023745Z
model: unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL

✗ adam_duplicate_merge_1       pass@1  20%  pass^5 0  (1/5 trials)
  trial 0: ✗  (9 steps, 0 schema errors)
    failure: expected edits in [1, 2], got 0
    failure: fact '0.999' is missing from the notes after applying the change
             set
    judge ✗ The surviving beta_2 note is a well-formed atomic flashcard: the…
  trial 1: ✗  (6 steps, 0 schema errors)
    failure: expected edits in [1, 2], got 0
    failure: fact '0.999' is missing from the notes after applying the change
             set
    judge ✗ The surviving beta_2 note is a well-formed atomic flashcard: the…
  trial 2: ✗  (9 steps, 0 schema errors)
    judge ✗ The surviving beta_2 note is a well-formed atomic flashcard: the…
  trial 3: ✗  (9 steps, 0 schema errors)
    failure: expected edits in [1, 2], got 0
    failure: fact '0.999' is missing from the notes after applying the change
             set
    judge ✓ The surviving beta_2 note is a well-formed atomic flashcard: the…
  trial 4: ✓  (9 steps, 0 schema errors)
    judge ✓ The surviving beta_2 note is a well-formed atomic flashcard: the…

✓ clean_cluster_no_changes_1   pass@1 100%  pass^5 1  (5/5 trials)

✗ split_compound_note_1        pass@1   0%  pass^5 0  (0/5 trials)
  trial 0: ✗  (8 steps, 0 schema errors)
    failure: expected creates in [3, 3], got 1
    judge ✗ After the split, each resulting note tests exactly one idea.
  trial 1: ✗  (6 steps, 0 schema errors)
    failure: expected creates in [3, 3], got 1
    judge ✗ After the split, each resulting note tests exactly one idea.
  trial 2: ✗  (7 steps, 0 schema errors)
    failure: expected creates in [3, 3], got 2
    judge ✗ After the split, each resulting note tests exactly one idea.
  trial 3: ✗  (6 steps, 0 schema errors)
    failure: expected creates in [3, 3], got 1
    judge ✗ After the split, each resulting note tests exactly one idea.
  trial 4: ✗  (7 steps, 0 schema errors)
    failure: expected creates in [3, 3], got 1
    judge ✗ After the split, each resulting note tests exactly one idea.

summary: 1/3 tasks pass^k, mean pass@1 40%
