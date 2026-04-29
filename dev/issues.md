**Primary:**

**(sorted in order of importance)**

**(for "poorly decorated", redecorate corresponding to the site UI theme)**

**(for LLM agents completing tasks, please make sure to follow the site UI theme, colors, fonts, etc.)**

- IntegrityError at /en/contests/16/rounds/new/ NOT NULL constraint failed: app_round.materials
- When a person applies to join a team, they get no feedback, the "Join" button doesn't dissapear
- At teams list and team detail view (template), the buttons inside the cards of teams / members don't fit (ex. Kick and Block buttons not fitting for a member card)
- The "Join" button to join a team persists even if the applicant is blocked
- Teams cannot be deleted by their captains, team members cannot leave (they should be able to even after registration end)
- Users can create multiple teams + contest_detail page doesn't show if they already applied (that was fixed for jurors)
- @team_leaderboard_detail.html (and css) is poorly decorated

**Additional:**

- The Cancel button at contests/16/rounds/4/submit/ looks strange (most likely doesn't use default buttons)
- /teams/new needs more vertical padding (just a little more)
- @admin_application_list.html has a button ("back to contests") with no padding or margin
- @rounds_detail_team.html and @rounds_detail.html can be merged + the first one has design flaws
- In profile, pending reviews for juries are empty even if there are assigned submissions to rate

**Fixed:**
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
- juries cannot apply to judge a contest FIXED!!!
- juries cannot judge assigned submissions (they don't see them) FIXED!!!
- Organizers cannot delete teams or kick juries on their contest FIXED!!!
- Jury applications are not visible to organizers FIXED!!!