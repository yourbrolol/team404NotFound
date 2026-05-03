# 📋 Test Documentation: `test_application.py`

## Purpose
This test suite focuses on the logic surrounding applications to a contest, specifically the approval process and validation of application types.

## Test Class: `ApplicationLogicTest`
Tests the core business logic and views related to the `Application` model.

### Setup
- Creates an **Organizer** and a **Participant**.
- Creates an active **Contest**.

### Test Cases
1. **`test_approve_participant_application`**
   - **Scenario**: A participant has a pending application for a contest.
   - **Action**: Organizer approves the application via a POST request.
   - **Verification**: 
     - Status code is 302 (Redirect).
     - Application status changes to `APPROVED`.
     - The user is successfully added to the contest's `participants` list.

2. **`test_apply_invalid_type_fails`**
   - **Scenario**: A user tries to apply to a contest with a non-existent or invalid application type.
   - **Action**: Participant sends a POST request with an invalid `app_type`.
   - **Verification**: 
     - Status code is 403 (Forbidden).
     - No `Application` object is created in the database.
