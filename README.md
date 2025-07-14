Tuk Business Finance Tracker Demo API

This repository hosts a demo environment for a Tuk Business Finance API, designed to help track and manage business expenses, fixed costs, and income of a TukTuk Business. It provides a simple web interface for data visualization and management, backed by a FastAPI backend and a PostgreSQL database.
✨ Features

    Fixed Costs Tracking: Record recurring or one-off fixed expenditures.

    Daily Expenses Tracking: Log day-to-day operational expenses.

    Income Management: Track revenue from various sources (e.g., tours, transfers).

    Cash-On-Hand Balance: Real-time tracking of your current cash balance.

    Summary & Reporting: Monthly, yearly, and global summaries of expenses, income, and profit/loss.

    Demo Data Population: Easily populate the database with sample data for testing.

    User Authentication: Basic authentication for demo purposes.

🚀 Demo Access

You can access the live demo at https://demotuk.duckdns.org.

Demo User Credentials:

To log in and explore the demo environment:

    Username: demo_user

    Password: DemoPass2025!


🔗 API Endpoints (Brief Overview)

The application exposes various API endpoints for managing financial data:

    /login: User authentication.

    /logout: User logout.

    /fixed-costs/: CRUD operations for fixed costs.

    /daily-expenses/: CRUD operations for daily expenses.

    /income/: CRUD operations for income entries.

    /summary/monthly: Monthly financial summaries.

    /summary/yearly: Yearly financial summaries.

    /summary/global: Global financial summaries.

    /summary/expense-categories: Summary of expenses by category.

    /summary/income-sources: Summary of income by source.

    /summary/cash-on-hand: Current cash on hand balance.

Refer to the backend code for detailed endpoint specifications.

💡 Future Features & Next Steps

I'm continuously working to improve this application. Here are some features and enhancements we plan to implement:

    Advanced Reporting: More detailed and customizable financial reports.

    User Management: Ability to create and manage multiple user accounts with different roles.

    Improved UI/UX: Further enhancements to the user interface for a more intuitive experience.

    Mobile Responsiveness: Optimizing the application for seamless use on mobile devices.

    Mobile App: Development of a mobile application (iOS/Android) for immediate logging when working

🛠️ Technologies Used

    Backend: FastAPI, SQLAlchemy

    Database: PostgreSQL (Docker), SQLite (Development/Demo)

    Frontend: HTML, CSS (Tailwind CSS), JavaScript (Chart.js for visualizations)

    Containerization: Docker, Docker Compose

    Deployment: (Assumed Linux server, e.g., Ubuntu)

📄 License

This project is licensed under the MIT License - see the LICENSE file for details.