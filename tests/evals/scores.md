# Eval scores

run: 20260920T134635Z
model: qwen3.8-27b
elapsed: 1h 13m

✓ adam_duplicate_merge_1       pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ clean_cluster_no_changes_1   pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✗ clean_code_formatting_1      pass@1  67%  pass^3  30%  (2/3 trials)  score 83%
  trial 0: ✗  (15 steps, score 50%)
    ✗ empty_change_set
       expected an empty change set, got 3 proposal(s)

✓ fix_code_formatting_1        pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✗ fix_code_formatting_command_1 pass@1  67%  pass^3  30%  (2/3 trials)  score 92%
  trial 1: ✗  (11 steps, score 75%)
    ✗ creates
       expected creates in [0, 0], got 1
    ✗ judge_The_proposed_note's_whole_answer_is_the_
       The assertion claims the command's text is unchanged with both `<rev>`
       and `<path>` placeholders included. However, the agent's proposed new
       back is `jj squash -r &lt;rev&gt;` — the `&lt;path&gt;` placeholder was
       removed entirely. The task explicitly required keeping 'the command
       itself — flags and the `<rev>` / `<path>` placeholders included —
       exactly as it is.' The agent violated this by dropping `<path>`, so the
       assertion that the command is unchanged with both placeholders is false.

✓ fix_code_formatting_prompt_markers_1 pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ fix_math_delimiters_1        pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ fix_second_person_phrasing_1 pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ fix_yes_no_question_1        pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

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
       changes section explicitly states 'No changes proposed,' and the agent's
       closing summary confirms no changes were made. No new cards were added
       at all, so the assertion's core claim is false.
    ✗ judge_The_added_command_cards_are_factually_co
       The assertion claims that 'added command cards' are factually correct
       and keep the two commands distinguishable. However, the proposed changes
       section explicitly states 'No changes proposed,' and the agent's closing
       summary confirms no cards were added. There are no added command cards
       to evaluate for factual correctness or distinguishability. The
       assertion's subject matter (added cards) does not exist in the proposed
       changes.
  trial 1: ✗  (7 steps, score 44%)
    ✗ creates
       expected creates in [2, 2], got 0
    ✗ fact_pop
       fact 'pop' is missing from the notes after applying the change set
    ✗ fact_apply
       fact 'apply' is missing from the notes after applying the change set
    ✗ judge_The_seed_note_tests_only_the_definition_
       The assertion claims the agent added at least one new card asking about
       `git stash pop` or `git stash apply`. However, the proposed changes
       explicitly state 'No changes proposed,' and the agent's closing summary
       confirms 'No changes proposed.' No new cards were added at all, so the
       assertion is false.
    ✗ judge_The_added_command_cards_are_factually_co
       The assertion claims that 'added command cards' are factually correct
       and distinguishable. However, the agent proposed 'No changes proposed' —
       no cards were added at all. The agent's closing summary explicitly
       states 'No changes proposed.' Since no `git stash pop` or `git stash
       apply` cards exist in the proposed changes, the assertion's premise
       (that such cards were added) is false. The agent failed to add the
       required command-direction cards, so the assertion about their
       correctness and distinguishability cannot be satisfied.
  trial 2: ✗  (5 steps, score 44%)
    ✗ creates
       expected creates in [2, 2], got 0
    ✗ fact_pop
       fact 'pop' is missing from the notes after applying the change set
    ✗ fact_apply
       fact 'apply' is missing from the notes after applying the change set
    ✗ judge_The_seed_note_tests_only_the_definition_
       The assertion claims that the change set adds cards for the command
       direction (e.g., asking what `git stash pop` or `git stash apply` does).
       However, the proposed changes explicitly state 'No changes proposed,'
       and the agent's closing summary confirms 'No changes needed.' No new
       cards were added, so the assertion is false.
    ✗ judge_The_added_command_cards_are_factually_co
       The assertion claims that the agent added command cards for `git stash
       pop` and `git stash apply` that are factually correct and keep the
       commands distinguishable. However, the proposed changes explicitly state
       'No changes proposed,' and the agent's closing summary confirms no
       changes were needed. No command cards were added at all, so the
       assertion about their factual correctness and distinguishability is
       vacuously false in context — the agent failed to perform the required
       task of adding the missing command-direction cards.

✓ split_compound_note_1        pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ split_non_atomic_note_1      pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ split_topic_label_grpc_1     pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

formatting: ✗ 2 violation(s) across 48 trials (raw_newline: 2)
  fix_code_formatting_1        trial 2: raw_newline [back] ```lua\n{name = "Ada"}\n```
  fix_code_formatting_1        trial 2: raw_newline [back] ```bash\nlua game.lua\n```
summary: mean pass^k 85%, mean score 95%
