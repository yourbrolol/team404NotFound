Findings
My tests identified several scenarios where the pending reviews list remains empty despite assignments or submissions existing:

Missing Contest Association: Even if a JuryAssignment exists, the jury member must also be added to the contest's jurys Many-to-Many field. If they are only assigned teams but not formally added to the contest, they will see nothing.
No Scoring Criteria: The "Pending Reviews" list is built by checking for missing scores against the contest's Scoring Criteria. If no criteria have been defined for the contest yet, the list will be empty because there is "nothing to rate."
Role Conflict (Organizer-Jury): The profile view uses an if/elif chain for roles. If a user is an Organizer but is also acting as a Jury member in a contest, they will only see the "Organizer" section ("My Contests") and the "Jury" section will be completely hidden.
Partial Assignments: If an organizer has assigned any teams to any jury members in a contest, the system switches to "Assignment Mode." In this mode, any jury member who was not explicitly assigned a team will see an empty list, even if there are teams with submissions they could otherwise judge.
Test Results
All tests passed, confirming these behaviors:

test_pending_reviews_not_shown_if_jury_not_in_contest_jurys: PASSED (Confirms cause #1)
test_pending_reviews_empty_when_no_criteria: PASSED (Confirms cause #2)
test_pending_reviews_for_organizer_who_is_also_jury: PASSED (Confirms cause #3)
test_pending_reviews_empty_when_other_jury_has_assignments: PASSED (Confirms cause #4)