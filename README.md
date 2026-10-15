# EstateFlow CRM

A real estate CRM application built with Python, Flask, SQLite, HTML, CSS, and JavaScript.

## Features

- User authentication
- Dashboard metrics
- Lead management
- Property and unit listing
- Booking management
- SQLite data persistence

## Requirements

- Python 3
- pip

## Setup

1. Open Terminal in the project directory.
2. Create a virtual environment:

   ```bash
   python3 -m venv .venv
   ```

3. Activate it:

   ```bash
   source .venv/bin/activate
   ```

4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. Start the application:

   ```bash
   python app.py
   ```

6. Open the local address shown by Flask in your browser.

## Database

The application initializes its database through `init_db()` in `app.py`. Follow the project's database initialization behavior when setting up a fresh copy.

## Security

Use authorized demo credentials for evaluation. Do not use real customer information or production secrets in a submitted copy.
