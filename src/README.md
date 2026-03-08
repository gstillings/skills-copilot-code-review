# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities
- View active school announcements
- Teacher-only announcement management (add, edit, delete)

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/activities` | Get all activities with their details and current participant count |
| POST | `/activities/{activity_name}/signup?email=student@mergington.edu&teacher_username=<teacher>` | Sign up a student for an activity (teacher auth required) |
| POST | `/activities/{activity_name}/unregister?email=student@mergington.edu&teacher_username=<teacher>` | Unregister a student from an activity (teacher auth required) |
| POST | `/auth/login?username=<username>&password=<password>` | Authenticate a teacher/admin user |
| GET | `/auth/check-session?username=<username>` | Validate a stored frontend session |
| GET | `/announcements` | Get active announcements only |
| GET | `/announcements?include_expired=true` | Get all announcements (active, upcoming, and expired) |
| POST | `/announcements?teacher_username=<teacher>` | Create an announcement (teacher role only) |
| PUT | `/announcements/{announcement_id}?teacher_username=<teacher>` | Update an announcement (teacher role only) |
| DELETE | `/announcements/{announcement_id}?teacher_username=<teacher>` | Delete an announcement (teacher role only) |

## Data Model

The application uses MongoDB collections with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Teachers** - Uses username as identifier:
   - Display name
   - Argon2 password hash
   - Role (`teacher` or `admin`)

3. **Announcements** - Uses generated IDs:
   - Title
   - Message
   - Optional start date
   - Required expiration date
   - Created by teacher username

Data is stored in MongoDB and initialized with sample records when collections are empty.
