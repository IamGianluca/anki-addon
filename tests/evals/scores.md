# Eval scores

run: 20260829T191537Z
model: unsloth/Qwen3.8-27B-GGUF:Q4_K_XL
elapsed: 18m 22s

✓ adam_duplicate_merge_1       pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ clean_cluster_no_changes_1   pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✗ fix_math_delimiters_1        pass@1  33%  pass^3   4%  (1/3 trials)  score 95%
  trial 1: ✗  (9 steps, score 92%)
    ✗ judge_Across_the_whole_change_set,_every_math_
       The assertion states that "$...$ converted to \(\) and $$...$$ to \[\]
       (inline stays inline, block stays block)." In Note 1, the original math
       used $...$ (inline delimiters). Per the rule, these should have been
       converted to \(...\) (inline). However, the agent converted them to
       \[...\] (block), changing the inline expressions to block expressions.
       The same issue applies to the newly created cosine note, where the
       content originally carried as $...$ (inline) was placed in \[...\]
       (block). This violates the "inline stays inline" constraint stated in
       the assertion. The tangent note (Note 2) corr…
  trial 2: ✗  (10 steps, score 92%)
    ✗ judge_Across_the_whole_change_set,_every_math_
       The assertion requires that $...$ (inline) be converted to \(...\)
       (inline) and $$...$$ (block) be converted to \[...\] (block), preserving
       the inline/block distinction. In the change set, Note 2 correctly
       converts $$...$$ to \[...\] (block → block), but Note 1's two $...$
       inline expressions are converted to \[...\] (block mode) in both the
       edited note and the newly created note. The rationale explicitly says
       'block mode, since each formula is the entire answer,' which is a
       deliberate style change, not a mechanical inline-to-inline conversion.
       The formulas themselves are unchanged, but the del…

✓ fix_second_person_phrasing_1 pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ follow_instruction_convert_abbreviation_1 pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ split_compound_note_1        pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ split_non_atomic_note_1      pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

formatting: ✓ no violations across 21 trials
summary: mean pass^k 86%, mean score 99%
