# Eval scores

run: 20260910T040037Z
model: qwen3.8-27b
elapsed: 55m 9s

✓ adam_duplicate_merge_1       pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ clean_cluster_no_changes_1   pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ clean_code_formatting_1      pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✗ fix_code_formatting_1        pass@1  67%  pass^3  30%  (2/3 trials)  score 94%
  trial 2: ✗  (11 steps, score 82%)
    ✗ edits
       expected edits in [3, 3], got 2
    ✗ must_touch_3
       note 3 should have been edited or deleted
    ✗ judge_The_proposed_note_whose_whole_answer_is_
       The agent did not propose any change to Note 3. Its closing summary
       explicitly states 'note 3 uses a fenced lua block for the bare token
       table.sort' and considers it 'already correct.' The original Note 3 back
       is a fenced code block (```lua\ntable.sort\n```), and since no edit was
       proposed for it, it remains in that form. The assertion claims the
       proposed note writes `table.sort` as inline code, but no such change was
       made. The assertion is false.

✗ fix_code_formatting_command_1 pass@1  67%  pass^3  30%  (2/3 trials)  score 96%
  trial 0: ✗  (9 steps, score 88%)
    ✗ judge_The_proposed_note's_whole_answer_is_the_
       The assertion claims the proposed note's answer is `jj squash -r <rev>
       <path>` with both placeholders unchanged and still escaped. However, the
       agent's proposed new back is `jj squash -r &lt;rev&gt;` inside a fenced
       bash block — the `<path>` argument was entirely removed. The command
       text is not unchanged; it is shorter. The `<path>` placeholder does not
       appear at all, so it cannot be 'stored escaped as &lt;path&gt;'. While
       the fenced-code-block formatting with a language tag is correct, the
       assertion's claim about the command's text being unchanged (including
       `<path>`) is false.

✓ fix_code_formatting_prompt_markers_1 pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ fix_math_delimiters_1        pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ fix_second_person_phrasing_1 pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

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
       The assertion claims that 'the change set nevertheless adds cards for
       the command direction' and that 'at least one new card asks what git
       stash pop or git stash apply does.' However, the proposed changes are
       explicitly 'No changes proposed.' The agent's closing summary also
       confirms 'No changes proposed.' Therefore, no new cards were added, and
       the assertion's claim that the change set adds command-direction cards
       is false.
    ✗ judge_The_added_command_cards_are_factually_co
       The proposed changes state 'No changes proposed' and the agent's summary
       confirms no cards were added. The assertion presupposes that command
       cards for `git stash pop` and `git stash apply` were added and evaluates
       their factual correctness and separability. Since no cards were actually
       added, the assertion's premise is not met — there are no 'added command
       cards' to be factually correct or to keep the commands distinguishable.
       The agent failed to perform the required task of deriving and proposing
       the missing command-direction cards.
  trial 1: ✗  (6 steps, score 44%)
    ✗ creates
       expected creates in [2, 2], got 0
    ✗ fact_pop
       fact 'pop' is missing from the notes after applying the change set
    ✗ fact_apply
       fact 'apply' is missing from the notes after applying the change set
    ✗ judge_The_seed_note_tests_only_the_definition_
       The assertion claims that the change set adds cards for the command
       direction (e.g., a card asking what `git stash pop` or `git stash apply`
       does). However, the proposed changes section explicitly states 'No
       changes proposed,' and the agent's closing summary confirms 'No changes
       proposed.' No new cards were added. The assertion is factually
       incorrect.
    ✗ judge_The_added_command_cards_are_factually_co
       The assertion claims that 'added command cards' exist and are factually
       correct. However, the proposed changes section explicitly states 'No
       changes proposed.' The agent added no cards for `git stash pop` or `git
       stash apply`. Since no cards were added, the assertion's premise is
       false — there are no 'added command cards' to evaluate for correctness
       or distinguishability. The agent failed to perform the core task of
       proposing the command-direction cards.
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
       changes section explicitly states 'No changes proposed' and the agent's
       summary confirms 'No changes needed.' No new cards were added, so the
       assertion is false.
    ✗ judge_The_added_command_cards_are_factually_co
       The assertion claims that 'added command cards' exist and are factually
       correct, keeping `git stash pop` and `git stash apply` distinguishable.
       However, the proposed changes section explicitly states 'No changes
       proposed,' and the agent's closing summary confirms no new cards were
       added. Since no command cards were added at all, the assertion's premise
       that such cards exist and satisfy the stated criteria is not met. The
       assertion cannot be true when it describes properties of non-existent
       cards.

✗ split_compound_note_1        pass@1  67%  pass^3  30%  (2/3 trials)  score 94%
  trial 0: ✗  (11 steps, score 82%)
    ✗ edits
       expected edits in [1, 1], got 2
    ✗ must_not_touch_2
       note 2 should not have been touched

✓ split_non_atomic_note_1      pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

formatting: ✗ 2 violation(s) across 42 trials (no_trailing_period: 2)
  split_non_atomic_note_1      trial 0: no_trailing_period [back] …Returns the number of items in an object.
  split_non_atomic_note_1      trial 0: no_trailing_period [back] …Generates a sequence of integers.
summary: mean pass^k 78%, mean score 95%
