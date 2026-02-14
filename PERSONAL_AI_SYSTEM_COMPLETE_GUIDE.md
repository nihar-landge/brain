# Personal AI Memory & Prediction System
## Complete Technical Documentation

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Technology Stack](#technology-stack)
4. [How Everything Works](#how-everything-works)
5. [Data Flow](#data-flow)
6. [Component Details](#component-details)
7. [ML Models Explained](#ml-models-explained)
8. [Setup Instructions](#setup-instructions)
9. [API Endpoints](#api-endpoints)
10. [Database Schema](#database-schema)
11. [Cost Analysis](#cost-analysis)
12. [Privacy & Security](#privacy-security)
13. [Future Enhancements](#future-enhancements)

---

## 🎯 System Overview

### What This System Does

A personal AI assistant that:
- **Remembers everything** you tell it (using Letta/MemGPT)
- **Never forgets** your preferences, goals, and history
- **Predicts** your mood, energy levels, and habit success
- **Provides insights** based on your behavioral patterns
- **Gives personalized advice** using your complete history
- **Learns continuously** from your daily logs

### Key Capabilities

```
✅ Long-term memory (remembers forever)
✅ Daily journaling (events, mood, decisions, habits)
✅ Predictive analytics (ML models predict your patterns)
✅ Semantic search (find anything from your history)
✅ Goal tracking & success prediction
✅ Energy forecasting & productivity optimization
✅ Decision support based on past outcomes
✅ Conversational AI interface
✅ Analytics dashboard with visualizations
✅ 100% local data storage (your device only)
```

---

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INTERFACE LAYER                     │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              React Web Application                    │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │  │
│  │  │ Journal  │  │   Chat   │  │    Dashboard     │   │  │
│  │  │  Input   │  │ Interface│  │  (Analytics &    │   │  │
│  │  │          │  │          │  │   Predictions)   │   │  │
│  │  └──────────┘  └──────────┘  └──────────────────┘   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↕️ REST API (FastAPI)
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND SERVICE LAYER                     │
│                      (Python FastAPI)                        │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                  LAYER 1: MEMORY                      │  │
│  │                                                        │  │
│  │              Letta (MemGPT) Agent                     │  │
│  │  ┌─────────────────────────────────────────────┐     │  │
│  │  │  Core Memory (Always Active)                │     │  │
│  │  │  - Current goals                            │     │  │
│  │  │  - Key preferences                          │     │  │
│  │  │  - User personality model                   │     │  │
│  │  │  - Active context                           │     │  │
│  │  └─────────────────────────────────────────────┘     │  │
│  │  ┌─────────────────────────────────────────────┐     │  │
│  │  │  Archival Memory (Long-term Storage)        │     │  │
│  │  │  - All journal entries                      │     │  │
│  │  │  - Historical decisions                     │     │  │
│  │  │  - Past events & experiences                │     │  │
│  │  │  - Mood history                             │     │  │
│  │  └─────────────────────────────────────────────┘     │  │
│  │  ┌─────────────────────────────────────────────┐     │  │
│  │  │  Recall Memory (Recent Context)             │     │  │
│  │  │  - Recent conversations                     │     │  │
│  │  │  - Last 10 interactions                     │     │  │
│  │  └─────────────────────────────────────────────┘     │  │
│  └──────────────────────────────────────────────────────┘  │
│                            ↕️                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              LAYER 2: KNOWLEDGE RETRIEVAL             │  │
│  │                                                        │  │
│  │                  RAG System (ChromaDB)                │  │
│  │  ┌─────────────────────────────────────────────┐     │  │
│  │  │  Vector Database                            │     │  │
│  │  │  - Embeddings of all journal entries        │     │  │
│  │  │  - Semantic search capability               │     │  │
│  │  │  - Fast similarity matching                 │     │  │
│  │  └─────────────────────────────────────────────┘     │  │
│  │  ┌─────────────────────────────────────────────┐     │  │
│  │  │  Embedding Model                            │     │  │
│  │  │  - text-embedding-004 (Gemini)              │     │  │
│  │  │  - Converts text to vectors                 │     │  │
│  │  └─────────────────────────────────────────────┘     │  │
│  └──────────────────────────────────────────────────────┘  │
│                            ↕️                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            LAYER 3: PREDICTIVE ANALYTICS              │  │
│  │                                                        │  │
│  │                  ML Models Engine                     │  │
│  │  ┌──────────────┐  ┌──────────────┐                  │  │
│  │  │ Mood         │  │ Habit Success│                  │  │
│  │  │ Predictor    │  │ Predictor    │                  │  │
│  │  │(RandomForest)│  │  (XGBoost)   │                  │  │
│  │  └──────────────┘  └──────────────┘                  │  │
│  │  ┌──────────────┐  ┌──────────────┐                  │  │
│  │  │ Energy       │  │ Decision     │                  │  │
│  │  │ Forecaster   │  │ Pattern      │                  │  │
│  │  │ (Prophet)    │  │ Analyzer     │                  │  │
│  │  └──────────────┘  └──────────────┘                  │  │
│  │  ┌──────────────┐                                     │  │
│  │  │ Goal         │                                     │  │
│  │  │ Achievement  │                                     │  │
│  │  │ Predictor    │                                     │  │
│  │  │(Neural Net)  │                                     │  │
│  │  └──────────────┘                                     │  │
│  │                                                        │  │
│  │  ┌─────────────────────────────────────────────┐     │  │
│  │  │  Feature Engineering Pipeline               │     │  │
│  │  │  - Extracts features from journal data      │     │  │
│  │  │  - Time-based features                      │     │  │
│  │  │  - Behavioral patterns                      │     │  │
│  │  │  - Historical statistics                    │     │  │
│  │  └─────────────────────────────────────────────┘     │  │
│  │  ┌─────────────────────────────────────────────┐     │  │
│  │  │  Model Training Pipeline                    │     │  │
│  │  │  - Automated retraining (weekly)            │     │  │
│  │  │  - Performance monitoring                   │     │  │
│  │  │  - Model versioning                         │     │  │
│  │  └─────────────────────────────────────────────┘     │  │
│  └──────────────────────────────────────────────────────┘  │
│                            ↕️                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              LAYER 4: LLM BRAIN                       │  │
│  │                                                        │  │
│  │               Gemini API (Free Tier)                  │  │
│  │  ┌─────────────────────────────────────────────┐     │  │
│  │  │  - Natural language understanding           │     │  │
│  │  │  - Response generation                      │     │  │
│  │  │  - Insight synthesis                        │     │  │
│  │  │  - Context analysis                         │     │  │
│  │  └─────────────────────────────────────────────┘     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↕️
┌─────────────────────────────────────────────────────────────┐
│                     DATA STORAGE LAYER                       │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   SQLite     │  │  ChromaDB    │  │ ML Models    │      │
│  │              │  │              │  │   Cache      │      │
│  │ - Journal    │  │ - Vector     │  │              │      │
│  │   entries    │  │   embeddings │  │ - Trained    │      │
│  │ - Mood logs  │  │ - Semantic   │  │   models     │      │
│  │ - Goals      │  │   index      │  │ - Model      │      │
│  │ - Habits     │  │              │  │   metadata   │      │
│  │ - Decisions  │  │              │  │ - Performance│      │
│  │ - Letta      │  │              │  │   metrics    │      │
│  │   memory     │  │              │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│          All stored locally on YOUR device                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 💻 Technology Stack

### Frontend Stack

```javascript
{
  "framework": "React 18.x",
  "language": "JavaScript (ES6+)",
  "styling": "TailwindCSS 3.x",
  "stateManagement": "React Hooks (useState, useEffect, useContext)",
  "charts": "Recharts 2.x",
  "icons": "Lucide React",
  "httpClient": "Fetch API",
  "build": "Vite"
}
```

**Key Libraries:**
- **React**: Component-based UI
- **TailwindCSS**: Utility-first styling
- **Recharts**: Data visualization (charts, graphs)
- **Lucide React**: Icon library
- **date-fns**: Date manipulation

### Backend Stack

```python
{
  "framework": "FastAPI 0.109+",
  "language": "Python 3.10+",
  "asyncSupport": "async/await (native)",
  "apiDocs": "OpenAPI/Swagger (auto-generated)",
  "cors": "FastAPI CORS middleware"
}
```

**Key Libraries:**
- **FastAPI**: Modern Python web framework
- **Uvicorn**: ASGI server
- **Pydantic**: Data validation

### Memory & AI Stack

```python
{
  "memorySystem": "Letta (MemGPT) 0.3+",
  "llm": "Google Gemini API (gemini-pro)",
  "embeddingModel": "text-embedding-004",
  "vectorDB": "ChromaDB 0.4+",
  "ragFramework": "LangChain (optional)"
}
```

**Key Components:**
- **Letta**: Long-term memory management
- **Gemini API**: LLM for conversations & insights
- **ChromaDB**: Vector database for semantic search
- **Sentence Transformers**: Embedding generation (fallback)

### Machine Learning Stack

```python
{
  "traditional_ml": {
    "scikit-learn": "1.3+",
    "xgboost": "2.0+",
    "prophet": "1.1+"
  },
  "deep_learning": {
    "tensorflow": "2.15+ (optional)",
    "pytorch": "2.1+ (optional)"
  },
  "data_processing": {
    "pandas": "2.1+",
    "numpy": "1.24+",
    "scipy": "1.11+"
  },
  "visualization": {
    "matplotlib": "3.8+",
    "seaborn": "0.12+"
  }
}
```

**ML Models:**
- **RandomForest**: Mood prediction
- **XGBoost**: Habit success prediction
- **Prophet**: Energy/productivity forecasting
- **Neural Networks**: Goal achievement prediction (optional)

### Database Stack

```python
{
  "structured_data": "SQLite 3.x",
  "vector_store": "ChromaDB 0.4+",
  "orm": "SQLAlchemy 2.0+ (optional)",
  "migrations": "Alembic (optional)"
}
```

### DevOps & Deployment

```yaml
containerization: Docker 24.x
orchestration: Docker Compose
server: Uvicorn (ASGI)
proxy: Nginx (optional, for production)
process_manager: systemd or PM2 (optional)
```

### Development Tools

```javascript
{
  "linting": {
    "python": "ruff, black, pylint",
    "javascript": "ESLint"
  },
  "testing": {
    "python": "pytest",
    "javascript": "Jest, React Testing Library"
  },
  "api_testing": "Postman, Thunder Client"
}
```

---

## ⚙️ How Everything Works

### System Workflow

#### 1. Daily Journal Entry

```
User writes journal entry
      ↓
Frontend sends to backend
      ↓
Backend processes:
  1. Saves to SQLite
  2. Generates embedding
  3. Stores in ChromaDB
  4. Updates Letta memory
  5. Triggers ML feature extraction
      ↓
Confirmation to user
```

#### 2. Conversational AI Query

```
User: "How have I been feeling lately?"
      ↓
Backend receives query
      ↓
Letta Agent:
  1. Checks core memory (knows user context)
  2. Searches archival memory (past conversations)
  3. Queries ChromaDB (semantic search for relevant entries)
      ↓
Relevant data retrieved
      ↓
Gemini API:
  1. Receives: User query + Context + Retrieved data
  2. Generates: Personalized response
      ↓
Response flows back:
  Gemini → Letta → Backend → Frontend → User
      ↓
Letta updates recall memory (remembers this conversation)
```

#### 3. Predictive Analytics

```
User requests prediction (e.g., "Will I succeed at gym today?")
      ↓
Backend identifies prediction type
      ↓
Feature Engineering:
  1. Extracts relevant features from journal data
  2. Day of week, time, historical success rate
  3. Current mood, energy level, competing tasks
      ↓
ML Model (Habit Success Predictor):
  1. Loads trained model
  2. Feeds features into model
  3. Generates prediction + confidence
      ↓
Gemini API (Natural Language Generation):
  1. Receives: Prediction results + User history
  2. Generates: Human-friendly explanation
      ↓
Response: "78% success probability because..."
```

#### 4. Automated Insights (Proactive)

```
Scheduled Job (Daily at 8 AM):
      ↓
ML Pipeline runs:
  1. Analyzes last 7 days of data
  2. Runs all predictive models
  3. Detects patterns & anomalies
      ↓
Insight Generation:
  1. Identifies significant findings
  2. Gemini generates natural language insights
  3. Creates notification/alert
      ↓
User sees: "Pattern detected: You're 60% more productive 
           after morning exercise. Try it tomorrow?"
```

---

## 🔄 Data Flow Detailed

### Write Path (Saving Data)

```python
# 1. User creates journal entry
journal_entry = {
    "date": "2026-02-14",
    "mood": 7,
    "events": "Had great meeting with team",
    "decisions": "Decided to start new project",
    "habits": ["exercise", "meditation"],
    "energy_level": 8
}

# 2. Backend receives via API
@app.post("/api/journal")
async def create_journal_entry(entry: JournalEntry):
    
    # 3. Save to SQLite
    db_entry = save_to_database(entry)
    
    # 4. Generate embedding for RAG
    embedding = generate_embedding(entry.text)
    chromadb.add(
        documents=[entry.text],
        embeddings=[embedding],
        metadatas=[{"date": entry.date, "mood": entry.mood}],
        ids=[db_entry.id]
    )
    
    # 5. Update Letta memory
    letta_agent.archival_memory_insert(entry.text)
    
    # If important, update core memory
    if entry.contains_goal():
        letta_agent.core_memory_append("goals", entry.goal_text)
    
    # 6. Extract features for ML
    features = extract_features(entry)
    ml_feature_store.save(features)
    
    # 7. Trigger model retraining if threshold reached
    if should_retrain():
        schedule_model_training()
    
    return {"status": "success", "id": db_entry.id}
```

### Read Path (Retrieving Data)

```python
# 1. User asks question
user_query = "What made me happy last week?"

# 2. Backend processes query
@app.post("/api/chat")
async def chat(query: str):
    
    # 3. Letta searches its memory
    letta_response = letta_agent.user_message(query)
    
    # Behind the scenes, Letta:
    # a. Checks core memory (user preferences)
    # b. Searches archival memory
    # c. Uses ChromaDB for semantic search
    relevant_entries = chromadb.query(
        query_texts=[query],
        n_results=5
    )
    
    # 4. Combines context
    context = {
        "user_query": query,
        "letta_memory": letta_response,
        "relevant_entries": relevant_entries,
        "user_profile": get_user_profile()
    }
    
    # 5. Calls Gemini API
    gemini_response = gemini_api.generate(
        prompt=format_prompt(context),
        model="gemini-pro"
    )
    
    # 6. Returns response
    return {
        "response": gemini_response,
        "sources": relevant_entries
    }
```

### Prediction Path (ML Models)

```python
# 1. User requests prediction
prediction_request = {
    "type": "habit_success",
    "habit": "gym",
    "time": "6:00 PM",
    "date": "2026-02-15"
}

# 2. Feature engineering
features = {
    "day_of_week": 5,  # Friday
    "hour": 18,
    "historical_success_rate": 0.45,  # 45% on Fridays at 6 PM
    "current_streak": 3,
    "mood_today": 7,
    "energy_level": 6,
    "competing_tasks": 2,
    "weather": "rainy",
    "last_gym_visit_days_ago": 2
}

# 3. Load trained model
model = load_model("habit_success_predictor_v3.pkl")

# 4. Generate prediction
prediction_proba = model.predict_proba([features])[0][1]  # 0.34
prediction_class = "low" if prediction_proba < 0.5 else "high"

# 5. Get explanation
feature_importance = model.feature_importances_
top_factors = get_top_factors(features, feature_importance)

# 6. Generate natural language explanation
explanation_prompt = f"""
User wants to go to gym at 6 PM on Friday.
Prediction: {prediction_proba*100:.0f}% success probability
Top factors:
- Friday evenings: historically 45% success rate
- Current energy level: 6/10
- Competing tasks: 2 (meeting until 5:30, dinner plans at 8)

Generate a helpful explanation and suggestion.
"""

gemini_explanation = gemini_api.generate(explanation_prompt)

# 7. Return result
return {
    "success_probability": 0.34,
    "confidence": "high",
    "prediction": "low success",
    "explanation": gemini_explanation,
    "factors": top_factors,
    "suggestion": "Try tomorrow 9 AM instead (87% success rate)"
}
```

---

## 🧩 Component Details

### 1. Letta (MemGPT) Agent

**Configuration:**

```python
from letta import create_client, LLMConfig, EmbeddingConfig

# Create Letta client
client = create_client()

# Configure LLM
llm_config = LLMConfig(
    model="gemini-pro",
    model_endpoint_type="google_ai",
    context_window=32000
)

# Configure embeddings
embedding_config = EmbeddingConfig(
    embedding_model="text-embedding-004",
    embedding_endpoint_type="google_ai",
    embedding_dim=768
)

# Create agent
agent = client.create_agent(
    name="PersonalMemoryAgent",
    llm_config=llm_config,
    embedding_config=embedding_config,
    
    # Core memory (always active)
    memory={
        "human": "User profile and preferences",
        "persona": "You are a personal AI assistant..."
    },
    
    # System instructions
    system="You have access to the user's complete history..."
)
```

**Memory Structure:**

```python
# Core Memory (limited size, always active)
core_memory = {
    "human": """
        Name: [User's name]
        Goals: [Current active goals]
        Preferences: [Key preferences]
        Current context: [What user is working on now]
    """,
    "persona": """
        I am a personal AI assistant that remembers everything
        about the user. I provide personalized insights and advice.
    """
}

# Archival Memory (unlimited, searchable)
archival_memory = [
    "2026-02-14: User had productive day, completed project X",
    "2026-02-13: User felt stressed, team meeting went poorly",
    # ... all journal entries
]

# Recall Memory (recent conversation history)
recall_memory = [
    {"role": "user", "content": "How was my week?"},
    {"role": "assistant", "content": "Your week was..."},
    # ... last 10 messages
]
```

**Key Functions:**

```python
# Insert into archival memory
agent.archival_memory_insert("New journal entry content")

# Search archival memory
results = agent.archival_memory_search("times I felt stressed")

# Update core memory
agent.core_memory_append("goals", "Learn Python by June")

# Send message (triggers full memory search)
response = agent.user_message("Give me advice on my current goal")
```

---

### 2. ChromaDB (Vector Database)

**Setup:**

```python
import chromadb
from chromadb.config import Settings

# Initialize ChromaDB
chroma_client = chromadb.Client(Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="./data/chromadb"
))

# Create collection
collection = chroma_client.create_collection(
    name="journal_entries",
    metadata={"description": "All user journal entries"}
)
```

**Usage:**

```python
# Add documents
collection.add(
    documents=["Had great day at work, completed project"],
    embeddings=[[0.1, 0.2, 0.3, ...]],  # 768-dim vector
    metadatas=[{"date": "2026-02-14", "mood": 8}],
    ids=["entry_123"]
)

# Semantic search
results = collection.query(
    query_texts=["times I felt accomplished"],
    n_results=5,
    where={"mood": {"$gte": 7}}  # Filter by metadata
)

# Returns:
# {
#   "documents": [[...relevant entries...]],
#   "metadatas": [[...metadata...]],
#   "distances": [[0.23, 0.45, ...]]  # Similarity scores
# }
```

---

### 3. ML Models

#### Mood Predictor

```python
from sklearn.ensemble import RandomForestClassifier
import pandas as pd

# Feature engineering
def extract_mood_features(date, user_data):
    return {
        "day_of_week": date.weekday(),
        "hour": date.hour,
        "month": date.month,
        "sleep_hours": user_data.get_sleep_hours(date - 1),
        "exercise_yesterday": user_data.had_exercise(date - 1),
        "social_interactions": user_data.count_interactions(date),
        "work_vs_weekend": 1 if date.weekday() < 5 else 0,
        "avg_mood_last_week": user_data.avg_mood(date - 7, date),
        "stress_events_recent": user_data.count_stress_events(date - 3, date)
    }

# Training
X_train = pd.DataFrame([extract_mood_features(d, user) for d in training_dates])
y_train = [user.get_mood(d) for d in training_dates]

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Prediction
features = extract_mood_features(tomorrow, user)
predicted_mood = model.predict([features])[0]
confidence = model.predict_proba([features]).max()

print(f"Predicted mood: {predicted_mood}/10 (confidence: {confidence:.0%})")
```

#### Habit Success Predictor

```python
import xgboost as xgb

# Feature engineering
def extract_habit_features(habit, date, user_data):
    return {
        "habit_type": habit_encoder.transform([habit])[0],
        "day_of_week": date.weekday(),
        "hour": date.hour,
        "current_streak": user_data.get_streak(habit, date),
        "historical_success_rate": user_data.success_rate(habit),
        "success_rate_this_day": user_data.success_rate(habit, day=date.weekday()),
        "success_rate_this_hour": user_data.success_rate(habit, hour=date.hour),
        "energy_level": user_data.get_energy(date),
        "mood": user_data.get_mood(date),
        "competing_tasks": user_data.count_tasks(date),
        "days_since_last": user_data.days_since_last(habit, date)
    }

# Training with XGBoost
dtrain = xgb.DMatrix(X_train, label=y_train)

params = {
    "objective": "binary:logistic",
    "max_depth": 6,
    "learning_rate": 0.1,
    "n_estimators": 200
}

model = xgb.train(params, dtrain, num_boost_round=200)

# Prediction
features = extract_habit_features("gym", tomorrow, user)
dtest = xgb.DMatrix([features])
success_prob = model.predict(dtest)[0]

print(f"Gym success probability: {success_prob:.0%}")

# Feature importance
importance = model.get_score(importance_type='weight')
print(f"Top factors: {sorted(importance.items(), key=lambda x: x[1], reverse=True)[:3]}")
```

#### Energy Forecaster

```python
from prophet import Prophet

# Prepare data
df = pd.DataFrame({
    "ds": dates,  # Datetime
    "y": energy_levels,  # Energy (1-10)
    "day_of_week": [d.weekday() for d in dates],
    "sleep_hours": sleep_data,
    "exercise": exercise_data
})

# Train Prophet model
model = Prophet(
    yearly_seasonality=False,
    weekly_seasonality=True,
    daily_seasonality=True
)

# Add custom seasonality and regressors
model.add_seasonality(name='weekly', period=7, fourier_order=3)
model.add_regressor('sleep_hours')
model.add_regressor('exercise')

model.fit(df)

# Forecast next 7 days
future = model.make_future_dataframe(periods=7*24, freq='H')  # Hourly
future['sleep_hours'] = predicted_sleep  # Use predicted values
future['exercise'] = predicted_exercise

forecast = model.predict(future)

# Results
forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
# ds: timestamp
# yhat: predicted energy
# yhat_lower/upper: confidence interval
```

---

### 4. API Endpoints

**Complete API Specification:**

```python
# ==================== JOURNAL ENDPOINTS ====================

@app.post("/api/journal")
async def create_journal_entry(entry: JournalEntry) -> dict:
    """Create a new journal entry"""
    # Input: { date, mood, events, decisions, habits, energy_level }
    # Output: { id, status, message }

@app.get("/api/journal")
async def get_journal_entries(
    start_date: str = None,
    end_date: str = None,
    limit: int = 50
) -> List[JournalEntry]:
    """Get journal entries with optional date filtering"""

@app.get("/api/journal/{entry_id}")
async def get_journal_entry(entry_id: int) -> JournalEntry:
    """Get specific journal entry"""

@app.put("/api/journal/{entry_id}")
async def update_journal_entry(
    entry_id: int,
    entry: JournalEntry
) -> dict:
    """Update existing journal entry"""

@app.delete("/api/journal/{entry_id}")
async def delete_journal_entry(entry_id: int) -> dict:
    """Delete journal entry"""

# ==================== CHAT ENDPOINTS ====================

@app.post("/api/chat")
async def chat(message: str) -> ChatResponse:
    """Send message to AI assistant"""
    # Input: { message: "How have I been feeling?" }
    # Output: { 
    #   response: "Based on your last week...",
    #   sources: [...relevant entries...],
    #   confidence: 0.85
    # }

@app.get("/api/chat/history")
async def get_chat_history(limit: int = 20) -> List[ChatMessage]:
    """Get recent chat history"""

# ==================== PREDICTION ENDPOINTS ====================

@app.post("/api/predict/mood")
async def predict_mood(date: str) -> MoodPrediction:
    """Predict mood for a specific date"""
    # Output: {
    #   predicted_mood: 7.2,
    #   confidence: 0.84,
    #   factors: [...],
    #   explanation: "..."
    # }

@app.post("/api/predict/habit")
async def predict_habit_success(
    habit: str,
    date: str,
    time: str
) -> HabitPrediction:
    """Predict success probability for a habit"""
    # Output: {
    #   success_probability: 0.78,
    #   recommendation: "high",
    #   factors: [...],
    #   suggestion: "..."
    # }

@app.get("/api/predict/energy")
async def predict_energy(days_ahead: int = 7) -> EnergyForecast:
    """Forecast energy levels"""
    # Output: {
    #   forecast: [{date, hour, energy, confidence}, ...],
    #   peak_times: [...],
    #   low_times: [...]
    # }

@app.post("/api/predict/goal")
async def predict_goal_achievement(goal: Goal) -> GoalPrediction:
    """Predict goal achievement probability"""

# ==================== ANALYTICS ENDPOINTS ====================

@app.get("/api/analytics/dashboard")
async def get_dashboard_data() -> DashboardData:
    """Get complete dashboard analytics"""
    # Output: {
    #   mood_trend: {...},
    #   habit_stats: {...},
    #   goal_progress: {...},
    #   insights: [...]
    # }

@app.get("/api/analytics/patterns")
async def analyze_patterns(
    category: str,
    lookback_days: int = 90
) -> PatternAnalysis:
    """Analyze behavioral patterns"""

@app.get("/api/analytics/insights")
async def get_insights() -> List[Insight]:
    """Get AI-generated insights"""
    # Output: [
    #   {
    #     type: "pattern",
    #     title: "You're more productive after exercise",
    #     description: "...",
    #     confidence: 0.91,
    #     actionable: true,
    #     suggestion: "..."
    #   }
    # ]

# ==================== GOAL ENDPOINTS ====================

@app.post("/api/goals")
async def create_goal(goal: Goal) -> dict:
    """Create a new goal"""

@app.get("/api/goals")
async def get_goals(status: str = "active") -> List[Goal]:
    """Get user goals"""

@app.put("/api/goals/{goal_id}")
async def update_goal(goal_id: int, goal: Goal) -> dict:
    """Update goal"""

@app.get("/api/goals/{goal_id}/progress")
async def get_goal_progress(goal_id: int) -> GoalProgress:
    """Get detailed goal progress"""

# ==================== SEARCH ENDPOINTS ====================

@app.post("/api/search")
async def semantic_search(query: str, limit: int = 10) -> SearchResults:
    """Semantic search across all journal entries"""
    # Uses ChromaDB for vector similarity search

@app.post("/api/search/similar")
async def find_similar_entries(entry_id: int) -> List[JournalEntry]:
    """Find entries similar to a specific entry"""

# ==================== ML MODEL ENDPOINTS ====================

@app.post("/api/models/retrain")
async def retrain_models(model_name: str = "all") -> dict:
    """Trigger model retraining"""

@app.get("/api/models/performance")
async def get_model_performance() -> ModelMetrics:
    """Get ML model performance metrics"""

# ==================== EXPORT/IMPORT ENDPOINTS ====================

@app.get("/api/export")
async def export_data(format: str = "json") -> FileResponse:
    """Export all user data"""

@app.post("/api/import")
async def import_data(file: UploadFile) -> dict:
    """Import data from file"""

# ==================== SYSTEM ENDPOINTS ====================

@app.get("/api/health")
async def health_check() -> dict:
    """System health check"""

@app.get("/api/stats")
async def get_stats() -> SystemStats:
    """Get system statistics"""
```

---

## 🗄️ Database Schema

### SQLite Schema

```sql
-- ==================== USERS TABLE ====================
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    preferences JSON  -- User preferences as JSON
);

-- ==================== JOURNAL ENTRIES ====================
CREATE TABLE journal_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    entry_date DATE NOT NULL,
    entry_time TIME,
    
    -- Content
    title VARCHAR(200),
    content TEXT NOT NULL,
    
    -- Structured data
    mood INTEGER CHECK(mood >= 1 AND mood <= 10),
    energy_level INTEGER CHECK(energy_level >= 1 AND energy_level <= 10),
    stress_level INTEGER CHECK(stress_level >= 1 AND stress_level <= 10),
    
    -- Tags and categories
    tags JSON,  -- ["work", "personal", "health"]
    category VARCHAR(50),  -- "work", "personal", "health", etc.
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_journal_date ON journal_entries(entry_date);
CREATE INDEX idx_journal_user ON journal_entries(user_id);

-- ==================== EVENTS ====================
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    journal_entry_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    
    event_title VARCHAR(200) NOT NULL,
    event_description TEXT,
    event_type VARCHAR(50),  -- "meeting", "social", "achievement", etc.
    importance INTEGER CHECK(importance >= 1 AND importance <= 5),
    
    event_date DATE NOT NULL,
    event_time TIME,
    duration_minutes INTEGER,
    
    outcome VARCHAR(20),  -- "positive", "negative", "neutral"
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (journal_entry_id) REFERENCES journal_entries(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ==================== DECISIONS ====================
CREATE TABLE decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    journal_entry_id INTEGER,
    user_id INTEGER NOT NULL,
    
    decision_title VARCHAR(200) NOT NULL,
    decision_description TEXT,
    decision_category VARCHAR(50),  -- "career", "health", "finance", etc.
    
    decision_date DATE NOT NULL,
    decision_time TIME,
    
    -- Decision metadata
    importance INTEGER CHECK(importance >= 1 AND importance <= 5),
    confidence INTEGER CHECK(confidence >= 1 AND confidence <= 10),
    emotional_state VARCHAR(50),  -- mood when deciding
    
    -- Outcome tracking
    outcome_expected TEXT,  -- What you hoped would happen
    outcome_actual TEXT,    -- What actually happened
    satisfaction INTEGER CHECK(satisfaction >= 1 AND satisfaction <= 10),
    outcome_date DATE,      -- When outcome became clear
    
    -- Analysis
    reversed BOOLEAN DEFAULT FALSE,  -- Changed your mind?
    reversal_date DATE,
    reversal_reason TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (journal_entry_id) REFERENCES journal_entries(id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ==================== HABITS ====================
CREATE TABLE habits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    
    habit_name VARCHAR(100) NOT NULL,
    habit_description TEXT,
    habit_category VARCHAR(50),  -- "health", "productivity", "learning", etc.
    
    -- Configuration
    target_frequency VARCHAR(50),  -- "daily", "3x_per_week", "weekly", etc.
    target_days JSON,  -- [1, 3, 5] for Mon, Wed, Fri
    target_time TIME,
    
    -- Status
    status VARCHAR(20) DEFAULT 'active',  -- "active", "paused", "completed"
    
    start_date DATE NOT NULL,
    end_date DATE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ==================== HABIT LOGS ====================
CREATE TABLE habit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    habit_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    journal_entry_id INTEGER,
    
    log_date DATE NOT NULL,
    log_time TIME,
    
    completed BOOLEAN NOT NULL,
    
    -- Context
    difficulty INTEGER CHECK(difficulty >= 1 AND difficulty <= 5),
    satisfaction INTEGER CHECK(satisfaction >= 1 AND satisfaction <= 5),
    notes TEXT,
    
    -- Why if not completed
    skip_reason VARCHAR(100),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (journal_entry_id) REFERENCES journal_entries(id) ON DELETE SET NULL
);

CREATE INDEX idx_habit_logs_date ON habit_logs(log_date);
CREATE INDEX idx_habit_logs_habit ON habit_logs(habit_id);

-- ==================== GOALS ====================
CREATE TABLE goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    
    goal_title VARCHAR(200) NOT NULL,
    goal_description TEXT,
    goal_category VARCHAR(50),  -- "career", "health", "learning", etc.
    
    -- Timeline
    start_date DATE NOT NULL,
    target_date DATE,
    completed_date DATE,
    
    -- Status
    status VARCHAR(20) DEFAULT 'active',  -- "active", "completed", "abandoned"
    progress INTEGER DEFAULT 0 CHECK(progress >= 0 AND progress <= 100),
    
    -- Metadata
    priority INTEGER CHECK(priority >= 1 AND priority <= 5),
    is_recurring BOOLEAN DEFAULT FALSE,
    
    -- Outcome
    achievement_level INTEGER CHECK(achievement_level >= 1 AND achievement_level <= 5),
    satisfaction INTEGER CHECK(satisfaction >= 1 AND satisfaction <= 10),
    completion_notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ==================== GOAL MILESTONES ====================
CREATE TABLE goal_milestones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_id INTEGER NOT NULL,
    
    milestone_title VARCHAR(200) NOT NULL,
    milestone_description TEXT,
    target_date DATE,
    completed_date DATE,
    completed BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE CASCADE
);

-- ==================== MOOD LOGS ====================
CREATE TABLE mood_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    journal_entry_id INTEGER,
    
    log_date DATE NOT NULL,
    log_time TIME NOT NULL,
    
    mood_value INTEGER NOT NULL CHECK(mood_value >= 1 AND mood_value <= 10),
    energy_level INTEGER CHECK(energy_level >= 1 AND energy_level <= 10),
    stress_level INTEGER CHECK(stress_level >= 1 AND stress_level <= 10),
    
    -- Context
    mood_tags JSON,  -- ["happy", "motivated", "anxious"]
    trigger TEXT,    -- What caused this mood
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (journal_entry_id) REFERENCES journal_entries(id) ON DELETE SET NULL
);

CREATE INDEX idx_mood_logs_date ON mood_logs(log_date);

-- ==================== PREDICTIONS ====================
CREATE TABLE predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    
    prediction_type VARCHAR(50) NOT NULL,  -- "mood", "habit", "energy", "goal"
    prediction_target VARCHAR(100),  -- What was predicted (habit name, goal, etc.)
    prediction_date DATE NOT NULL,      -- When prediction was made
    target_date DATE NOT NULL,          -- What date was predicted
    
    -- Prediction details
    predicted_value REAL NOT NULL,
    confidence REAL NOT NULL,
    
    -- Verification
    actual_value REAL,
    actual_date DATE,
    prediction_accuracy REAL,  -- Calculated after actual value known
    
    -- Model info
    model_name VARCHAR(50),
    model_version VARCHAR(20),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ==================== INSIGHTS ====================
CREATE TABLE insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    
    insight_type VARCHAR(50) NOT NULL,  -- "pattern", "anomaly", "suggestion", "warning"
    insight_category VARCHAR(50),  -- "mood", "productivity", "habits", etc.
    
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    
    confidence REAL NOT NULL,
    importance INTEGER CHECK(importance >= 1 AND importance <= 5),
    
    actionable BOOLEAN DEFAULT FALSE,
    action_taken BOOLEAN DEFAULT FALSE,
    action_date DATE,
    
    -- Supporting data
    supporting_data JSON,  -- Evidence for the insight
    
    -- Status
    dismissed BOOLEAN DEFAULT FALSE,
    helpful_rating INTEGER CHECK(helpful_rating >= 1 AND helpful_rating <= 5),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,  -- Some insights are time-sensitive
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ==================== ML MODELS METADATA ====================
CREATE TABLE ml_models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    
    model_name VARCHAR(100) NOT NULL,  -- "mood_predictor", "habit_success", etc.
    model_version VARCHAR(20) NOT NULL,
    model_type VARCHAR(50),  -- "RandomForest", "XGBoost", etc.
    
    -- Training metadata
    training_date TIMESTAMP NOT NULL,
    training_samples INTEGER,
    
    -- Performance metrics
    accuracy REAL,
    precision_score REAL,
    recall_score REAL,
    f1_score REAL,
    mae REAL,  -- Mean Absolute Error
    rmse REAL,  -- Root Mean Squared Error
    
    -- Model file
    model_file_path VARCHAR(500),
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ==================== FEATURE STORE ====================
-- Stores extracted features for ML models
CREATE TABLE ml_features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    feature_date DATE NOT NULL,
    
    -- Features stored as JSON for flexibility
    features JSON NOT NULL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_ml_features_date ON ml_features(feature_date);

-- ==================== CHAT HISTORY ====================
CREATE TABLE chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    
    role VARCHAR(20) NOT NULL,  -- "user" or "assistant"
    message TEXT NOT NULL,
    
    -- Context
    related_journal_entries JSON,  -- IDs of relevant entries
    sources JSON,  -- Sources used to generate response
    
    -- Metadata
    tokens_used INTEGER,
    model_used VARCHAR(50),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_chat_history_user ON chat_history(user_id);
CREATE INDEX idx_chat_history_created ON chat_history(created_at);

-- ==================== LETTA MEMORY ====================
-- Stores Letta's persistent memory
CREATE TABLE letta_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    
    memory_type VARCHAR(20) NOT NULL,  -- "core", "archival", "recall"
    memory_key VARCHAR(100),  -- For core memory ("human", "persona")
    memory_content TEXT NOT NULL,
    
    -- For archival search
    embedding_id VARCHAR(100),  -- Reference to ChromaDB
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ==================== SYSTEM LOGS ====================
CREATE TABLE system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    log_level VARCHAR(20) NOT NULL,  -- "INFO", "WARNING", "ERROR"
    log_source VARCHAR(100),  -- Component that generated log
    message TEXT NOT NULL,
    details JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 💰 Cost Analysis

### Free Tier Breakdown

```yaml
Gemini API (Google):
  tier: FREE
  limits:
    requests_per_minute: 15
    requests_per_day: 1500
    tokens_per_minute: 1000000
    tokens_per_day: unlimited
  cost: $0/month
  sufficient_for: Personal use (typical: 50-200 requests/day)

ChromaDB:
  tier: FREE (self-hosted)
  cost: $0/month
  storage: Unlimited (on your device)

Letta (MemGPT):
  tier: FREE (open source)
  cost: $0/month
  
ML Libraries:
  scikit-learn: FREE
  XGBoost: FREE
  Prophet: FREE
  pandas: FREE
  numpy: FREE
  cost: $0/month

Total Monthly Cost: $0
```

### Paid Alternatives (Optional)

```yaml
If you exceed free tier:

OpenAI GPT-4:
  cost_per_1k_tokens: 
    input: $0.03
    output: $0.06
  estimated_monthly: $5-20 (depending on usage)

Claude API:
  cost_per_1k_tokens:
    input: $0.025
    output: $0.125
  estimated_monthly: $8-25

Pinecone (Vector DB alternative):
  free_tier: 1 index, 100k vectors
  paid_tier: $70/month (more capacity)
  
Cloud Hosting (if not self-hosted):
  AWS/GCP/Azure: $10-50/month
  DigitalOcean: $5-20/month
```

### Cost Optimization Tips

1. **Use Gemini Free Tier**: Generous limits for personal use
2. **Self-host everything**: ChromaDB, Letta, ML models (all local)
3. **Batch predictions**: Run ML models once daily, not per request
4. **Cache responses**: Store common queries
5. **Optimize embeddings**: Don't re-embed unchanged content

**Realistic monthly cost for personal use: $0**

---

## 🔒 Privacy & Security

### Data Privacy

```yaml
Data Location:
  - All data stored locally on YOUR device
  - SQLite database: /data/database.db
  - ChromaDB: /data/chromadb/
  - ML models: /data/models/
  
External API Calls:
  - Gemini API: Only when you request AI responses
  - What's sent: Your query + relevant context
  - What's NOT sent: Your entire database
  - Retention: Google says no data retention for API calls
  - Encryption: HTTPS (encrypted in transit)

Cloud Storage:
  - Default: NONE (everything local)
  - Optional: Can add encrypted cloud backup
  
Access Control:
  - Single-user system (no authentication by default)
  - Can add: Password protection, encryption at rest
```

### Security Best Practices

```python
# 1. Database Encryption (Optional)
from sqlalchemy_encrypt import EncryptedType
from sqlalchemy import String

# Encrypt sensitive fields
class JournalEntry(Base):
    content = Column(EncryptedType(String, 'your-secret-key'))

# 2. API Key Protection
# Store in environment variables, never in code
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 3. CORS Configuration (limit origins)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Only your frontend
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# 4. Input Validation
from pydantic import BaseModel, validator

class JournalEntry(BaseModel):
    content: str
    
    @validator('content')
    def content_must_not_be_empty(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Content cannot be empty')
        return v

# 5. Rate Limiting
from slowapi import Limiter

limiter = Limiter(key_func=lambda: "user")

@app.post("/api/chat")
@limiter.limit("30/minute")  # Max 30 requests per minute
async def chat(request: Request, message: str):
    ...
```

### Privacy Levels

**Level 1: Maximum Privacy (Recommended)**
```
✅ All data local (SQLite, ChromaDB)
✅ Use Gemini API (no data retention)
✅ No cloud storage
✅ Network-isolated option available
```

**Level 2: Balanced**
```
✅ Data local
✅ Encrypted cloud backup
✅ Use Gemini API
```

**Level 3: Fully Cloud**
```
⚠️ Data in cloud database
⚠️ Vector DB hosted (Pinecone)
⚠️ More convenient, less private
```

---

## 📦 Setup Instructions

### Prerequisites

```bash
# Required software
- Python 3.10 or higher
- Node.js 18+ and npm
- Git
- 8GB RAM minimum (16GB recommended for ML)
- 5GB free disk space

# Optional
- Docker & Docker Compose (for containerized setup)
- CUDA-capable GPU (for faster ML training)
```

### Quick Start (Docker - Easiest)

```bash
# 1. Clone repository
git clone https://github.com/yourusername/personal-ai-system.git
cd personal-ai-system

# 2. Create .env file
cat > .env << EOF
GEMINI_API_KEY=your_gemini_api_key_here
EOF

# Get free API key at: https://makersuite.google.com/app/apikey

# 3. Start everything with Docker
docker-compose up -d

# 4. Access application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs

# That's it! 🎉
```

### Manual Setup (More Control)

#### Backend Setup

```bash
# 1. Navigate to backend directory
cd backend

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# 5. Initialize database
python scripts/init_db.py

# 6. Start backend server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Backend running at: http://localhost:8000
```

#### Frontend Setup

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Configure API endpoint
cp .env.example .env
# Edit .env:
# VITE_API_URL=http://localhost:8000

# 4. Start development server
npm run dev

# Frontend running at: http://localhost:3000
```

#### Letta Setup

```bash
# Letta is installed with backend dependencies
# Configure Letta

cd backend

# Create Letta configuration
python scripts/setup_letta.py

# This will:
# - Configure Letta with Gemini API
# - Create initial agent
# - Set up memory structure
# - Test connection
```

#### ChromaDB Setup

```bash
# ChromaDB is installed with backend dependencies
# Initialize ChromaDB

python scripts/init_chromadb.py

# This will:
# - Create collections
# - Set up indexing
# - Test vector search
```

### Project Structure

```
personal-ai-system/
│
├── backend/                    # Python FastAPI backend
│   ├── main.py                # FastAPI app entry point
│   ├── requirements.txt       # Python dependencies
│   ├── .env.example          # Environment variables template
│   │
│   ├── api/                   # API endpoints
│   │   ├── journal.py        # Journal endpoints
│   │   ├── chat.py           # Chat endpoints
│   │   ├── predictions.py    # ML prediction endpoints
│   │   ├── analytics.py      # Analytics endpoints
│   │   └── goals.py          # Goal management endpoints
│   │
│   ├── models/                # Database models
│   │   ├── journal.py
│   │   ├── user.py
│   │   ├── habits.py
│   │   └── goals.py
│   │
│   ├── services/              # Business logic
│   │   ├── letta_service.py  # Letta integration
│   │   ├── rag_service.py    # ChromaDB/RAG
│   │   ├── ml_service.py     # ML predictions
│   │   └── gemini_service.py # Gemini API wrapper
│   │
│   ├── ml/                    # Machine learning
│   │   ├── models/           # Trained models storage
│   │   ├── mood_predictor.py
│   │   ├── habit_predictor.py
│   │   ├── energy_forecaster.py
│   │   ├── feature_engineering.py
│   │   └── training_pipeline.py
│   │
│   ├── utils/                 # Utilities
│   │   ├── database.py       # DB connection
│   │   ├── embeddings.py     # Embedding generation
│   │   └── helpers.py
│   │
│   ├── scripts/               # Setup scripts
│   │   ├── init_db.py        # Initialize database
│   │   ├── setup_letta.py    # Configure Letta
│   │   ├── init_chromadb.py  # Set up ChromaDB
│   │   └── seed_data.py      # Sample data for testing
│   │
│   └── data/                  # Data storage (gitignored)
│       ├── database.db       # SQLite database
│       ├── chromadb/         # Vector database
│       └── models/           # Trained ML models
│
├── frontend/                  # React frontend
│   ├── package.json
│   ├── vite.config.js
│   ├── .env.example
│   │
│   ├── public/                # Static assets
│   │   └── assets/
│   │
│   └── src/
│       ├── App.jsx           # Main app component
│       ├── main.jsx          # Entry point
│       │
│       ├── components/        # React components
│       │   ├── Journal/
│       │   │   ├── JournalEntry.jsx
│       │   │   ├── JournalList.jsx
│       │   │   └── JournalForm.jsx
│       │   │
│       │   ├── Chat/
│       │   │   ├── ChatInterface.jsx
│       │   │   └── MessageBubble.jsx
│       │   │
│       │   ├── Dashboard/
│       │   │   ├── Dashboard.jsx
│       │   │   ├── MoodChart.jsx
│       │   │   ├── HabitTracker.jsx
│       │   │   ├── GoalProgress.jsx
│       │   │   └── InsightsPanel.jsx
│       │   │
│       │   ├── Predictions/
│       │   │   ├── MoodForecast.jsx
│       │   │   ├── EnergyChart.jsx
│       │   │   └── HabitPrediction.jsx
│       │   │
│       │   └── Common/
│       │       ├── Navbar.jsx
│       │       ├── Sidebar.jsx
│       │       └── Loading.jsx
│       │
│       ├── services/          # API services
│       │   ├── api.js        # API client
│       │   ├── journal.js
│       │   ├── chat.js
│       │   └── predictions.js
│       │
│       ├── hooks/             # Custom React hooks
│       │   ├── useJournal.js
│       │   ├── useChat.js
│       │   └── usePredictions.js
│       │
│       ├── utils/             # Utilities
│       │   ├── formatters.js
│       │   └── helpers.js
│       │
│       └── styles/            # CSS files
│           └── globals.css
│
├── docker/                    # Docker configuration
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
│
├── docker-compose.yml         # Docker Compose config
├── README.md                  # Project documentation
├── .gitignore
└── LICENSE
```

### Configuration Files

**backend/requirements.txt**
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
pydantic==2.5.3
python-dotenv==1.0.0

# Letta & AI
letta==0.3.0
google-generativeai==0.3.2
chromadb==0.4.22
langchain==0.1.0

# ML
scikit-learn==1.3.2
xgboost==2.0.3
prophet==1.1.5
pandas==2.1.4
numpy==1.26.3
scipy==1.11.4

# Utilities
python-multipart==0.0.6
aiofiles==23.2.1
httpx==0.26.0
```

**frontend/package.json**
```json
{
  "name": "personal-ai-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.21.1",
    "recharts": "^2.10.3",
    "lucide-react": "^0.307.0",
    "date-fns": "^3.0.6",
    "axios": "^1.6.5"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.1",
    "vite": "^5.0.11",
    "tailwindcss": "^3.4.1",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.33"
  }
}
```

**docker-compose.yml**
```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: ../docker/Dockerfile.backend
    ports:
      - "8000:8000"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - DATABASE_URL=sqlite:///./data/database.db
    volumes:
      - ./backend/data:/app/data
      - ./backend/ml/models:/app/ml/models
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: ../docker/Dockerfile.frontend
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  backend_data:
  ml_models:
```

### Initial Data Seeding (Optional)

```bash
# Add sample data for testing
python backend/scripts/seed_data.py

# This creates:
# - 30 days of sample journal entries
# - Sample goals and habits
# - Some chat history
# - Allows immediate testing of predictions
```

---

## 🚀 Future Enhancements

### Phase 1 (Next 3 months)

```
✅ Multi-agent system (specialized AI agents)
✅ Voice input for journal entries
✅ Mobile-responsive improvements
✅ Data export/import (JSON, CSV, PDF)
✅ Dark mode
✅ Notification system
✅ Calendar integration
```

### Phase 2 (3-6 months)

```
✅ Mobile app (React Native)
✅ Collaborative features (share insights with therapist/coach)
✅ Integration with wearables (sleep, steps, heart rate)
✅ Advanced visualizations (3D charts, heatmaps)
✅ Custom ML model training (upload your own data)
✅ API for third-party integrations
```

### Phase 3 (6-12 months)

```
✅ Multi-user support (family/team features)
✅ Marketplace for custom AI personalities
✅ Advanced NLP (sentiment analysis, entity extraction)
✅ Automated goal tracking (parse from conversations)
✅ Integration with productivity tools (Notion, Todoist)
✅ AI-powered journaling prompts
✅ Therapy-mode (specialized for mental health)
```

---

## 📊 Performance Benchmarks

### Expected Performance

```yaml
API Response Times:
  journal_create: <100ms
  chat_simple: 2-4 seconds (Gemini API)
  chat_complex: 5-8 seconds (with RAG)
  prediction_mood: <500ms
  prediction_habit: <300ms
  semantic_search: <200ms
  
ML Training Times:
  mood_predictor: 2-5 minutes (weekly retraining)
  habit_predictor: 1-3 minutes
  energy_forecaster: 3-7 minutes
  
Database Queries:
  simple_select: <10ms
  complex_join: <50ms
  full_text_search: <100ms
  
Memory Usage:
  backend_idle: ~200MB
  backend_active: ~500MB
  chromadb: ~100MB + data size
  ml_models: ~300MB (all loaded)
  frontend: ~150MB
```

---

## 🐛 Troubleshooting

### Common Issues

**1. Gemini API Key Error**
```bash
Error: "API key not valid"

Solution:
1. Get free API key: https://makersuite.google.com/app/apikey
2. Add to .env file: GEMINI_API_KEY=your_key_here
3. Restart backend: uvicorn main:app --reload
```

**2. Letta Connection Error**
```bash
Error: "Cannot connect to Letta"

Solution:
# Reinstall Letta
pip uninstall letta
pip install letta==0.3.0

# Reset Letta config
python scripts/setup_letta.py
```

**3. ChromaDB Persistence Error**
```bash
Error: "ChromaDB data not persisting"

Solution:
# Ensure correct path in code
chroma_client = chromadb.Client(Settings(
    persist_directory="./data/chromadb"  # Absolute path recommended
))

# Manually create directory
mkdir -p data/chromadb
```

**4. ML Model Training Fails**
```bash
Error: "Not enough data for training"

Solution:
# Need minimum 30 entries for training
# Use seed data:
python scripts/seed_data.py

# Or wait until you have 30+ real entries
```

**5. Frontend Can't Connect to Backend**
```bash
Error: "Network Error" in browser console

Solution:
1. Check backend is running: http://localhost:8000/docs
2. Check CORS settings in backend
3. Verify .env in frontend: VITE_API_URL=http://localhost:8000
4. Clear browser cache
```

---

## 📚 Additional Resources

### Documentation Links

- **Letta (MemGPT)**: https://github.com/cpacker/MemGPT
- **Gemini API**: https://ai.google.dev/docs
- **ChromaDB**: https://docs.trychroma.com/
- **FastAPI**: https://fastapi.tiangolo.com/
- **React**: https://react.dev/
- **scikit-learn**: https://scikit-learn.org/
- **XGBoost**: https://xgboost.readthedocs.io/
- **Prophet**: https://facebook.github.io/prophet/

### Learning Resources

- **ML for Personal Analytics**: [Course Link]
- **Building AI Agents**: [Tutorial Link]
- **RAG Systems**: [Guide Link]
- **FastAPI Best Practices**: [Documentation Link]

---

## 🤝 Contributing

This is a personal project, but contributions are welcome!

```bash
# 1. Fork the repository
# 2. Create feature branch
git checkout -b feature/amazing-feature

# 3. Commit changes
git commit -m "Add amazing feature"

# 4. Push to branch
git push origin feature/amazing-feature

# 5. Open Pull Request
```

---

## 📄 License

MIT License - Feel free to use and modify for personal use.

---

## 🎯 Quick Start Checklist

```
☐ Install Python 3.10+
☐ Install Node.js 18+
☐ Get Gemini API key (free)
☐ Clone repository
☐ Set up backend (pip install -r requirements.txt)
☐ Set up frontend (npm install)
☐ Configure .env files
☐ Initialize database (python scripts/init_db.py)
☐ Start backend (uvicorn main:app --reload)
☐ Start frontend (npm run dev)
☐ Access at http://localhost:3000
☐ Create first journal entry
☐ Chat with AI
☐ Explore dashboard
☐ Wait 30 days for ML predictions to activate
```

---

## 💡 Tips for Best Results

1. **Journal daily**: More data = better predictions
2. **Be detailed**: Rich context helps AI understand you better
3. **Track consistently**: Log mood, energy, habits regularly
4. **Review insights weekly**: AI gets smarter over time
5. **Update goals**: Keep your goals current in the system
6. **Ask questions**: The more you interact, the better it learns
7. **Provide feedback**: Rate predictions to improve accuracy

---

## 📞 Support

For issues, questions, or suggestions:
- GitHub Issues: [Link to repo]
- Email: your-email@example.com
- Discord: [Community link]

---

**Last Updated**: February 14, 2026
**Version**: 1.0.0
**Status**: Production Ready ✅

---

