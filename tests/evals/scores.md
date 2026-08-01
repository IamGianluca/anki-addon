# Eval scores

run: 20260801T021231Z
model: unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL

✗ adam_duplicate_merge_1       pass@1   0%  pass^3 0  (0/3 trials)
  trial 0: ✗  (10 steps, 0 schema errors)
    failure: note 3 should not have been touched
    judge ✓ The surviving beta_2 note is a well-formed atomic flashcard: the…
  trial 1: ✗  (8 steps, 0 schema errors)
    failure: expected edits in [1, 2], got 0
    failure: fact '0.999' is missing from the notes after applying the change
             set
    judge ✗ The surviving beta_2 note is a well-formed atomic flashcard: the…
  trial 2: ✗  (6 steps, 0 schema errors)
    failure: expected edits in [1, 2], got 0
    failure: expected deletes in [1, 1], got 0
    judge ✗ The surviving beta_2 note is a well-formed atomic flashcard: the…

✓ clean_cluster_no_changes_1   pass@1 100%  pass^3 1  (3/3 trials)

✗ split_compound_note_1        pass@1  67%  pass^3 0  (2/3 trials)
  trial 0: ✗  (6 steps, 0 schema errors)
    failure: expected creates in [3, 3], got 1
    judge ✗ After the split, each resulting note tests exactly one idea.
  trial 1: ✓  (6 steps, 0 schema errors)
    judge ✓ After the split, each resulting note tests exactly one idea.
  trial 2: ✓  (8 steps, 0 schema errors)
    judge ✓ After the split, each resulting note tests exactly one idea.

summary: 1/3 tasks pass^k, mean pass@1 56%
