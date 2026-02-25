Here is a **GitHub-ready README.md** version — clean Markdown formatting exactly how it should appear on GitHub. You can paste this directly into your repo’s **README.md**.

---

# CivicAid Agentic AI

**Agentic Civic AI powered by Gemini + FastAPI + Opik**

CivicAid is an **agentic AI assistant designed to help people navigate complex civic services** such as veterans benefits, immigration processes, and housing assistance.

This project demonstrates how to build a **production-style agentic AI system** with:

* Google Gemini
* FastAPI
* Agent workflows
* Evaluation pipelines
* Opik observability

---

## Overview

CivicAid is a civic navigation AI that helps users understand:

* Programs they qualify for
* Required documents
* Application steps
* Official resources

Unlike traditional chatbots, CivicAid:

* Uses structured reasoning
* Produces actionable steps
* Provides domain-specific guidance
* Supports evaluation and tracing

---

## Features

### Agentic AI

* Multi-step reasoning
* Structured responses
* Task-oriented assistance
* Context-aware prompts

### Civic Assistance Domains

Supports guidance for:

* Veteran benefits
* Immigration services
* Housing assistance

### API-Based System

FastAPI REST API allows integration with:

* Web apps
* Mobile apps
* Civic platforms

---

## Architecture

```
User Request
     |
     v
FastAPI Endpoint
     |
     v
CivicAid Agent
     |
     |---- Gemini LLM
     |
     |---- Reasoning Logic
     |
     v
Structured Response
```

---

## Installation

### Clone Repository

```
git clone https://github.com/bhavyaraoulji/civicaid-agentic-ai.git
cd civicaid-agentic-ai
```

---

### Create Virtual Environment

```
python -m venv venv
```

Mac/Linux:

```
source venv/bin/activate
```

Windows:

```
venv\Scripts\activate
```

---

### Install Dependencies

```
pip install -r requirements.txt
```

---

### Environment Variables

Create a `.env` file:

```
GEMINI_API_KEY=your_api_key
OPIK_API_KEY=your_api_key
```

---

## Running the API

Start FastAPI server:

```
uvicorn app:app --reload
```

Open Swagger UI:

```
http://127.0.0.1:8000/docs
```

---

## Example Request

Endpoint:

```
POST /ask
```

Example Request:

```json
{
 "question": "How can a veteran apply for housing assistance?"
}
```

Example Response:

```json
{
 "answer": "You may qualify for VA housing programs such as HUD-VASH. Steps include contacting your VA office and applying for vouchers."
}
```

---

# Evaluation Pipeline

CivicAid includes an **evaluation pipeline** for testing the agent’s performance.

This allows:

* Measuring response quality
* Testing prompts
* Improving reliability
* Tracking agent accuracy

---

## Evaluation Dataset

File:

```
eval_dataset.jsonl
```

Contains evaluation queries across civic domains.

Example:

```json
{
 "input": "How do I apply for housing assistance?",
 "expected_output": "Steps to apply for housing assistance programs"
}
```

---

## Running Evaluations

Start the API first:

```
uvicorn app:app --reload
```

Then run:

```
python run_evals_http.py
```

This script:

* Sends test queries
* Calls the API
* Collects responses
* Measures performance

---

## Evaluation Flow

```
Evaluation Dataset
        |
        v
Evaluation Script
        |
        v
FastAPI API
        |
        v
CivicAid Agent
        |
        v
Results
```

---

## Observability with Opik

CivicAid integrates **Opik tracing** for monitoring agent behavior.

This enables:

* Prompt tracking
* Response inspection
* Latency analysis
* Debugging

---

## Project Structure

```
civicaid-agentic-ai/

app.py
FastAPI application

civicaid_agent.py
Agent logic

eval_dataset.jsonl
Evaluation dataset

run_evals_http.py
Evaluation script

requirements.txt
Dependencies

.env
Environment variables (ignored)
```

---

## Tech Stack

* Python
* FastAPI
* Gemini API
* Opik Observability
* Agent Architecture

---

## Use Cases

CivicAid can help:

* Veterans navigate benefits
* Immigrants find legal pathways
* Families locate housing assistance
* Citizens understand programs

---

## Future Improvements

Planned enhancements:

* Retrieval Augmented Generation (RAG)
* Government document search
* Eligibility prediction
* Form automation
* Multi-language support

---

## Author

**Bhavya Raoulji**

AI Engineer | Software Engineer | Civic Tech Builder

GitHub:

[https://github.com/bhavyaraoulji](https://github.com/bhavyaraoulji)

---

## Hackathon Submission

This project was built as a **hackathon submission** demonstrating:

* Agentic AI design
* Production API
* Evaluation pipeline
* Observability tracing

---

# civicaid-agentic-ai
Agentic civic AI with Gemini + Opik for veterans, immigration, and housing assistance
