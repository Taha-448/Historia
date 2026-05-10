from fastapi import FastAPI, Depends, HTTPException, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from twilio.twiml.messaging_response import MessagingResponse
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
import os
from dotenv import load_dotenv
from pathlib import Path
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from redis_client import redis_client, check_rate_limit, cache_chat_history, get_cached_chat_history
from psycopg2.extras import RealDictCursor


from database import (
    get_or_create_patient_session, 
    get_chat_history, 
    save_message, 
    save_conversation,
    get_active_sessions_list,
    verify_session_active,
    insert_summary,
    initialize_db,
    get_weekly_analytics,
    get_symptom_data,
    get_audit_logs,
    get_user_by_username,
    create_staff_user,
    verify_staff_user,
    get_db_connection
)

# JWT Security Settings
SECRET_KEY = "SUPER_SECRET_TRIAGE_KEY" # In production, use os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# --- AUTH HELPERS ---
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None: raise HTTPException(status_code=401)
        return {"username": username, "role": role}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")

# Load the OPENAI_API_KEY and DATABASE_URL from the .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

app = FastAPI()

# Allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Setup the AI Model (Using OpenAI!)
llm = ChatOpenAI(temperature=0.2, model="gpt-4o-mini")

# 2. The Strict System Prompt
prompt_template = """
You are Historia, an empathetic, professional medical assistant for a Pakistani telemedicine platform. Always introduce yourself as Historia.
Your ONLY job is to collect patient history in a structured way.
You must ask about:
1. Chief Complaint (What is wrong?)
2. Duration (How long has it been happening?)
3. Severity (How bad is it?)
4. Medical History (Any past illnesses or current medications?)

CRITICAL RULES:
- You must NEVER diagnose the patient.
- You must NEVER prescribe medication.
- Ask only one question at a time. Be empathetic.
- If a patient asks for a diagnosis, politely tell them that only a doctor can diagnose, and you are here to gather information for the doctor.
- VERY IMPORTANT: Once you have collected the 4 basic pieces of information, you MUST ask 5 to 8 relevant, detailed follow-up questions about their specific symptoms to build a comprehensive report.
- You MUST ask these follow-up questions ONE BY ONE. Never bundle multiple questions together.
- After you have asked exactly 5 to 8 follow-up questions in total, politely end the triage session by telling the patient that you have everything the doctor needs. DO NOT ask any further questions after that.

LANGUAGE RULES:
- If the patient communicates in Urdu or Roman Urdu and a language preference hasn't been set yet, your VERY NEXT response must ONLY be to acknowledge it and ask if they would prefer to continue the conversation in Roman Urdu or English.
- IMPORTANT: Do NOT ask any clinical or triage questions in the same message where you ask for a language preference.
- Example Choice Message: "I see you're speaking Urdu. Would you like to continue in English or Roman Urdu? (Kya aap Roman Urdu mein baat karna chahenge ya English mein?)"
- Once the user chooses, you MUST strictly use that language for all future messages in this session.
- If they choose Roman Urdu, ensure your clinical questions are clear, empathetic, and easy to understand in that language.

Current conversation:
{history}
Patient: {human_input}
Nurse:"""

prompt = PromptTemplate(
    input_variables=["history", "human_input"], 
    template=prompt_template
)

# Initialize database tables on startup
initialize_db()

# --- API ENDPOINTS ---

@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user_by_username(form_data.username)
    if not user or not pwd_context.verify(form_data.password, user['hashed_password']):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    # Check if user is verified
    if not user.get('is_verified', False):
        raise HTTPException(status_code=403, detail="Account pending admin verification.")
    
    access_token = create_access_token(data={"sub": user['username'], "role": user['role']})
    return {"access_token": access_token, "token_type": "bearer", "role": user['role']}

@app.post("/signup")
async def signup(username: str = Form(...), password: str = Form(...), role: str = Form(...)):
    # Check if user already exists
    if get_user_by_username(username):
        raise HTTPException(status_code=400, detail="Username already taken")
    
    hashed_password = pwd_context.hash(password)
    
    # Auto-verify only Nurses. Doctors and Admins require manual approval.
    is_verified = True if role == 'nurse' else False
    
    create_staff_user(username, hashed_password, role, is_verified=is_verified)
    
    detail = "Account created. You can log in now."
    if role in ['doctor', 'admin']:
        detail = f"Account created. Please wait for an existing admin to verify your {role} profile."
        
    return {"detail": detail}

