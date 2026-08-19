# Eval scores

run: 20260819T003108Z
model: unsloth/Qwen3.8-27B-GGUF:Q4_K_XL
elapsed: 9m 14s

✗ adam_duplicate_merge_1       pass@1  67%  pass^3  30%  (2/3 trials)  score 89%
  trial 1: ✗  (9 steps, score 67%)
    ✗ creates
       expected creates in [0, 0], got 1
    ✗ deletes
       expected deletes in [0, 0], got 1
    ✗ judge_The_note_that_ends_up_answering_the_shar
       The assertion claims the note answering the shared question (what beta_2
       controls) keeps its previous front AND back unchanged. Note 2 is the
       surviving note that answers this question. Its front is unchanged ('In
       the Adam optimizer, what is beta_2?'), but its back was reworded from
       'It controls the decay rate of the second moment estimate. Typical
       value: 0.999.' to 'The decay rate of the second moment estimate.' This
       is a rewording of an already-clear note (the role portion was perfectly
       stated before), and the assertion explicitly states that such rewording
       constitutes a failure. Therefore th…

✓ clean_cluster_no_changes_1   pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ split_compound_note_1        pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ split_non_atomic_note_1      pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

summary: mean pass^k 82%, mean score 97%
