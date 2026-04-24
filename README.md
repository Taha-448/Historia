# 🩺 Triage AI Nurse Bot (Historia)

Historia is a high-performance, medical-grade triage assistant that automates patient history taking and provides real-time emergency detection and practice analytics using advanced AI and database concepts.

## 🚀 Key Features

### 1. Automated Intelligent Triage
*   **Emergency Detection**: Real-time SQL triggers scan patient summaries for critical red-flags and immediately alert doctors with visual UI "Critical Alert" badges.
*   **Patient History**: Structured history taking based on Chief Complaint, Duration, Severity, and Medical History.

### 2. Enterprise-Grade Security
*   **RBAC (Role-Based Access Control)**: Tiered access for Doctors, Nurses, and Admins.
*   **Postgres RLS (Row Level Security)**: Data security enforced at the database engine level—sensitive summaries are invisible to unauthorized personnel even at the API layer.
*   **JWT Authentication**: Secure login system with encrypted token-based sessions.

### 3. Practice Management & Analytics
*   **Analytics Dashboard**: Insightful reports on average triage duration, weekly patient volume, and emergency case ratios.
*   **Symptom Distribution**: Visual histograms showing the frequency of symptoms like Fever, Pain, or Cough across the practice.
*   **Audit Logging**: Full traceability with a "System Activity" feed showing every summary insertion or update with detailed diff-tracking.

## 🛠️ Technology Stack
*   **Frontend**: React.js, Vanilla CSS, Axios.
*   **Backend**: FastAPI, Python 3.14 (Experimental Support), OpenAI GPT-4o-mini.
*   **Database**: PostgreSQL 14+ (ACID Compliant).
*   **Security**: JSON Web Tokens (JWT), passlib (PBKDF2 Hashing).
*   **Integration**: Twilio WhatsApp API.

## 👥 Roles & Permissions
*   **Doctor (Taha)**: Can view full medical summaries, run analytics, and view audit trails.
*   **Nurse (Haad)**: Manages the live waiting room and patient flow.
*   **Admin**: System-wide management.

---
*Developed for advanced clinical triage automation.*
