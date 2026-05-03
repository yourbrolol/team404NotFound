# Test Bug Report

## Overview
This report covers the failing tests observed when running `python manage.py test app.tests`.

## Failed Tests
1. `test_apply_invalid_type_fails` (app.tests.test_application.ApplicationLogicTest)
2. `test_non_organizer_cannot_delete_contest` (app.tests.test_bugfixes.BugfixRegressionTest)
3. `test_organizer_can_delete_own_contest` (app.tests.test_bugfixes.BugfixRegressionTest)

## Root Causes
### 1. Invalid application type test returns 404 instead of 403
- The failure is caused by internationalized URL routing.
- `settings.py` uses `LANGUAGE_CODE = 'en-us'`, while supported languages are configured as `('en', 'English')` and `('uk', 'Ukrainian')`.
- The generated request path became `/en-us/contests/.../apply/invalid_type/`, which does not resolve correctly through the locale-aware URL patterns.
- As a result, the view is never reached and the test sees a `404` rather than the expected `403`.

### 2. Contest delete POST returns 405
- `ContestDeleteView` in `app/views/views_contest.py` defines only `get()` and does not handle `post()`.
- Therefore, POST requests to the contest delete endpoint are rejected by Django with `405 Method Not Allowed`.
- This prevents both the non-organizer permission check and the organizer deletion action from executing.

## Impact
- `test_apply_invalid_type_fails` appears to be a view logic error but is actually an i18n routing/configuration issue.
- Both contest deletion failures stem from a missing POST handler, causing the same endpoint to fail for authorized and unauthorized users.

## Recommended Fixes
- Align `LANGUAGE_CODE` with supported language codes or adjust URL generation to use a valid locale prefix.
- Update `ContestDeleteView` to support POST and perform organizer permission checks before deleting the contest.
