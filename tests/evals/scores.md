# Eval scores

run: 20260830T201950Z
model: unsloth/Qwen3.8-27B-GGUF:Q4_K_XL
elapsed: 22m 14s

✓ adam_duplicate_merge_1       pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ clean_cluster_no_changes_1   pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✗ fix_math_delimiters_1        pass@1  67%  pass^3  30%  (2/3 trials)  score 95%
  trial 2: ✗  (8 steps, score 86%)
    ✗ edits
       expected edits in [3, 3], got 2
    ✗ must_touch_3
       note 3 should have been edited or deleted

✓ fix_second_person_phrasing_1 pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ follow_instruction_convert_abbreviation_1 pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ split_compound_note_1        pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ split_non_atomic_note_1      pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

formatting: ✓ no violations across 21 trials
summary: mean pass^k 90%, mean score 99%
