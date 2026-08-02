# Eval scores

run: 20260802T013451Z
model: unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL

✗ adam_duplicate_merge_1       pass@1  20%  pass^5 0  (1/5 trials)
  trial 0: ✗  (8 steps, 0 schema errors)
    failure: expected creates in [1, 1], got 0
    judge ✗ After the merge, every resulting note tests exactly one fact.
  trial 1: ✗  (15 steps, 0 schema errors)
    failure: expected edits in [0, 1], got 2
    failure: expected creates in [1, 1], got 0
    failure: note 3 should not have been touched
    judge ✗ After the merge, every resulting note tests exactly one fact.
  trial 2: ✗  (9 steps, 0 schema errors)
    failure: expected edits in [0, 1], got 2
    failure: expected creates in [1, 1], got 0
    failure: note 3 should not have been touched
    judge ✗ After the merge, every resulting note tests exactly one fact.
  trial 3: ✗  (8 steps, 0 schema errors)
    failure: expected creates in [1, 1], got 0
    judge ✗ After the merge, every resulting note tests exactly one fact.
  trial 4: ✓  (10 steps, 0 schema errors)
    judge ✓ After the merge, every resulting note tests exactly one fact.

✓ clean_cluster_no_changes_1   pass@1 100%  pass^5 1  (5/5 trials)

✗ split_compound_note_1        pass@1   0%  pass^5 0  (0/5 trials)
  trial 0: ✗  (4 steps, 0 schema errors)
    failure: expected creates in [3, 3], got 1
    judge ✗ After the split, each resulting note tests exactly one idea.
  trial 1: ✗  (7 steps, 0 schema errors)
    failure: expected creates in [3, 3], got 1
    judge ✗ After the split, each resulting note tests exactly one idea.
  trial 2: ✗  (7 steps, 0 schema errors)
    failure: expected creates in [3, 3], got 1
    judge ✗ After the split, each resulting note tests exactly one idea.
  trial 3: ✗  (7 steps, 0 schema errors)
    failure: expected creates in [3, 3], got 1
    judge ✗ After the split, each resulting note tests exactly one idea.
  trial 4: ✗  (7 steps, 0 schema errors)
    failure: expected creates in [3, 3], got 1
    judge ✗ After the split, each resulting note tests exactly one idea.

summary: 1/3 tasks pass^k, mean pass@1 40%
