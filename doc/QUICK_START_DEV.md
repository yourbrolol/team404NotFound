# Quick Start for Developers

This guide will help you set up your development environment and get ContestKeeper running locally.

## 1. Prerequisites

- Python 3.10+
- Git
- Virtualenv (recommended)

## 2. Local Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd team404NotFound
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Apply migrations**:
   ```bash
   cd ContestKeeper
   python manage.py migrate
   ```

5. **Create a superuser**:
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**:
   ```bash
   python manage.py runserver
   ```

You can now access the application at `http://127.0.0.1:8000/`.

## 3. Project Structure

- `ContestKeeper/`: The main Django project directory.
    - `app/`: The core application containing models, views, templates, and static files.
    - `ContestKeeper/`: Project configuration (settings, wsgi, asgi).
- `dev/`: Development scripts and utilities.
- `doc/`: Project documentation.

## 4. Making Changes

1. **Create a branch** for your feature or bugfix.
2. **Implement changes** in `app/`.
3. **Run tests** to ensure everything is working:
   ```bash
   python manage.py test
   ```
4. **Submit a Pull Request** with a clear description of your changes.

## 5. Useful Commands

- `python manage.py makemigrations`: Create new database migrations after model changes.
- `python manage.py collectstatic`: Collect static files for production.
- `python manage.py shell`: Open an interactive Python shell with the Django environment loaded.
