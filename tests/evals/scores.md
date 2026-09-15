# Eval scores

run: 20260915T154501Z
model: qwen3.8-27b
elapsed: 1h 4m

✓ adam_duplicate_merge_1       pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ clean_cluster_no_changes_1   pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✗ clean_code_formatting_1      pass@1  67%  pass^3  30%  (2/3 trials)  score 83%
  trial 0: ✗  (10 steps, score 50%)
    ✗ empty_change_set
       expected an empty change set, got 1 proposal(s)

✓ fix_code_formatting_1        pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ fix_code_formatting_command_1 pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ fix_code_formatting_prompt_markers_1 pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ fix_math_delimiters_1        pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ fix_second_person_phrasing_1 pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ follow_instruction_convert_abbreviation_1 pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ recall_direction_docker_dangling_1 pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ recall_direction_git_stash_1 pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✗ recall_direction_git_stash_derive_1 pass@1   0%  pass^3   0%  (0/3 trials)  score 44%
  trial 0: ✗  (7 steps, score 44%)
    ✗ creates
       expected creates in [2, 2], got 0
    ✗ fact_pop
       fact 'pop' is missing from the notes after applying the change set
    ✗ fact_apply
       fact 'apply' is missing from the notes after applying the change set
    ✗ judge_The_seed_note_tests_only_the_definition_
       The assertion claims that the change set adds at least one new card
       testing the command direction (git stash pop or git stash apply).
       However, the proposed changes explicitly state 'No changes proposed,'
       and the agent's closing summary confirms no changes were made. No new
       cards were added, so the assertion is factually incorrect about what the
       change set contains.
    ✗ judge_The_added_command_cards_are_factually_co
       The assertion claims that 'added command cards' exist, are factually
       correct, and keep the two commands distinguishable. However, the
       proposed changes section explicitly states 'No changes proposed,' and
       the agent's summary confirms no cards were added. Since no cards were
       added at all, the assertion's premise is entirely unmet. The agent
       failed to derive the missing command-direction cards for `git stash pop`
       and `git stash apply`, so the assertion cannot pass.
  trial 1: ✗  (6 steps, score 44%)
    ✗ creates
       expected creates in [2, 2], got 0
    ✗ fact_pop
       fact 'pop' is missing from the notes after applying the change set
    ✗ fact_apply
       fact 'apply' is missing from the notes after applying the change set
    ✗ judge_The_seed_note_tests_only_the_definition_
       The assertion claims that the change set adds cards for the command
       direction (e.g., asking what `git stash pop` or `git stash apply` does).
       However, the proposed changes explicitly state 'No changes proposed' and
       the agent's closing summary confirms no cards were added. The change set
       is empty, so no new cards for the command direction were added.
    ✗ judge_The_added_command_cards_are_factually_co
       The agent proposed no changes at all, as stated both in the 'Proposed
       changes' section ('No changes proposed') and the closing summary. Since
       no command cards were added, the assertion that 'the added command cards
       are factually correct and keep the two similar commands distinguishable'
       cannot be satisfied. There are no such cards to evaluate. The agent
       failed to fulfill the core requirement of proposing active-recall cards
       for the git stash pop vs. git stash apply distinction.
  trial 2: ✗  (5 steps, score 44%)
    ✗ creates
       expected creates in [2, 2], got 0
    ✗ fact_pop
       fact 'pop' is missing from the notes after applying the change set
    ✗ fact_apply
       fact 'apply' is missing from the notes after applying the change set
    ✗ judge_The_seed_note_tests_only_the_definition_
       The proposed changes explicitly state 'No changes proposed.' The agent's
       closing summary confirms it made no additions. The assertion claims that
       'the change set nevertheless adds cards for the command direction' and
       that 'at least one new card asks what git stash pop or git stash apply
       does.' This is directly contradicted by the fact that no changes were
       proposed at all. No new cards exist in the change set.
    ✗ judge_The_added_command_cards_are_factually_co
       The agent proposed no changes at all — no cards were added. The
       assertion references 'the added command cards' and evaluates their
       factual correctness and distinguishability, but since no cards were
       added, there are no added command cards to assess. The assertion
       presupposes the existence of cards that do not exist in the proposed
       changes. The agent failed to fulfill the task requirement to derive and
       propose the missing command-direction cards for git stash pop and git
       stash apply.

✓ split_compound_note_1        pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ split_non_atomic_note_1      pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ split_topic_label_grpc_1     pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

formatting: ✓ no violations across 45 trials
summary: mean pass^k 89%, mean score 95%
