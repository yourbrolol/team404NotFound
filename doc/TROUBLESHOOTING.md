# Troubleshooting Guide

This document covers common issues you might encounter while developing or running ContestKeeper and provides solutions to resolve them.

## 1. Database Issues

### Error: `OperationalError: no such table: ...`
**Cause**: The database migrations haven't been applied or the database file is missing.
**Solution**: Run `python manage.py migrate` to apply all migrations.

### Error: `IntegrityError: UNIQUE constraint failed`
**Cause**: Attempting to insert a duplicate value into a field with a unique constraint (e.g., duplicate username or team name).
**Solution**: Ensure data being entered is unique. If testing, you may need to clear the test data or use different names.

## 2. Server & Environment Issues

### Error: `ModuleNotFoundError: No module named '...'`
**Cause**: A dependency is missing in your current environment.
**Solution**: Ensure your virtual environment is activated and run `pip install -r requirements.txt`.

### Port already in use
**Cause**: Another process is using port 8000.
**Solution**: Run the server on a different port: `python manage.py runserver 8080`.

## 3. Static Files & CSS

### Changes to CSS/JS are not reflecting
**Cause**: The browser is caching old static files.
**Solution**: 
1. Perform a hard refresh in your browser (Ctrl+F5 or Cmd+Shift+R).
2. If in production, ensure you ran `python manage.py collectstatic`.
3. Check if there are any errors in the browser console.

## 4. Permissions

### Error: `403 Forbidden` or "You do not have permission to view this page"
**Cause**: Your user account does not have the required role (Organizer, Jury, Participant) to access the specific view.
**Solution**: 
1. Check your user role in the Django Admin (`/admin/`).
2. Ensure you are logged in with the correct account.

## 5. WebSockets & Real-time

### Leaderboard not updating in real-time
**Cause**: Django Channels might not be configured correctly, or the WebSocket connection failed.
**Solution**:
1. Check the browser console for WebSocket connection errors.
2. Ensure `redis` (if used as a channel layer) is running.
3. Verify that `python manage.py runserver` is handling both HTTP and WebSocket traffic (it does by default with Channels).

---

If your issue is not listed here, please contact the project maintainers or search the [Django Documentation](https://docs.djangoproject.com/).
