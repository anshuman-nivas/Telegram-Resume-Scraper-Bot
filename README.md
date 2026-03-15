
---

# 📄 TELEGRAM RESUME SCRAPER BOT

### Intelligent Resume Extraction & Processing System

---

## 📌 Overview

This system is an **Automated Telegram Resume Collection & Processing Bot** designed to:

* Monitor multiple Telegram job/resume groups
* Extract resumes from PDF / DOCX / Images
* Perform OCR using a Dockerized OCR microservice
* Classify resumes vs job descriptions intelligently
* Deduplicate candidates using identity matching
* Automatically email resumes received today
* Maintain processing state & sync with Google Sheets

The system operates as a **fully autonomous pipeline**, requiring minimal manual intervention once deployed.

Built to streamline recruitment workflows. It is suitable for:

* Recruitment agencies
* HR automation pipelines
* Talent acquisition teams
* Startup hiring automation
* Resume pooling systems

---

## 🧠 System Architecture

```
                ┌──────────────────────────┐
                │   Google Sheet (Groups)  │
                └────────────┬─────────────┘
                             │
                             ▼
                ┌──────────────────────────┐
                │ Telegram Resume Bot      │
                │ (Telethon Client)        │
                └────────────┬─────────────┘
                             │
                             ▼
                ┌──────────────────────────┐
                │ Document Analyzer        │
                │ - PDF / DOCX Parser      │
                │ - OCR API Client         │
                └────────────┬─────────────┘
                             │
                             ▼
                ┌──────────────────────────┐
                │ Docker OCR Service       │
                │ (PaddleOCR Engine)       │
                └────────────┬─────────────┘
                             │
                             ▼
                ┌──────────────────────────┐
                │ Resume Classifier        │
                │ - Fuzzy NLP Logic        │
                │ - JD vs Resume scoring   │
                └────────────┬─────────────┘
                             │
                             ▼
                ┌──────────────────────────┐
                │ Identity Dedup System    |
                │ - Email/Phone Dedup      |
                └────────────┬─────────────┘
                             │
                             ▼
         ┌──────────────────────────────────────┐
         │ Storage + Email + State Persistence  │
         └──────────────────────────────────────┘
```

---

## ⚙️ Core Functionalities

### 📥 Telegram Monitoring

* Automatically joins Telegram groups from Google Sheet
* Supports both public and private invite links
* Fetches historical messages
* Listens to real-time incoming resumes
* Handles Telegram flood waits safely
* Crash-safe incremental scanning

---

### 📄 Resume Extraction

Supports:

* PDF resumes
* DOCX resumes
* Image resumes (.jpg / .jpeg / .png)

Image resumes processed via OCR microservice.

---

### 🤖 OCR Microservice (Dockerized PaddleOCR)

* PaddleOCR based extraction
* CPU optimized inference
* API based architecture
* Fully isolated dependency environment
* Replaceable with GPU OCR in future

---

### 🧠 Intelligent Resume Classification

Resume detection is done using:

* Rule-based keyword detection
* Resume section scoring
* JD signal detection
* Fuzzy matching to handle OCR noise
* Email + Phone presence scoring

No LLM used → extremely fast processing.

---

### 🧍 Identity-Based Deduplication

Candidate deduplication performed using:

* Email
* Phone number
* Email + Phone combined identity key

If duplicate found → newer resume replaces older.

Works across:

* Multiple groups
* Multiple formats
* Historical + live messages

---

### 📧 Smart Email Automation

* Only **today’s resumes are emailed automatically**
* Historical resumes are pooled locally
* Email failure → resume NOT marked processed
* Ensures no resume loss

---

### 📊 Google Sheets Synchronization

Tracks per group:

* Last scanned message ID
* Last scan timestamp
* Total resumes fetched
* Total processed documents
* Group join status

Acts as operational dashboard.

---

### 🧾 Persistent Runtime State

Maintains:

* Resume hash database
* Candidate identity store
* Group scanning cursor
* Processing counters

System is:

✔ Restart safe
✔ Crash safe
✔ Network failure safe

---

### 📁 Resume Storage Architecture

Resumes stored as:

```
resumes/
   group_name/
       username_resumeCount_originalName.pdf
```

Where username is derived from email prefix.

Ensures:

* Unique naming
* Candidate grouping
* Clean recruiter pool

---

### 📜 Automated Log Management

* Rotating log system
* Max size: 5 MB per file
* Maintains last 5 logs
* Prevents disk overflow

---

### 🧩 Failure Recovery Design

System handles:

* OCR failure
* Network disconnection
* Telegram rate limits
* Email failure
* Partial processing crash
* Duplicate processing prevention

---

## 📁 Project Structure

```
ResumeBot/
│
├── userbot.exe
├── .env
├── credentials.json
│
├── state/
│   ├── runtime_state.json
│   ├── identity_store.json
│   ├── seen_resume_hashes.json
│
├── logs/
├── resumes/
├── temp/
```

---

## 🔑 Credentials Setup

### 1️⃣ Telegram API

Visit:

https://my.telegram.org

Steps:

* Login using phone
* Open API Development Tools
* Create application
* Copy API_ID and API_HASH

---

### 2️⃣ Google Sheets Service Account

* Open Google Cloud Console
* Create project
* Enable Google Sheets API
* Create Service Account
* Download JSON → rename to:

```
credentials.json
```

Share your sheet with service account email.

---

### 3️⃣ Email Setup

Use:

* Gmail App Password
* NOT normal password

---

### 4️⃣ OCR Service (Docker)

Start OCR service:

```
docker run -p 8001:8001 ocr_service
```

---

## 🧾 .env Example

```
API_ID=
API_HASH=
PHONE=

EMAIL_SENDER=
EMAIL_PASSWORD=
EMAIL_RECEIVER=

SMTP_SERVER=smtp.gmail.com
SMTP_PORT=465

GOOGLE_SHEETS_ID=
GOOGLE_SHEETS_WORKSHEET_NAME=Sheet1
GOOGLE_SHEETS_CREDENTIALS_PATH=credentials.json

OCR_API_URL=http://localhost:8001/ocr
```

---

## ▶️ Running The System

### 🔹 Option 1 — Run via Python

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python userbot.py
```

---

### 🔹 Option 2 — Build EXE

```
pyinstaller --noconfirm --onefile --console --name ResumeBot ^
--add-data ".env;." ^
--add-data "credentials.json;." ^
--hidden-import telethon.sync ^
--hidden-import rapidfuzz ^
--hidden-import fitz ^
--hidden-import docx ^
--hidden-import gspread ^
--hidden-import google.oauth2 ^
userbot.py
```

Then run:

```
ResumeBot.exe
```

---

### ⚠️ Important Operational Notes

* Always start OCR container before bot
* Do not edit runtime state files manually
* First run requires Telegram OTP login
* Do not move resumes folder while bot running
* Email failures do not increment processed counter
* Duplicate resumes automatically replaced

---

## 🔐 Security

* All credentials stored locally
* No external resume storage
* Controlled Google Sheet access
* OCR runs locally

---

## 📈 Scalability

System can scale using:

* GPU OCR container
* Queue system (Redis / Kafka)
* Cloud deployment
* Multi-bot architecture

---

## 🛠 Troubleshooting

Check logs:

```
logs/bot.log
```

Common issues:

* OCR container not running
* Google Sheet permissions missing
* Telegram flood wait
* Email authentication failure

---

## 📞 Support

For deployment support or customization:
Contact Me.
LinkedIn : [https://www.linkedin.com/in/anshuman-nivas-b195a9253/]
