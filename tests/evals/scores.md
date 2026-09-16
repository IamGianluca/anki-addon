# Eval scores

run: 20260915T203346Z
model: qwen3.8-27b
elapsed: 1h 4m

✓ adam_duplicate_merge_1       pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ clean_cluster_no_changes_1   pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✗ clean_code_formatting_1      pass@1  67%  pass^3  30%  (2/3 trials)  score 83%
  trial 0: ✗  (13 steps, score 50%)
    ✗ empty_change_set
       expected an empty change set, got 3 proposal(s)

✓ fix_code_formatting_1        pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ fix_code_formatting_command_1 pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ fix_code_formatting_prompt_markers_1 pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ fix_math_delimiters_1        pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ fix_second_person_phrasing_1 pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ follow_instruction_convert_abbreviation_1 pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✗ recall_direction_docker_dangling_1 pass@1  67%  pass^3  30%  (2/3 trials)  score 97%
  trial 2: ✗  (8 steps, score 91%)
    ✗ fact_tagged
       fact 'tagged' is missing from the notes after applying the change set

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
       The assertion claims that 'the change set nevertheless adds cards for
       the command direction' and that 'at least one new card asks what git
       stash pop or git stash apply does.' However, the proposed changes
       section explicitly states 'No changes proposed,' and the agent's closing
       summary confirms 'No changes proposed.' No new cards were added at all.
       The assertion is factually incorrect about what the change set contains.
    ✗ judge_The_added_command_cards_are_factually_co
       The assertion states that 'the added command cards are factually correct
       and keep the two similar commands distinguishable.' However, the
       proposed changes section explicitly says 'No changes proposed.' No cards
       were added for `git stash pop` or `git stash apply`. The agent's closing
       summary even incorrectly claims there is 'no canonical confusable pair
       of `git stash` that would warrant additional cards,' which is factually
       wrong since `git stash pop` vs `git stash apply` is a well-known
       confusable pair. Since no cards were added, the assertion about their
       correctness and distinguishability is …
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
       proposed changes explicitly state 'No changes proposed,' and the agent's
       closing summary confirms 'No changes proposed.' No new cards were added
       at all, so the assertion is factually incorrect about what the agent
       did.
    ✗ judge_The_added_command_cards_are_factually_co
       The agent proposed no changes at all — no new command cards were added
       for `git stash pop` or `git stash apply`. The assertion specifically
       evaluates 'the added command cards' and their factual correctness and
       distinguishability. Since no such cards exist in the proposed changes,
       the assertion cannot be satisfied.
  trial 2: ✗  (6 steps, score 44%)
    ✗ creates
       expected creates in [2, 2], got 0
    ✗ fact_pop
       fact 'pop' is missing from the notes after applying the change set
    ✗ fact_apply
       fact 'apply' is missing from the notes after applying the change set
    ✗ judge_The_seed_note_tests_only_the_definition_
       The assertion claims that the change set adds at least one new card
       asking about `git stash pop` or `git stash apply`. However, the proposed
       changes explicitly state 'No changes proposed,' and the agent's summary
       confirms no cards were added. The assertion is directly contradicted by
       the evidence shown.
    ✗ judge_The_added_command_cards_are_factually_co
       The agent proposed no changes at all. The assertion presupposes that
       command cards for `git stash pop` and `git stash apply` were added, but
       the 'Proposed changes' section explicitly states 'No changes proposed.'
       Since no such cards exist in the output, the assertion that they are
       factually correct, distinguishable, and unbundled cannot be satisfied.

✓ split_compound_note_1        pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ split_non_atomic_note_1      pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ split_topic_label_grpc_1     pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

formatting: ✗ 2 violation(s) across 45 trials (raw_newline: 2)
  fix_code_formatting_1        trial 1: raw_newline [back] ```lua\n{name = "Ada"}\n```
  fix_code_formatting_1        trial 1: raw_newline [back] ```bash\nlua game.lua\n```
summary: mean pass^k 84%, mean score 95%
