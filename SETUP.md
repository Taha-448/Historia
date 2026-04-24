# 🛠️ Triage AI Nurse Bot: Advanced Setup Guide

This guide covers the setup for the **Persistent & Secure** version of the Triage Bot.

## 1. Prerequisites
*   **Python 3.9+** (Tested on 3.14 experimental)
*   **Node.js & npm**
*   **PostgreSQL 14+** (Local or Cloud)
*   **OpenAI API Key**
*   **Twilio Account** (For WhatsApp integration)

## 2. Database Setup (PostgreSQL)
1.  **Create Database**: Open your Postgres terminal and run:
    ```sql
    CREATE DATABASE triage_nurse_ai_bot;
    ```
2.  **Initialize Schema**: Navigate to the `/Backend` folder and run the schema file:
    ```bash
    psql -U postgres -d triage_nurse_ai_bot -f schema.sql
    ```
    *This creates all tables, triggers, and stored procedures for RLS, Auditing, and Analytics.*

## 3. Backend Configuration
1.  **Environment Variables**: Create a `.env` file in the `/Backend` directory:
    ```env
    DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@localhost:5432/triage_nurse_ai_bot"
    OPENAI_API_KEY="sk-..."
    TWILIO_ACCOUNT_SID="..."
    TWILIO_AUTH_TOKEN="..."
    TWILIO_WHATSAPP_NUMBER="..."
    ```
2.  **Install Dependencies**:
    ```bash
    cd Backend
    python -m venv venv
    .\venv\Scripts\activate
    pip install -r requirements.txt
    # Ensure security libraries are present
    pip install python-jose[cryptography] passlib[bcrypt] python-multipart
    ```
3.  **Run the Server**:
    ```bash
    uvicorn main:app --reload
    ```

## 4. Frontend Configuration
1.  **Install & Run**:
    ```bash
    cd client
    npm install
    npm start
    ```

## 5. Testing Credentials
The system uses **Role-Based Access Control**. Use these accounts to test different permission levels:

| User | Role | Username | Password |
| :--- | :--- | :--- | :--- |
| **Dr. Taha** | Doctor | `taha` | `doctor123` |
| **Nurse Haad** | Nurse | `haad` | `nurse123` |
| **Admin** | Admin | `admin_user` | `admin123` |

---
**Note**: The Nurse role is restricted from viewing medical summaries, analytics, and audit logs.
