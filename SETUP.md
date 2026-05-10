# 🛠️ Triage AI Nurse Bot: Advanced Setup Guide

This guide covers the setup for the **Historia** triage system with PostgreSQL and Redis.

## 1. Prerequisites
*   **Python 3.9+**
*   **Node.js & npm**
*   **PostgreSQL 14+**
*   **Redis Server** (Local or Cloud)
*   **OpenAI API Key**

## 2. Database Setup (PostgreSQL)
1.  **Create Database**:
    ```sql
    CREATE DATABASE triage_nurse_ai_bot;
    ```
2.  **Initialize Schema**: Navigate to `/Backend` and run:
    ```bash
    psql -U postgres -d triage_nurse_ai_bot -f schema.sql
    ```

## 3. Cache & Rate-Limit Setup (Redis)
Ensure you have a Redis instance running. If using Redis Cloud, grab your connection URL.

## 4. Backend Configuration
1.  **Environment Variables**: Create a `.env` in `/Backend`:
    ```env
    DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@localhost:5432/triage_nurse_ai_bot"
    REDIS_URL="redis://:YOUR_PASSWORD@your-redis-host:port"
    OPENAI_API_KEY="sk-..."
    TWILIO_ACCOUNT_SID="..."
    TWILIO_AUTH_TOKEN="..."
    ```
2.  **Install Dependencies**:
    ```bash
    cd Backend
    python -m venv venv
    .\venv\Scripts\activate
    pip install -r requirements.txt
    ```
3.  **Run the Server**:
    ```bash
    uvicorn main:app --reload
    ```

## 5. Frontend Configuration
```bash
cd client
npm install
npm start
```

## 6. Default Testing Credentials
All default accounts share the password: **`password123`**

| User | Role | Username | Notes |
| :--- | :--- | :--- | :--- |
| **Dr. Taha** | Doctor | `taha` | Full Clinical Access |
| **Nurse Haad** | Nurse | `haad` | Waiting Room Only |
| **Admin** | Admin | `admin_user` | Full Access + Staff Verification |

**Note**: New Doctor/Admin accounts created via Signup require manual verification by an existing Admin before login is permitted.
