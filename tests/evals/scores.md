# Eval scores

run: 20260816T041550Z
model: unsloth/Qwen3.8-27B-GGUF:Q4_K_XL
elapsed: 7m 18s

✗ adam_duplicate_merge_1       pass@1  33%  pass^3   4%  (1/3 trials)  score 88%
  trial 1: ✗  (8 steps, score 88%)
    ✗ judge_After_the_merge,_no_two_notes_ask_the_sa
       After the proposed changes, the three notes are: (1) 'In Adam, what is
       the default value of beta_2?' / '0.999', (2) 'In the Adam optimizer,
       what is beta_2?' / 'It controls the decay rate of the second moment
       estimate. Typical value: 0.999.', (3) 'What does beta_1 control in
       Adam?' / 'Decay rate of the first moment estimate.' No two notes ask the
       same question. However, Note 2's back still contains two facts: the role
       of beta_2 (decay rate of the second moment estimate) AND the typical
       value (0.999). The first part of the assertion (no two notes ask the
       same question) is satisfied, but the seco…
  trial 2: ✗  (5 steps, score 75%)
    ✗ edits
       expected edits in [1, 2], got 0
    ✗ judge_After_the_merge,_no_two_notes_ask_the_sa
       The agent proposed no changes at all. Notes 1 and 2 still both ask
       essentially the same question about beta_2's role in Adam ('What does
       beta_2 control in Adam?' vs 'In the Adam optimizer, what is beta_2?'),
       so two notes still ask the same question. Additionally, Note 2's back
       contains two facts (the decay-rate role AND the typical value 0.999), so
       it does not test exactly one fact. The assertion is false.

✓ clean_cluster_no_changes_1   pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ split_compound_note_1        pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ split_non_atomic_note_1      pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

summary: mean pass^k 76%, mean score 97%
