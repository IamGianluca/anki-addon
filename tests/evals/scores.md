# Eval scores

run: 20260911T025608Z
model: qwen3.8-27b
elapsed: 1h 9m

✓ adam_duplicate_merge_1       pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ clean_cluster_no_changes_1   pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ clean_code_formatting_1      pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ fix_code_formatting_1        pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ fix_code_formatting_command_1 pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ fix_code_formatting_prompt_markers_1 pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✗ fix_math_delimiters_1        pass@1  67%  pass^3  30%  (2/3 trials)  score 98%
  trial 0: ✗  (10 steps, score 93%)
    ✗ judge_Every_math_expression_in_the_change_set_
       Checking each formula in the change set for content preservation: Note 1
       (sine) and the new cosine note preserve their content exactly. Note 3
       (secant) preserves its content exactly. However, for Note 2 (tangent),
       the original back is `$$\tan(2x) = \frac{2 \tan x}{1 - \tan^2 x}$$`
       where the content between the `$$` delimiters is `\tan(2x) = ...`. The
       proposed new back is `\[tan(2x) = \frac{2 \tan x}{1 - \tan^2 x}\]` where
       the content between the `\[` and `\]` delimiters is `tan(2x) = ...`. The
       first `\tan` has lost its backslash, becoming plain `tan`. This is
       confirmed by comparison with Note …

✗ fix_second_person_phrasing_1 pass@1  67%  pass^3  30%  (2/3 trials)  score 97%
  trial 1: ✗  (15 steps, score 92%)
    ✗ creates
       expected creates in [0, 0], got 1

✓ follow_instruction_convert_abbreviation_1 pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ recall_direction_docker_dangling_1 pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ recall_direction_git_stash_1 pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✗ recall_direction_git_stash_derive_1 pass@1   0%  pass^3   0%  (0/3 trials)  score 44%
  trial 0: ✗  (6 steps, score 44%)
    ✗ creates
       expected creates in [2, 2], got 0
    ✗ fact_pop
       fact 'pop' is missing from the notes after applying the change set
    ✗ fact_apply
       fact 'apply' is missing from the notes after applying the change set
    ✗ judge_The_seed_note_tests_only_the_definition_
       The assertion claims that the change set adds cards for the command
       direction (git stash pop or git stash apply). However, the proposed
       changes explicitly state 'No changes proposed,' and the agent's closing
       summary confirms no changes were made. No new cards were added
       whatsoever, so the assertion is factually incorrect.
    ✗ judge_The_added_command_cards_are_factually_co
       The proposed changes section explicitly states 'No changes proposed.'
       The agent added no command cards whatsoever. The assertion claims that
       'added command cards' are factually correct and distinguishable, but no
       such cards exist in the proposed changes. The assertion's subject does
       not exist, so it cannot pass.
  trial 1: ✗  (7 steps, score 44%)
    ✗ creates
       expected creates in [2, 2], got 0
    ✗ fact_pop
       fact 'pop' is missing from the notes after applying the change set
    ✗ fact_apply
       fact 'apply' is missing from the notes after applying the change set
    ✗ judge_The_seed_note_tests_only_the_definition_
       The assertion claims that the change set adds at least one new card
       asking what `git stash pop` or `git stash apply` does. However, the
       proposed changes section explicitly states 'No changes proposed,' and
       the agent's closing summary confirms 'No changes proposed.' No new cards
       of any kind were added. The assertion is factually incorrect about what
       the change set contains.
    ✗ judge_The_added_command_cards_are_factually_co
       The assertion claims that added command cards are factually correct and
       keep git stash pop and git stash apply distinguishable. However, the
       proposed changes state 'No changes proposed,' and the agent's closing
       summary confirms no cards were added. There are no added command cards
       to evaluate. The assertion presupposes the existence of cards that were
       never created, so it cannot be satisfied.
  trial 2: ✗  (6 steps, score 44%)
    ✗ creates
       expected creates in [2, 2], got 0
    ✗ fact_pop
       fact 'pop' is missing from the notes after applying the change set
    ✗ fact_apply
       fact 'apply' is missing from the notes after applying the change set
    ✗ judge_The_seed_note_tests_only_the_definition_
       The assertion claims that the change set adds cards for the command
       direction (git stash pop or git stash apply). However, the proposed
       changes explicitly state 'No changes proposed.' No new cards were added
       at all. The assertion is factually incorrect about what the agent did.
    ✗ judge_The_added_command_cards_are_factually_co
       The assertion presumes that command cards for 'git stash pop' and 'git
       stash apply' were added and evaluates their factual correctness and
       distinguishability. However, the proposed changes explicitly state 'No
       changes proposed,' and the agent's closing summary confirms no cards
       were added. There are no 'added command cards' to evaluate. The
       assertion's premise is contradicted by the shown output.

✓ split_compound_note_1        pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ split_non_atomic_note_1      pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

formatting: ✓ no violations across 42 trials
summary: mean pass^k 83%, mean score 96%
