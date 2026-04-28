**Primary:**

**(sorted in order of importance)**

**(for "poorly decorated", redecorate corresponding to the site UI theme)**

**(for LLM agents completing tasks, please make sure to follow the site UI theme, colors, fonts, etc.)**

- Page not found (404) at contests/14/announcements/3/delete/?
- Page not found (404) at contests/14/schedule/7/delete/
- @team_leaderboard_detail.html is not mapped to any url patters and button
- Admins / staff cannot manage / delete contests (manage button is visible, but after clicking it, it shows 403 forbidden error, delete button is not visible)
- In teams tab, admins see the join button
- Anyone can see teams assigned to to juries to rate (only organizers and juries should see that)

**Additional:**

- @admin_application_list.html has a button ("back to contests") with no padding or margin
- @rounds_detail_team.html and @rounds_detail.html can be merged + the first one has design flaws
- Admins see "registration closed", should not.
- In profile, pending reviews for juries are empty even if there are assigned submissions to rate

**Fixed:**
- TypeError at /en/contests/14/analytics/ FIXED!!!
- @admin_leaderboard_dashboard.html is poorly decorated + "Add scoring criterion button" background is broken FIXED!!!
- @leaderboard.html is poorly decorated FIXED!!!
- @round_detail.html is poorly decorated FIXED!!!
- juries cannot apply to judge a contest FIXED!!!
- juries cannot judge assigned submissions (they don't see them) FIXED!!!
- Organizers cannot delete teams or kick juries on their contest FIXED!!!
- Jury applications are not visible to organizers FIXED!!!