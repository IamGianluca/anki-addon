# Eval scores

run: 20260816T033738Z
model: unsloth/Qwen3.8-27B-GGUF:Q4_K_XL
elapsed: 7m 6s

✗ adam_duplicate_merge_1       pass@1  67%  pass^3  30%  (2/3 trials)  score 93%
  trial 1: ✗  (4 steps, score 78%)
    ✗ edits
       expected edits in [1, 2], got 0
    ✗ judge_After_the_merge,_no_two_notes_ask_the_sa
       The agent proposed no changes, so no merge occurred. In the unchanged
       cluster, Note 1 ('What does beta_2 control in Adam?') and Note 2 ('In
       the Adam optimizer, what is beta_2?') still ask the same question about
       beta_2's role in Adam. Therefore, the condition 'no two notes ask the
       same question' is violated. Additionally, Note 2's back contains two
       facts (the role AND the typical value 0.999), so the condition 'each
       resulting note tests exactly one fact' is also violated. The assertion
       is false.

✓ clean_cluster_no_changes_1   pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ split_compound_note_1        pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ split_non_atomic_note_1      pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

summary: mean pass^k 82%, mean score 98%
