# Eval scores

run: 20260731T023243Z
model: unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL

✗ adam_duplicate_merge_1       pass@1   0%  pass^3 0  (0/3 trials)
  trial 0: ✗  (10 steps, 0 schema errors)
    failure: note 3 should not have been touched
    failure: fact 'second moment' is missing from the notes after applying the
             change set
    failure: fact 'first moment' is missing from the notes after applying the
             change set
    judge ✓ The surviving beta_2 note is a well-formed atomic flashcard: the…
  trial 1: ✗  (12 steps, 0 schema errors)
    failure: note 3 should not have been touched
    judge ✓ The surviving beta_2 note is a well-formed atomic flashcard: the…
  trial 2: ✗  (9 steps, 0 schema errors)
    failure: note 3 should not have been touched
    judge ✗ The surviving beta_2 note is a well-formed atomic flashcard: the…

✗ clean_cluster_no_changes_1   pass@1   0%  pass^3 0  (0/3 trials)
  trial 0: ✗  (10 steps, 0 schema errors)
    failure: expected an empty change set, got 2 proposal(s)
  trial 1: ✗  (10 steps, 0 schema errors)
    failure: expected an empty change set, got 3 proposal(s)
  trial 2: ✗  (12 steps, 0 schema errors)
    failure: expected an empty change set, got 3 proposal(s)

✗ split_compound_note_1        pass@1   0%  pass^3 0  (0/3 trials)
  trial 0: ✗  (11 steps, 0 schema errors)
    failure: expected edits in [1, 1], got 2
    failure: note 2 should not have been touched
    judge ✓ After the split, each resulting note tests exactly one idea.
  trial 1: ✗  (8 steps, 0 schema errors)
    failure: expected edits in [1, 1], got 2
    failure: note 2 should not have been touched
    judge ✓ After the split, each resulting note tests exactly one idea.
  trial 2: ✗  (9 steps, 0 schema errors)
    failure: expected edits in [1, 1], got 2
    failure: note 2 should not have been touched
    judge ✗ After the split, each resulting note tests exactly one idea.

summary: 0/3 tasks pass^k, mean pass@1 0%
