# Expense Tracking and Budgeting API

The **Expense Tracking and Budgeting API** helps individuals manage their finances by tracking expenses, setting budgets, and generating real-time alerts. The API supports user authentication, secure data management, and easy integration with third-party services.

## Problem Solved

Managing personal finances can be overwhelming. This API simplifies the process by enabling users to:

- **Track expenses**: Categorize and store expenses with various attributes.
- **Set budgets**: Create, update, and monitor budgets, ensuring users stay within their spending limits.
- **Automate alerts**: Get notified when spending exceeds or approaches predefined limits.
- **Visualize data**: Gain insights into spending habits with analytics and visual breakdowns.

## Key Features

- **User Management**: Register, log in, and authenticate users with JWT-based authentication.
- **Expense Tracking**: Add, update, and categorize expenses.
- **Budget Management**: Set and adjust budgets, track expenses against limits, and receive alerts.
- **Data Analytics**: Summarize expenses, view detailed breakdowns by category, and export data.
- **Real-time Notifications**: WebSocket support for live notifications of budget alerts.
- **Secure Access**: JWT-based authentication and password hashing for secure access to the system.

## Tech Stack

- **Backend Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM (SQLite also available as an alternative)
- **Authentication**: JWT, OAuth2
- **Notifications**: WebSocket-based live notifications
- **Data Visualization**: Integration with front-end for trends and expense tracking

## Installation

### Prerequisites

- **Python 3.9+**
- **PostgreSQL Database** (optional if using SQLite)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/Incognitol07/expense-tracker-api.git
   cd expense-tracker-api
   ```

2. Install **Pipenv** (if you haven't already):
   ```bash
   pip install pipenv
   ```

3. Set up a `Pipenv` environment:
   ```bash
   pipenv install
   ```

   This command will create a virtual environment and install the dependencies specified in the `Pipfile`.

4. Activate the `Pipenv` shell:
   ```bash
   pipenv shell
   ```

5. Set up environment variables:
   - In the root directory of the project, you'll find a file named `.env.example`.
   - **Rename** the `.env.example` file to `.env`.
   - Open the `.env` file and edit it with your own values for the following variables:
      ```plaintext
      ENVIRONMENT=development
      DB_HOST=localhost
      DB_NAME=expense_tracker
      DB_USER=postgres
      DB_PASSWORD=password
      JWT_SECRET_KEY=myjwtsecretkey
      MASTER_KEY=master_key
      ```

6. Choose your database:
   - **PostgreSQL**: Ensure you have a PostgreSQL database set up and running.
   - **SQLite**: If you prefer SQLite, open `app/config.py` and `app/database.py`, and uncomment the SQLite database URL while commenting out the PostgreSQL connection line. SQLite does not require additional setup.

7. Start the application:
   ```bash
   uvicorn app.main:app --reload
   ```

The application will be available at `http://localhost:8000`.

### Real-Time Notifications

- **WebSocket Endpoint**: `/ws/notifications/{user_id}` - Connect to this WebSocket endpoint for live notifications about budget alerts and spending updates.

This feature allows users to stay updated with budget notifications in real-time, improving their ability to manage finances instantly.

## Project Structure

```plaintext
expense-tracker-api/
├── app/
│   ├── main.py              # Application entry point
│   ├── websocket_manager.py  # WebSocket connection management
│   ├── routers/             # API endpoint routers
│   ├── schemas/             # Pydantic models for request validation
│   ├── utils/               # Utility functions (e.g., security, notifications)
│   ├── models/              # SQLAlchemy models
│   ├── database.py          # Database connection and session handling
│   └── config.py            # Configuration settings
├── Pipfile                  # Pipenv configuration file
├── Pipfile.lock             # Locked versions of installed packages
├── .env                     # Environment variables
└── README.md                # Project documentation
```

## Testing the API

You can test the API using **curl**, **Postman**, **Bruno**, or FastAPI's interactive docs available at `http://localhost:8000/docs`.

### Example Request

To register a new user:

```bash
curl -X POST "http://localhost:8000/auth/register" -H "accept: application/json" -H "Content-Type: application/json" -d '{"username": "testuser", "password": "password123"}'
```

### WebSocket Notifications

To test real-time notifications via WebSocket:

1. Connect to `/ws/notifications/{user_id}`.
2. Upon spending updates or threshold alerts, the connected WebSocket will receive messages in real time.

## Conclusion

The Expense Tracking and Budgeting API offers a robust system for managing personal finances, automating budget management, and visualizing financial data. With features like real-time alerts, secure authentication, and comprehensive data tracking, this API helps users make informed decisions about their finances.

## License

This project is licensed under the MIT License.