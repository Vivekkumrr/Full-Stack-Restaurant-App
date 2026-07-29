# Johnny's Restaurant

A full-stack restaurant reservation and management system for Johnny's Restaurant.

## Tech Stack

- **Backend:** Django, Django REST Framework, django-cors-headers
- **Frontend:** React (Vite), Axios
- **Database:** PostgreSQL (production) / SQLite (local dev)
- **Auth:** Django session authentication with CSRF protection

## Features

- Customer reservation booking with real-time table availability
- Automatic table status updates (available → reserved → available)
- Admin dashboard: manage reservations, tables, and menu
- Role-based access (customer / staff / admin)

## Project Structure

```
backend/    # Django project (api app, settings, views, models)
frontend/   # React + Vite app
```

## Getting Started

### Backend Setup

1. Navigate to the backend folder and create a virtual environment:
   ```bash
   cd backend
   python -m venv venv
   venv\Scripts\activate      # Windows
   source venv/bin/activate   # macOS/Linux
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file (or set these as environment variables):
   ```
   SECRET_KEY=your-secret-key-here
   DJANGO_ENV=development
   ```
   Leave `DATABASE_URL` unset locally — the project falls back to SQLite automatically.

4. Run migrations:
   ```bash
   python manage.py migrate
   ```

5. Start the backend server:
   ```bash
   python manage.py runserver
   ```
   Backend runs at `http://localhost:8000`.

### Frontend Setup

1. Navigate to the frontend folder:
   ```bash
   cd frontend
   npm install
   ```

2. Create a `.env` file:
   ```
   VITE_API_URL=http://localhost:8000/api
   ```

3. Start the dev server:
   ```bash
   npm run dev
   ```
   Frontend runs at `http://localhost:5173`.

## Default User Roles

| Role | Access |
|---|---|
| Customer | Book/view/cancel own reservations |
| Staff | Manage reservations and tables |
| Admin | Full access, including menu management |
