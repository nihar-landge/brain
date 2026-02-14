# Brain - Personal AI Journal & Dashboard

A local-first, privacy-focused AI journaling and analytics platform.

## Prerequisites

- **Python**: 3.10+
- **Node.js**: 18+
- **npm**: 9+

## Setup & Installation

### 1. Backend

1.  Navigate to the backend directory:
    ```bash
    cd backend
    ```
2.  Create and activate a virtual environment (optional but recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Configure environment variables:
    - Create a `.env` file in the `backend` directory.
    - Add your Gemini API Key and a Secret Key:
      ```env
      GEMINI_API_KEY=your_gemini_api_key_here
      API_SECRET_KEY=your_secret_key_here
      ```

### 2. Frontend

1.  Navigate to the frontend directory:
    ```bash
    cd frontend
    ```
2.  Install dependencies:
    ```bash
    npm install
    ```

## Running the Application

You need to run both the backend and frontend servers simultaneously.

### Start the Backend

In the `backend` directory:
```bash
python -m uvicorn main:app --reload
```
The backend will start at `http://localhost:8000`.

### Start the Frontend

In the `frontend` directory:
```bash
npm run dev
```
The frontend will start at `http://localhost:5173`.

## Features

- **Journal**: Daily entries with mood, energy, and stress tracking.
- **Dashboard**: Visual analytics of your mood trends and habit completion.
- **Goals**: Track long-term goals with milestones and progress bars.
- **Habits**: Daily habit tracker with streaks and stats.
- **Predictions**: AI-powered insights into your mood and energy patterns.
- **Chat**: Conversational interface with long-term memory.
