# Expense Tracking and Budgeting API

The **Expense Tracking and Budgeting API** is designed to help individuals manage their finances effectively by tracking expenses, setting and managing budgets, and generating real-time alerts for better financial control. The API supports user authentication, secure data management, and easy integration with third-party services.

## Problem Solved

Managing personal finances can be overwhelming. This API simplifies the process by enabling users to:

- **Track expenses**: Categorize and store expenses with various attributes.
- **Set budgets**: Create, update, and monitor budgets, ensuring that users stay within their spending limits.
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
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT, OAuth2
- **Notifications**: WebSocket-based live notifications
- **Data Visualization**: Integration with front-end for trends and expense tracking

## Installation

### Prerequisites

- **Python 3.8+**
- **PostgreSQL Database**
- **Docker** (optional)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/Incognitol07/expense-tracker-api.git
   cd expense-tracker-api
   ```

2. Set up a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the root directory and add the following:
   ```plaintext
   DATABASE_URL=postgresql://username:password@localhost:5432/expense_tracker
   SECRET_KEY=your_secret_key
   JWT_SECRET_KEY=your_jwt_secret_key
   ```

5. Start the application:
   ```bash
   uvicorn app.main:app --reload
   ```

The application will be available at `http://localhost:8000`.

## API Endpoints

### User Authentication

- **POST /auth/register**: Register a new user.
- **POST /auth/login**: Log in and receive a JWT token.
- **POST /auth/logout**: Invalidate the user's token (optional).
- **GET /auth/refresh**: Refresh the JWT token (optional).

### Expense Management

- **POST /expenses**: Create a new expense.
- **GET /expenses**: Retrieve all expenses for the authenticated user.
- **GET /expenses/{expense_id}**: Retrieve a specific expense.
- **PUT /expenses/{expense_id}**: Update a specific expense.
- **DELETE /expenses/{expense_id}**: Delete a specific expense.

### Category Management

- **POST /categories**: Create a new expense category.
- **GET /categories**: Retrieve all expense categories.
- **GET /categories/{category_id}**: Retrieve a specific category.
- **PUT /categories/{category_id}**: Update a category.
- **DELETE /categories/{category_id}**: Delete a category.

### Budget Management

- **POST /budget**: Set or update a budget.
- **GET /budget**: Retrieve the current budget.
- **PUT /budget**: Update the budget limits.
- **GET /budget/status**: Retrieve the status of the current budget (e.g., remaining balance).
- **GET /budget/history**: Retrieve historical budget data.

### Alerts and Notifications

- **POST /alert**: Set up alerts for when a budget threshold is near or exceeded.
- **GET /alert**: Retrieve all alert settings.
- **PUT /alert**: Update an existing alert.
- **DELETE /alert**: Delete a specific alert.

### Data Analytics

- **GET /analytics/summary**: Summary of expenses and budget adherence.
- **GET /analytics/monthly**: Monthly expense breakdown by category.
- **GET /analytics/weekly**: Weekly expense breakdown by category.
- **GET /analytics/trends**: Trend analysis for expenses over time.
- **GET /analytics/export**: Export data in CSV or JSON format.

### Real-Time Notifications

- **WebSocket Endpoint**: `/ws/notifications/{user_id}` - Connects to WebSocket for live notifications of budget alerts and spending updates.

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
├── requirements.txt         # Project dependencies
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

## Running with Docker

To run the application in Docker:

1. Build the Docker image:
   ```bash
   docker build -t expense-tracker-api .
   ```

2. Run the Docker container:
   ```bash
   docker run -d -p 8000:8000 --env-file .env expense-tracker-api
   ```

3. Access the application via `http://localhost:8000`.

## Conclusion

The Expense Tracking and Budgeting API offers a robust system for managing personal finances, automating budget management, and visualizing financial data. With features like real-time alerts, secure authentication, and comprehensive data tracking, this API can help users make informed decisions about their finances.

## License

This project is licensed under the MIT License.