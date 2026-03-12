
---

# 📄 TELEGRAM RESUME SCRAPER BOT

## Intelligent Resume Extraction & Processing System

---

## 📌 Overview

This system is an automated **Telegram Resume Collection Bot** designed to:

* Monitor multiple Telegram job/resume groups
* Extract resumes from PDF / DOCX / Images
* Perform OCR using a Dockerized OCR microservice
* Classify resumes vs job descriptions intelligently
* Deduplicate candidates using identity matching
* Automatically email resumes received today
* Maintain processing state & sync with Google Sheets

This is a **fully automated production-grade pipeline** built for recruitment automation.

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
                │ (PaddleOCR)              │
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
                │ Identity Manager         │
                │ - Email/Phone Dedup      │
                └────────────┬─────────────┘
                             │
                             ▼
         ┌──────────────────────────────────────┐
         │  Storage + Email Automation + State  │
         └──────────────────────────────────────┘
```

---

## ⚙️ Key Features

### 📥 Telegram Monitoring

* Auto joins groups from Google Sheet
* Monitors both historical + live messages
* Handles flood waits intelligently
* Private + public group support

### 📄 Resume Extraction

Supports:

* PDF resumes
* DOCX resumes
* Image resumes (via OCR)

### 🤖 OCR Microservice

* Dockerized PaddleOCR engine
* CPU optimized
* API based architecture
* Scalable & replaceable

### 🧠 Intelligent Resume Classification

Uses:

* Fuzzy keyword matching
* Resume section scoring
* JD detection scoring
* OCR noise correction

### 🧍 Identity Deduplication

Based on:

* Email
* Phone
* Email + Phone combined key

Automatically replaces older resume.

### 📧 Smart Email Automation

* Only **today’s resumes are emailed**
* Historical resumes are only stored
* Email failure → resume not counted processed

### 📊 Google Sheets Sync

Tracks per group:

* Last scanned message ID
* Total resumes fetched
* Total processed documents
* Join status

### 🧾 Runtime Persistence

Maintains:

* Seen file hashes
* Candidate identity store
* Bot scanning cursor
* Processing counters

Bot is **restart safe**.

---

## 📁 Project Structure

```
Resume Bot/
│
├── ResumeBot.exe
├── .env
├── credentials.json
│
├── runtime_state.json
├── identity_store.json
├── seen_resume_hashes.json
│
├── resumes/
├── logs/
└── temp/
```

---

## 🔑 Required Credentials Setup

### 1️⃣ Telegram API Credentials

Go to:

👉 [https://my.telegram.org](https://my.telegram.org)

Steps:

1. Login using phone number
2. Go to **API Development Tools**
3. Create app
4. Copy:

* API_ID
* API_HASH

---

### 2️⃣ Google Sheets Service Account

Steps:

1. Go to Google Cloud Console
2. Create new project
3. Enable:

```
Google Sheets API
```

4. Create **Service Account**
5. Download JSON → rename to:

```
credentials.json
```

6. Share sheet with service account email.

7. In case of any confusion refer this -> "https://youtu.be/zCEJurLGFRk?si=TX_rFLGqmjA65TDQ"
---

### 3️⃣ Email Credentials

Use:

* Gmail / SMTP server

Enable:

* App password (NOT real password)

---

### 4️⃣ OCR Service (Docker)

Install:

```
Docker Desktop
```

Then run:

```
docker run -p 8001:8001 ocr_service
```

---

## 🧾 .env Configuration

Example:

```
API_ID=xxxxx
API_HASH=xxxxx
PHONE=+91xxxxxxxx

EMAIL_SENDER=xxx@gmail.com
EMAIL_PASSWORD=app_password
EMAIL_RECEIVER=xxx@gmail.com

SMTP_SERVER=smtp.gmail.com
SMTP_PORT=465

GOOGLE_SHEETS_ID=xxxx
GOOGLE_SHEETS_WORKSHEET_NAME=Sheet1
GOOGLE_SHEETS_CREDENTIALS_PATH=credentials.json

OCR_API_URL=http://localhost:8001/ocr
```

---

## ▶️ How To Run

### Step 1 — Start OCR Service

```
docker run -p 8001:8001 ocr_service
```

### Step 2 — Run Bot

```
ResumeBot.exe
```

First run:

* Telegram login OTP required

---

## ⚠️ Important Operational Notes

### ✔ Always start OCR service before bot

### ✔ Do NOT edit runtime JSON files manually

### ✔ Do NOT move resumes folder while bot running

### ✔ Bot uses incremental scanning

### ✔ Restart safe

### ✔ Email failures do NOT mark resume processed

### ✔ Duplicate resumes auto replaced

### ✔ OCR noise automatically corrected

---

## 📊 Resume Classification Logic

Resume score based on:

* Contact info presence
* Resume section detection
* Fuzzy keyword matching

JD score based on:

* Hiring language detection
* Salary / vacancy signals

Decision:

```
If JD > Resume → Ignore
If Resume < threshold → Ignore
Else → Save
```

---

## 🔐 Security Considerations

* Credentials stored locally only
* No external data storage
* No resume sharing except configured email
* Google sheet access limited via service account

---

## 🧩 Failure Recovery Design

Bot supports:

* Crash safe restart
* Duplicate prevention
* Partial processing recovery
* Sheet state reconstruction
* Atomic file writes

---

## 📈 Scalability Design

System can scale by:

* Replacing OCR container with GPU version
* Adding Redis queue
* Cloud deployment
* Multi-bot sharding
* Async email workers

---

## 🛠 Support

If system stops:

Check:

```
logs/bot.log
```

Common issues:

* OCR not running
* Sheet permission missing
* Telegram flood wait
* Email auth failure

---
