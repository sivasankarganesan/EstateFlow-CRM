# EstateFlow CRM

**Real Estate Customer Relationship Management System**

EstateFlow CRM is a web-based application designed to manage real estate leads, property inventory, sales employees, follow-up activities, and property bookings in one place.

## 1. Project Overview

The application helps real estate teams track potential customers through the sales pipeline, manage property availability, and record bookings. It provides role-based access for administrators and sales employees.

## 2. Features

- **User Authentication:** Login and logout with password verification.
- **Role-Based Access:** Separate permissions for Admin and Sales Employee roles.
- **Dashboard:** Displays lead counts, sales pipeline stages, follow-ups, bookings, booked value, and available units.
- **Lead Management:** Create, search, filter, and update customer leads.
- **Lead Assignment:** Assign leads to sales employees.
- **Follow-Up Tracking:** Record follow-up dates and customer interaction notes.
- **Property Management:** Maintain projects, buildings, units, property types, areas, prices, and availability.
- **Booking Management:** Link a lead to a property unit and record a booking.
- **Duplicate Booking Prevention:** Prevent multiple confirmed bookings for the same property unit.
- **Responsive Interface:** Web interface built with HTML, CSS, and JavaScript.

## 3. Technology Stack

| Component | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python, Flask |
| Database | SQLite |
| API | REST-style JSON API |
| Authentication | Flask sessions and password hashing |
| Production server | Gunicorn |
| Version control | Git and GitHub |
| Deployment | Render |

## 4. Project Structure

```text
EstateFlow-CRM/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
└── static/
    └── index.html
```

- `app.py` — Flask application, API endpoints, authentication, and database operations.
- `requirements.txt` — Python dependencies.
- `static/index.html` — Frontend interface.
- `.gitignore` — Excludes local databases, environment files, and unnecessary generated files.
- `estateflow.db` — SQLite database created automatically when the application initializes. It is not committed to the Git repository.

## 5. Installation and Local Setup

### Prerequisites

- Python 3
- pip
- Git

### Installation

Clone the repository:

```bash
git clone https://github.com/sivasankarganesan/EstateFlow-CRM.git
cd EstateFlow-CRM
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the application:

```bash
python app.py
```

Open the local URL displayed by Flask in your browser. The default port is `5000`.

For production-style local testing, use:

```bash
gunicorn app:app
```

## 6. Database Overview

EstateFlow CRM uses SQLite for data storage. The database schema is initialized by the `init_db()` function in `app.py`.

The main tables are:

- `users`
- `leads`
- `lead_notes`
- `projects`
- `buildings`
- `units`
- `bookings`

Foreign keys maintain relationships between related records. Database constraints help validate role values, lead stages, unit status, and booking uniqueness.

Refer to `DB_API_OVERVIEW.md` for the detailed database schema and API endpoint documentation.

## 7. API Overview

The backend exposes JSON endpoints for authentication, dashboard information, lead management, notes, property inventory, and bookings.

All `/api` endpoints except the health check and login endpoint require authentication unless otherwise stated. Administrator-only operations enforce role checks.

Health check:

```http
GET /api/health
```

Example response:

```json
{
  "status": "ok",
  "app": "EstateFlow CRM"
}
```

See `DB_API_OVERVIEW.md` for the full endpoint list, permissions, and database relationships.

## 8. Business Rules

1. A lead must have a name and phone number.
2. Lead stages are restricted to New, Contacted, Site Visit, Interested, Negotiation, Booked, and Lost.
3. A sales employee can access leads assigned to them, while administrators can manage all leads.
4. A property unit can have only one confirmed booking at a time.
5. Booking a unit updates its status and changes the associated lead stage to Booked.
6. Cancelling a booking makes the unit available again.

## 9. Design Decisions

- **SQLite:** Selected for a lightweight application with simple setup and minimal dependencies.
- **Flask:** Used to implement the backend and JSON API with a small Python codebase.
- **Role-Based Authorization:** Separates administrator operations from sales employee operations.
- **Database Constraints and Transactions:** Used to protect data integrity and prevent duplicate active bookings.
- **Automatic Initialization:** The database schema and sample records are created when the database is initialized for the first time.

## 10. Deployment

The application is deployed as a Python web service on Render, using Gunicorn as the application server.

**Live application:** Add your Render public URL here.

**Source code:** https://github.com/sivasankarganesan/EstateFlow-CRM

### Deployment Note

The current configuration uses SQLite. Render's free service does not provide persistent disks, so database changes may be lost after restarts or redeployments. Persistent storage or a managed database such as PostgreSQL is recommended for production use.

## 11. Security Considerations

- Passwords are hashed before storage.
- Session-based authentication is used.
- Role checks protect administrator-only operations.
- Database queries use parameterized SQL for data values.
- The default demo password and fallback Flask secret key must be replaced before production use.
- Only synthetic demonstration data should be used in the publicly deployed demo until production storage and security configuration are completed.

## 12. Conclusion

EstateFlow CRM demonstrates how a real estate sales workflow can be managed through a web application. It combines lead tracking, employee assignments, property inventory, dashboard reporting, and booking operations using Flask, SQLite, and a JavaScript-based frontend.