@app.post("/admin/verify_staff")
async def verify_staff(username: str, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can verify staff.")
    
    verify_staff_user(username)
    return {"detail": f"User {username} has been verified."}

@app.get("/admin/pending_staff")
async def get_pending_staff(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can view pending staff.")
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT username, role, created_at FROM staff_users WHERE is_verified = FALSE")
        pending = cursor.fetchall()
        for p in pending:
            p['created_at'] = str(p['created_at'])
        return {"pending": pending}
    finally:
        cursor.close()
        conn.close()

@app.post("/chat/web")
async def web_chat(request: Request, message: dict):
    user_message = message.get("text")
    client_ip = request.client.host
    
    # 1. Rate Limiting (Redis)
    is_allowed = check_rate_limit(client_ip)
    if not is_allowed:
        raise HTTPException(status_code=429, detail="Too many messages. Please wait 60 seconds.")
    
    # 2. Session & History with Caching (Redis)
    session_id = get_or_create_patient_session(client_ip)
    
    history = get_cached_chat_history(session_id)
    if not history:
        history = get_chat_history(session_id)
        cache_chat_history(session_id, history)
    
    # 3. Invoke LangChain 
    final_prompt = prompt.format(history=history, human_input=user_message)
    
    try:
        ai_response = llm.invoke(final_prompt).content
    except Exception as e:
        if "429" in str(e) or "rate_limit" in str(e).lower():
            return {"response": "The AI Doctor is currently busy due to OpenAI rate limits. Please wait 60 seconds."}
        return {"response": "An unexpected server error occurred."}
    
    # 4. Save to Postgres & Update Cache
    save_message(session_id, "Human", user_message)
    save_message(session_id, "AI", ai_response)
    save_conversation(user_message, ai_response)
    
    # Refresh cache so the next turn sees the new messages
    history = get_chat_history(session_id)
    cache_chat_history(session_id, history)
    
    return {"response": ai_response}

@app.post("/chat/whatsapp")
async def whatsapp_chat(request: Request, Body: str = Form(...), From: str = Form(...)):
    clean_phone = From.replace("whatsapp:", "")
    
    # 1. Rate Limiting (Redis)
    is_allowed = check_rate_limit(clean_phone)
    if not is_allowed:
        resp = MessagingResponse()
        resp.message("Rate limit exceeded. Please wait a moment.")
        return PlainTextResponse(str(resp), media_type="application/xml")

    # 2. Session & History with Caching (Redis)
    session_id = get_or_create_patient_session(clean_phone)
    
    history = get_cached_chat_history(session_id)
    if not history:
        history = get_chat_history(session_id)
        cache_chat_history(session_id, history)
    
    final_prompt = prompt.format(history=history, human_input=Body)
    
    try:
        ai_response = llm.invoke(final_prompt).content
    except Exception as e:
        if "429" in str(e) or "rate_limit" in str(e).lower():
            resp = MessagingResponse()
            resp.message("System busy. Please wait 60 seconds.")
            return PlainTextResponse(str(resp), media_type="application/xml")
        raise e
    
    save_message(session_id, "Human", Body)
    save_message(session_id, "AI", ai_response)
    save_conversation(Body, ai_response)
    
    # Refresh cache so the next turn sees the new messages
    history = get_chat_history(session_id)
    cache_chat_history(session_id, history)
    
    resp = MessagingResponse()
    resp.message(ai_response)
    return PlainTextResponse(str(resp), media_type="application/xml")

@app.get("/active_sessions")
async def get_active_sessions(current_user: dict = Depends(get_current_user)):
    sessions = get_active_sessions_list(role=current_user['role'])
    return {"sessions": sessions}

@app.get("/summary")
async def generate_summary(session_id: int, current_user: dict = Depends(get_current_user)):
    if not verify_session_active(session_id):
        return {"summary": "This session is either not active or does not exist."}
        
    chat_history = get_chat_history(session_id)
    if not chat_history:
        return {"summary": "No messages in the current session."}
    
    summary_template = """
    You are an expert medical assistant. Based on the conversation below, extract:
    - Chief Complaint:
    - Duration:
    - Severity:
    - Medical History:
    If missing, write "Not provided".
    
    Conversation:
    {chat_history}
    """
    
    summary_prompt = PromptTemplate(input_variables=["chat_history"], template=summary_template)
    final_prompt = summary_prompt.format(chat_history=chat_history)
    
    try:
        summary_result = llm.invoke(final_prompt).content
    except Exception as e:
        return {"summary": "An error occurred while generating the summary."}
    
    insert_summary(session_id, summary_result, role=current_user['role'])
    return {"summary": summary_result}

@app.get("/analytics")
async def get_analytics(current_user: dict = Depends(get_current_user)):
    stats = get_weekly_analytics(role=current_user['role'])
    symptoms = get_symptom_data(role=current_user['role'])
    return {"stats": stats, "symptoms": symptoms}

@app.get("/audit_logs")
async def get_logs(current_user: dict = Depends(get_current_user)):
    if current_user['role'] not in ['admin', 'doctor']:
         raise HTTPException(status_code=403, detail="Not authorized to view audit logs")
    logs = get_audit_logs()
    return {"logs": logs}