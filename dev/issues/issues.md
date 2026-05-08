**Primary:**

**(sorted in order of importance)**

**(for "poorly decorated", redecorate corresponding to the site UI theme)**

**(for LLM agents completing tasks, please make sure to follow the site UI theme, colors, fonts, etc.)**

**Additional:**

- Contest cards in "My contests" at profile/ should be actual cards with background and similar styling to other contest cards across the site
- At the registation page, there is no light theme. Only the dark one is available.

**Probing**

**(here lie issues that weren't been proven true / their behaviour wasn't studied yet, do not fix until studied & moved out)**

- /evaluate/(idx)?round_id=(id) shows "Evaluation phase is closed" for jurors who are not assigned to the team, should be "You're not assigned to evaluate this team" (reason: finish evaluation contest button might start this issue to happen)

**Fixed:**

- At contest_detail.html, a separate leaderboard tab is visible for the organizers, should not as they already have quick access to it through another page. FIXED!!!
- No language selector at register / login pages is placed FIXED!!!
- The "Finish evaluation" button (primary style) at admin_leaderboard_dashboard.html should have a confirmation dialog before triggering an action ("Are you sure you want to finish evaluation? This action cannot be undone.") as it finishes the evaluation phase for whole project (which can't be undone) FIXED!!!
- At contest_detail.html, when there is an active round, jurors see "View & Submit" instead of "Judge" (and the button should send them to /rounds/team) + after completion the new text needs to be translated to uk (Ukrainian) FIXED!!!
- @admin_application_list.html has a button ("back to contests") with no padding or margin FIXED!!!
- (contest-idx)/leaderboard should be shown to participants as a card at contest_detail.html but only after the contest is finished. Before that, it cannot be accessed neither like described, neither through URL (/leaderboard) FIXED!!!
- @admin_application_list.html has a button ("back to contests") with no padding or margin FIXED!!!
- @team_leaderboard_detail.html (and css) is poorly decorated FIXED!!!
- Users can create multiple teams + contest_detail page doesn't show if they already applied (that was fixed for jurors) FIXED!!!
- Teams cannot be deleted by their captains, team members cannot leave (they should be able to even after registration end) FIXED!!!
- The "Join" button to join a team persists even if the applicant is blocked (actually, it also is a backend issue, it lets the blocked person to apply as well) FIXED!!!
- At teams list and team detail view (template), the buttons inside the cards of teams / members don't fit (ex. Kick and Block buttons not fitting for a member card) FIXED!!!
- IntegrityError at /en/contests/16/rounds/new/ NOT NULL constraint failed: app_round.materials FIXED!!!
- When a person applies to join a team, they get no feedback, the "Join" button doesn't dissapear FIXED!!!
- Admins see "registration closed", should not. FIXED!!!
- Anyone can see teams assigned to to juries to rate (only organizers and juries should see that) FIXED!!!
- In teams tab, admins see the join button FIXED!!!
- Admins / staff cannot manage / delete contests (manage button is visible, but after clicking it, it shows 403 forbidden error, delete button is not visible) FIXED!!!
- TemplateSyntaxError at /en/contests/14/leaderboard/team/8/ FIXED!!!
- @team_leaderboard_detail.html is not mapped to any url patters and button FIXED!!!
- Page not found (404) at contests/14/announcements/3/delete/? FIXED!!!
- Page not found (404) at contests/14/schedule/7/delete/ FIXED!!!
- TypeError at /en/contests/14/analytics/ FIXED!!!
- @admin_leaderboard_dashboard.html is poorly decorated + "Add scoring criterion button" background is broken FIXED!!!
- @leaderboard.html is poorly decorated FIXED!!!
- @round_detail.html is poorly decorated FIXED!!!
- @rounds_detail_team.html and @rounds_detail.html can be merged + the first one has design flaws FIXED!!!
- In profile, pending reviews for juries are empty even if there are assigned submissions to rate (see dev/issues/jury_pending_reviews.md for more info) FIXED!!!
- The "Leaderboard" tab in contest_detail.html is not translated to uk (Ukrainian) FIXED!!!
- juries cannot apply to judge a contest FIXED!!!
- juries cannot judge assigned submissions (they don't see them) FIXED!!!
- Organizers cannot delete teams or kick juries on their contest FIXED!!!
- Jury applications are not visible to organizers FIXED!!!
