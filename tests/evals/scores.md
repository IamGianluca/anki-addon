# Eval scores

run: 20260819T123440Z
model: unsloth/Qwen3.8-27B-GGUF:Q4_K_XL
elapsed: 7m 41s

✗ adam_duplicate_merge_1       pass@1  67%  pass^3  30%  (2/3 trials)  score 93%
  trial 2: ✗  (5 steps, score 78%)
    ✗ edits
       expected edits in [1, 2], got 0
    ✗ judge_After_the_changes,_no_two_notes_ask_the_
       Since no changes were proposed, Notes 1 and 2 remain in the cluster.
       Note 1 asks 'What does beta_2 control in Adam?' and Note 2 asks 'In the
       Adam optimizer, what is beta_2?' These are functionally the same
       question about beta_2's role in Adam, violating the 'no two notes ask
       the same question' part of the assertion. Additionally, Note 2's back
       ('It controls the decay rate of the second moment estimate. Typical
       value: 0.999.') tests two facts in one card, violating the 'each
       resulting note tests exactly one fact' part. Both sub-claims of the
       assertion fail.

✓ clean_cluster_no_changes_1   pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ split_compound_note_1        pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ split_non_atomic_note_1      pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

summary: mean pass^k 82%, mean score 98%
