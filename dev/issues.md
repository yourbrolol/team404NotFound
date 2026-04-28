**Primary:**

**(sorted in order of importance)**

**(for "poorly decorated", redecorate corresponding to the site UI theme)**

**(for LLM agents completing tasks, please make sure to follow the site UI theme, colors, fonts, etc.)**


- @admin_leaderboard_dashboard.html is poorly decorated
- @leaderboard.html is poorly decorated
- TypeError at /en/contests/14/analytics/
- Admins / staff cannot manage / delete contests (manage button is visible, but after clicking it, it shows 403 forbidden error, delete button is not visible)
- In teams tab, admins see the join button
- Anyone can see teams assigned to to juries to rate (only organizers and juries should see that)

**Additional:**

- Admins see "registration closed", should not.
- In profile, pending reviews for juries are empty even if there are assigned submissions to rate

**Fixed:**
- @round_detail.html is poorly decorated FIXED!!!
- juries cannot apply to judge a contest FIXED!!!
- juries cannot judge assigned submissions (they don't see them) FIXED!!!
- Organizers cannot delete teams or kick juries on their contest FIXED!!!
- Jury applications are not visible to organizers FIXED!!!