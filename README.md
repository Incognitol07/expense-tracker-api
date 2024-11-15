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
- **Group Expense Tracking**: Track expenses for groups of users, with automatic splitting of expenses.
- **Debt Notifications**: Get notified when debts are owed within a group, with real-time notifications for updates and payment status.

## Tech Stack

- **Backend Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM (SQLite also available as an alternative)
- **Authentication**: JWT, OAuth2
- **Notifications**: WebSocket-based live notifications
- **Data Visualization**: Integration with front-end for trends and expense tracking

## Installation

### Prerequisites

- **Python 3.12+**

### Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Incognitol07/expense-tracker-api.git
   cd expense-tracker-api
   ```

2. **Set up environment variables**:
   - In the root directory of the project, you'll find a file named `.env.example`.
   - **Copy** the `.env.example` file and rename the copy to `.env`. You can do this using any of the following methods:

     - **Command Line (Linux/Mac)**:
       ```bash
       cp .env.example .env
       ```
     - **Command Line (Windows)**:
       ```cmd
       copy .env.example .env
       ```

     - **Graphical Interface**:
       1. Right-click on the `.env.example` file.
       2. Select **Copy** (or press `Ctrl+C`).
       3. Paste it in the same directory (right-click and select **Paste**, or press `Ctrl+V`).
       4. Rename the pasted file to `.env`.

   - Open the `.env` file in a text editor and update it with your own values for the following variables:
     ```plaintext
     ENVIRONMENT=development
     DB_HOST=localhost
     DB_NAME=expense_tracker
     DB_USER=postgres
     DB_PASSWORD=password
     JWT_SECRET_KEY=myjwtsecretkey
     MASTER_KEY=master_key
     ```

3. **Database Configuration**:
   - By default, the application uses **SQLite** as the database. SQLite requires no additional setup.
   - If you prefer to use PostgreSQL:
     - Uncomment the PostgreSQL database URL line in `app/config.py`.
     - Update your `.env` file with PostgreSQL credentials.

4. **Install Packages**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Start the application**:
   ```bash
   uvicorn app.main:app --reload
   ```

   The application will be available at `http://localhost:8000`.

### Real-Time Notifications

- **WebSocket Endpoint**: `/ws/notifications/{user_id}` - Connect to this WebSocket endpoint for live notifications about budget alerts and spending updates.

This feature allows users to stay updated with budget notifications in real-time, improving their ability to manage finances instantly.

### Group Expense Tracking and Debt Notifications

- **Group Creation**: Users can create groups and invite others to join by email. Upon acceptance, group members can share and track expenses.
- **Expense Splitting**: Expenses paid by one member can be split among all group members, with real-time updates sent through notifications.
- **Debt Notifications**: When expenses are split, users will receive notifications about how much they owe or are owed within the group. These notifications include the status of debt payments.

## Project Structure

```plaintext
expense-tracker-api/
├── app/
│   ├── main.py              # Application entry point
│   ├── websocket_manager.py # WebSocket connection management
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
curl -X POST "http://localhost:8000/auth/register" -H "accept: application/json" -H "Content-Type: application/json" -d '{"username": "testuser","email":"test@user.com", "password": "password123"}
```

### WebSocket Notifications

To test real-time notifications via WebSocket:

1. Connect to `/ws/notifications/{user_id}`.
2. Upon spending updates or threshold alerts, the connected WebSocket will receive messages in real time.

## Conclusion

The Expense Tracking and Budgeting API offers a robust system for managing personal finances, automating budget management, and visualizing financial data. With features like real-time alerts, secure authentication, group expense tracking, debt notifications, and comprehensive data tracking, this API helps users make informed decisions about their finances.

## License

This project is licensed under the MIT License.