# Eval scores

run: 20260808T005556Z
model: unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL
elapsed: 20m 16s

✗ adam_duplicate_merge_1       pass@1  20%  pass^5   0%  (1/5 trials)  score 78%
  trial 0: ✗  (10 steps, score 67%)
    ✗ creates
       expected creates in [0, 0], got 1
    ✗ deletes
       expected deletes in [0, 0], got 1
    ✗ must_not_touch_3
       note 3 should not have been touched
  trial 1: ✗  (10 steps, score 67%)
    ✗ deletes
       expected deletes in [0, 0], got 1
    ✗ fact_second moment
       fact 'second moment' is missing from the notes after applying the change
       set
    ✗ judge_After_the_merge,_no_two_notes_ask_the_sa
       The agent deleted Note 1 (the role/definition card for beta_2) and
       edited Note 2 to become a typical-value card. This leaves the cluster
       without any note testing beta_2's role/definition, violating the
       instruction to merge them into one role card. Consequently, the
       resulting notes do not fully cover the intended facts, and the assertion
       that each resulting note tests exactly one fact in a proper merge is
       false.
  trial 2: ✗  (8 steps, score 78%)
    ✗ creates
       expected creates in [0, 0], got 1
    ✗ deletes
       expected deletes in [0, 0], got 1
  trial 4: ✗  (9 steps, score 78%)
    ✗ edits
       expected edits in [1, 2], got 3
    ✗ must_not_touch_3
       note 3 should not have been touched

✓ clean_cluster_no_changes_1   pass@1 100%  pass^5 100%  (5/5 trials)  score 100%

✓ split_compound_note_1        pass@1 100%  pass^5 100%  (5/5 trials)  score 100%

✓ split_non_atomic_note_1      pass@1 100%  pass^5 100%  (5/5 trials)  score 100%

summary: mean pass^k 75%, mean score 94%
