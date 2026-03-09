# E-commerce Backend

This is the backend for the e-commerce site, built with Flask.

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Set up environment variables in `.env`
3. Run migrations: `alembic upgrade head`
4. Run the app: `python app.py`

## Structure

- `app.py`: Main application
- `database/`: Database models and connection
- `routes/`: API endpoints
- `services/`: Business logic
- `middleware/`: Authentication and rate limiting
- `utils/`: Helpers and validators
