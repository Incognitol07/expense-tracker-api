# Expense Tracking and Budgeting API

This is an API built with FastAPI to manage personal finances. It offers features for tracking expenses, managing budgets, categorizing spending, and generating analytics. The API supports user authentication and secure data access with JWT-based authentication.

## Features

- **User Management**: Register, log in, and authenticate users.
- **Expense Tracking**: Add, update, and delete expenses, categorized by predefined or custom categories.
- **Budget Management**: Set budgets, monitor spending, and receive alerts.
- **Analytics**: Generate insights and visualize spending patterns.
- **Security**: JWT-based authentication and secure password storage.

## Tech Stack

- **Backend**: FastAPI
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Authentication**: OAuth2 and JWT
- **Migrations**: Alembic
- **Deployment**: Uvicorn

## Project Structure

```plaintext
project
|__ alembic                 # Alembic migration files
|__ app
|   |__ main.py             # Application entry point
|   |__ routers             # API routers
|   |__ schemas             # Pydantic models for requests/responses
|   |__ utils               # Utility functions (e.g., security, notifications)
|   |__ models              # SQLAlchemy models
|   |__ database.py         # Database connection
|   |__ config.py           # Configuration settings
|__ alembic.ini             # Alembic configuration
|__ requirements.txt        # Project dependencies
|__ README.md               # Project documentation
|__ .env                    # Environment variables (not committed)
```

## Getting Started

### Prerequisites

- **Python 3.8+**
- **PostgreSQL Database**
- **Docker** (optional, for containerized setup)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Incognitol07/expense-tracker-api.git
   cd expense-tracker-api
   ```

2. **Set up a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file in the root directory with the following:
   ```plaintext
   DATABASE_URL=postgresql://username:password@localhost:5432/expense_tracker
   SECRET_KEY=your_secret_key
   ```

5. **Apply database migrations**:
   ```bash
   alembic upgrade head
   ```

6. **Start the application**:
   ```bash
   uvicorn app.main:app --reload
   ```

### API Endpoints

| Method | Endpoint                 | Description                        |
|--------|---------------------------|------------------------------------|
| POST   | `/auth/register`          | Register a new user               |
| POST   | `/auth/login`             | User login and token generation   |
| GET    | `/expenses`               | Retrieve user expenses            |
| POST   | `/expenses`               | Add a new expense                 |
| PUT    | `/expenses/{expense_id}`  | Update an existing expense        |
| DELETE | `/expenses/{expense_id}`  | Delete an expense                 |
| GET    | `/categories`             | List expense categories           |
| POST   | `/budget`                 | Set or update a budget            |
| GET    | `/analytics`              | Retrieve analytics on expenses    |

### Testing the API

To test the API, you can use **curl**, **Postman**, or **FastAPI's interactive documentation** available at `http://127.0.0.1:8000/docs`.

### Example Request

Here’s an example of how to register a user:

```bash
curl -X POST "http://127.0.0.1:8000/auth/register" -H "accept: application/json" -H "Content-Type: application/json" -d '{"username": "testuser", "password": "testpassword"}'
```

### Security

- Passwords are hashed using `bcrypt`.
- Tokens are generated and verified using JWT, ensuring secure access to protected endpoints.

## Running with Docker

For easier setup and deployment, you can run the application using Docker.

1. **Build the Docker image**:
   ```bash
   docker build -t expense-tracker-api .
   ```

2. **Run the container**:
   ```bash
   docker run -d -p 8000:8000 --env-file .env expense-tracker-api
   ```

3. **Access the application**:
   Visit `http://localhost:8000/docs` to access the API documentation.

## License

This project is licensed under the MIT License.
