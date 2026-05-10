# 🩺 Triage AI Nurse Bot (Historia)

Historia is a high-performance, medical-grade triage assistant that automates patient history taking and provides real-time emergency detection and practice analytics using advanced AI and database concepts.

## 🚀 Key Features

### 1. Automated Intelligent Triage
*   **Emergency Detection**: Real-time SQL triggers scan patient summaries for critical red-flags and immediately alert doctors with visual UI "Critical Alert" badges.
*   **Intelligent History**: Structured history taking based on Chief Complaint, Duration, Severity, and Medical History with AI-driven follow-up questions.

### 2. High-Performance Caching & Protection
*   **Redis Rate Limiting**: Protects the API from spam and controls costs by limiting message frequency per user/IP.
*   **Redis Chat Caching**: Sub-millisecond retrieval of conversation history, offloading 90% of read traffic from PostgreSQL.

### 3. Enterprise-Grade Security
*   **RBAC (Role-Based Access Control)**: Tiered access for Doctors, Nurses, and Admins.
*   **Postgres RLS (Row Level Security)**: Data security enforced at the database engine level—sensitive summaries are invisible to unauthorized personnel.
*   **Staff Verification Flow**: Manual gatekeeping for Doctor/Admin accounts to ensure only verified personnel can access clinical data.
*   **Secure Hashing**: PBKDF2-SHA256 password encryption for all staff accounts.

### 4. Practice Management & Analytics
*   **Analytics Dashboard**: Insightful reports on average triage duration, weekly patient volume, and emergency case ratios.
*   **Symptom Distribution**: Visual frequency mapping of common patient complaints.
*   **Audit Logging**: Automated system activity feed showing every medical summary insertion or update with detailed change tracking.

## 🛠️ Technology Stack
*   **Frontend**: React.js, Vanilla CSS, Axios.
*   **Backend**: FastAPI, Python 3.9+, OpenAI GPT-4o-mini.
*   **Database**: PostgreSQL 14+ (Persistent) & Redis (Cache/Rate-Limit).
*   **Security**: JWT (JSON Web Tokens), passlib, RLS.

---
*Developed for advanced clinical triage automation.*
