# Eval scores

run: 20260818T012746Z
model: unsloth/Qwen3.8-27B-GGUF:Q4_K_XL
elapsed: 8m 12s

✗ adam_duplicate_merge_1       pass@1  67%  pass^3  30%  (2/3 trials)  score 93%
  trial 1: ✗  (4 steps, score 78%)
    ✗ edits
       expected edits in [1, 2], got 0
    ✗ judge_After_the_merge,_no_two_notes_ask_the_sa
       The agent proposed no changes, meaning no merge occurred. Notes 1 and 2
       still both ask essentially the same question about beta_2's role in Adam
       ('What does beta_2 control in Adam?' vs 'In the Adam optimizer, what is
       beta_2?'). Additionally, Note 2's back contains two facts (the role AND
       the typical value 0.999), so it does not test exactly one fact. The
       assertion that 'no two notes ask the same question, and each resulting
       note tests exactly one fact' is false given the unchanged cluster.

✓ clean_cluster_no_changes_1   pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ split_compound_note_1        pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ split_non_atomic_note_1      pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

summary: mean pass^k 82%, mean score 98%
