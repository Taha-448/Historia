from fastapi import FastAPI, Depends, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from twilio.twiml.messaging_response import MessagingResponse
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
import os
from dotenv import load_dotenv
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional

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
    get_user_by_username
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
    
    access_token = create_access_token(data={"sub": user['username'], "role": user['role']})
    return {"access_token": access_token, "token_type": "bearer", "role": user['role']}

@app.post("/chat/web")
async def web_chat(message: dict):
    user_message = message.get("text")
    
    # Since Web users don't log in right now, we route them to a global "Web" phone number acting as a Session tracker
    session_id = get_or_create_patient_session("WEB_GUEST_001")
    
    # 1. Fetch History from Secure Postgres DB
    history = get_chat_history(session_id)
    
    # 2. Invoke LangChain 
    final_prompt = prompt.format(history=history, human_input=user_message)
    
    try:
        ai_response = llm.invoke(final_prompt).content
    except Exception as e:
        if "429" in str(e) or "rate_limit" in str(e).lower():
            return {"response": "The AI Doctor is currently busy due to OpenAI rate limits. Please wait 60 seconds and click Send again!"}
        return {"response": "An unexpected server error occurred."}
    
    # 3. Save Both Messages to Postgres
    save_message(session_id, "Human", user_message)
    save_message(session_id, "AI", ai_response)
    
    # 4. Save to the new 'conversations' table as requested
    save_conversation(user_message, ai_response)
    
    return {"response": ai_response}

@app.post("/chat/whatsapp")
async def whatsapp_chat(Body: str = Form(...), From: str = Form(...)):
    # Twilio sends WhatsApp numbers formatted as "whatsapp:+1234567890"
    # We strip "whatsapp:" off so it perfectly fits our strict 20-character database limit!
    clean_phone = From.replace("whatsapp:", "")
    
    session_id = get_or_create_patient_session(clean_phone)
    
    history = get_chat_history(session_id)
    
    final_prompt = prompt.format(history=history, human_input=Body)
    
    try:
        ai_response = llm.invoke(final_prompt).content
    except Exception as e:
        if "429" in str(e) or "rate_limit" in str(e).lower():
            resp = MessagingResponse()
            resp.message("The AI Doctor is currently busy with high patient volume (OpenAI limit). Please wait exactly 1 minute before sending another message.")
            return PlainTextResponse(str(resp), media_type="application/xml")
        raise e
    
    save_message(session_id, "Human", Body)
    save_message(session_id, "AI", ai_response)
    
    # Save to the new 'conversations' table as requested
    save_conversation(Body, ai_response)
    
    resp = MessagingResponse()
    resp.message(ai_response)
    return PlainTextResponse(str(resp), media_type="application/xml")

@app.get("/active_sessions")
async def get_active_sessions(current_user: dict = Depends(get_current_user)):
    sessions = get_active_sessions_list(role=current_user['role'])
    return {"sessions": sessions}

@app.get("/summary")
async def generate_summary(session_id: int, current_user: dict = Depends(get_current_user)):
    """Generates the summary for the SPECIFIC requested session in DB."""
    
    # Verify the session exists and is active
    if not verify_session_active(session_id):
        return {"summary": "This session is either not active or does not exist."}
        
    chat_history = get_chat_history(session_id)
    
    if not chat_history:
        return {"summary": "No messages in the current session."}
    
    # ... (Prompt logic) ...
    summary_template = """
    You are an expert medical assistant. Based on the conversation below between a triage nurse and a patient, extract the following information and format it clearly for a doctor:
    
    - Chief Complaint:
    - Duration:
    - Severity:
    - Medical History:
    
    If any information is missing, simply write "Not provided". Do NOT invent information.
    
    Conversation:
    {chat_history}
    
    Structured Summary:
    """
    
    summary_prompt = PromptTemplate(input_variables=["chat_history"], template=summary_template)
    final_prompt = summary_prompt.format(chat_history=chat_history)
    
    try:
        summary_result = llm.invoke(final_prompt).content
    except Exception as e:
        return {"summary": "An error occurred while generating the summary."}
    
    # Passing the role to the database
    insert_summary(session_id, summary_result, role=current_user['role'])
    
    return {"summary": summary_result}

@app.get("/analytics")
async def get_analytics(current_user: dict = Depends(get_current_user)):
    """Returns summarized analytics for the doctor dashboard."""
    stats = get_weekly_analytics(role=current_user['role'])
    symptoms = get_symptom_data(role=current_user['role'])
    return {
        "stats": stats,
        "symptoms": symptoms
    }

@app.get("/audit_logs")
async def get_logs(current_user: dict = Depends(get_current_user)):
    """Returns the recent system activity for the auditing dashboard."""
    # Auditing view is usually restricted to Admin or Senior Doctors
    if current_user['role'] not in ['admin', 'doctor']:
         raise HTTPException(status_code=403, detail="Not authorized to view audit logs")
    logs = get_audit_logs()
    return {"logs": logs}