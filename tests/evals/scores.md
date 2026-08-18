# Eval scores

run: 20260819T000316Z
model: unsloth/Qwen3.8-27B-GGUF:Q4_K_XL
elapsed: 7m 48s

✗ adam_duplicate_merge_1       pass@1  67%  pass^3  30%  (2/3 trials)  score 96%
  trial 1: ✗  (9 steps, score 89%)
    ✗ judge_After_the_merge,_no_two_notes_ask_the_sa
       After the proposed changes, Note 1 asks about the typical value of
       beta_2 (0.999), Note 2 asks what beta_2 is (decay rate of second moment
       estimate, with typical value 0.999), and Note 3 asks about beta_1. The
       questions are distinct — no two notes ask the same question. However,
       the second part of the assertion fails: Note 2's back contains TWO
       facts: (1) 'It controls the decay rate of the second moment estimate'
       and (2) 'Typical value: 0.999.' So Note 2 tests two facts, not exactly
       one. The agent's own rationale acknowledges Note 2 is kept 'as-is'
       despite containing both facts, which violates…

✓ clean_cluster_no_changes_1   pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ split_compound_note_1        pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ split_non_atomic_note_1      pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

summary: mean pass^k 82%, mean score 99%
