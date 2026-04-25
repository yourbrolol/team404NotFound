# team404NotFound — ContestKeeper

ContestKeeper is a web platform for organizing programming tournaments with team registration, task rounds, submissions, jury evaluation, and leaderboards.

## Tech Stack
- **Framework:** Django 6.0.4
- **Language:** Python 3.13.5
- **Database:** SQLite
- **Server:** Daphne (ASGI)
- **Frontend:** Vanilla HTML/CSS/JS (Dark Theme)

## Installation & Startup

**Clone the repository and enter the project root:**
   ```bash
   cd team404NotFound
   ```

**There are 2 ways to run the app: The default way and the Docker way**

**Default way:**

1. **Create a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r ContestKeeper/requirements.txt
   ```

3. **Set up environment variables:**
   Copy `.env.example` to `.env` and adjust settings.
   ```bash
   cp ContestKeeper/.env.example ContestKeeper/.env
   ```

4. **Run migrations:**
   ```bash
   cd ContestKeeper
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Start the server:**
   ```bash
   python manage.py runserver
   ```

**Docker way**

1. **Build the Docker image**
   ```bash
   sudo docker build -t contestkeeper . # optionally change "contestkeeper" to custom name
   ```

2. **Run the Docker image**
   ```bash
   sudo docker run -p 8000:8000 contestkeeper # change "contestkeeper" to container name; change the first 8000 to the needed port
   ```

## User Roles & Credentials
All default accounts use the password: `password`

- **Organizer:** `organizer` — Creates contests, manages rounds, and assigns jury members.
- **Jury:** `jury` — Evaluates team submissions based on criteria.
- **Participant:** `user`, `admin` — Joins teams and submits solutions to rounds.

## Project Structure
- `ContestKeeper/`: Main Django project directory.
- `app/`: Primary application logic including models, views, and templates.
- `app/static/`: CSS and JS assets.
- `app/templates/`: HTML templates for all views.