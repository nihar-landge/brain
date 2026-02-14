# Complete Database Architecture
## Personal AI Memory System - Database Design

**Last Updated:** February 14, 2026  
**Version:** 1.0

---

## 🎯 Database Strategy Overview

### **Core Principle: Single Source of Truth**

```
┌─────────────────────────────────────────────────────┐
│              DATABASE ARCHITECTURE                   │
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │   SQLite (MASTER - Single Source of Truth) │    │
│  │                                             │    │
│  │  - All structured data                      │    │
│  │  - Authoritative copy                       │    │
│  │  - Source for all queries                   │    │
│  │  - Handles transactions                     │    │
│  └────────────────────────────────────────────┘    │
│              ↓                                       │
│         (Syncs to)                                   │
│              ↓                                       │
│  ┌────────────────────────────────────────────┐    │
│  │   ChromaDB (INDEX - Vector Search)         │    │
│  │                                             │    │
│  │  - Vector embeddings only                   │    │
│  │  - References SQLite IDs                    │    │
│  │  - Used for semantic search                 │    │
│  │  - Recreatable from SQLite                  │    │
│  └────────────────────────────────────────────┘    │
│              ↓                                       │
│         (Powers)                                     │
│              ↓                                       │
│  ┌────────────────────────────────────────────┐    │
│  │   Letta Memory (CACHE - Active Context)    │    │
│  │                                             │    │
│  │  - Core Memory (4KB active context)        │    │
│  │  - References SQLite for archival          │    │
│  │  - Temporary working memory                 │    │
│  └────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

---

## 📊 Complete Database Schema

### **Database: SQLite (Primary Storage)**

**Why SQLite:**
- ✅ Zero configuration
- ✅ Single file (easy backup)
- ✅ ACID compliant (reliable)
- ✅ Fast for single-user
- ✅ No server needed
- ✅ Perfect for local-first apps

---

## 🗃️ Table Definitions

### **1. Core Tables**

#### **Table: `users`**

```sql
CREATE TABLE users (
    -- Primary Key
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- User Info
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255),
    full_name VARCHAR(200),
    
    -- Profile
    timezone VARCHAR(50) DEFAULT 'UTC',
    date_format VARCHAR(20) DEFAULT 'YYYY-MM-DD',
    
    -- Preferences (JSON)
    preferences TEXT DEFAULT '{}',
    -- {
    --   "theme": "monochrome",
    --   "notifications": true,
    --   "default_mood": 7,
    --   "ai_personality": "supportive"
    -- }
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE
);

-- Indexes
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
```

**Purpose:** Store user information and preferences

---

#### **Table: `journal_entries`** (CORE TABLE)

```sql
CREATE TABLE journal_entries (
    -- Primary Key
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Foreign Keys
    user_id INTEGER NOT NULL,
    
    -- Entry Content
    entry_date DATE NOT NULL,
    entry_time TIME DEFAULT CURRENT_TIME,
    title VARCHAR(200),
    content TEXT NOT NULL,  -- Main journal text
    
    -- Structured Data
    mood INTEGER CHECK(mood >= 1 AND mood <= 10),
    energy_level INTEGER CHECK(energy_level >= 1 AND energy_level <= 10),
    stress_level INTEGER CHECK(stress_level >= 1 AND stress_level <= 10),
    sleep_hours DECIMAL(3,1),  -- e.g., 7.5
    
    -- Categorization
    category VARCHAR(50),  -- 'personal', 'work', 'health', 'reflection'
    tags TEXT,  -- JSON array: ["productive", "anxious", "grateful"]
    
    -- Context
    location VARCHAR(200),
    weather VARCHAR(50),
    
    -- Embeddings Reference
    embedding_id VARCHAR(100),  -- Reference to ChromaDB
    embedding_generated_at TIMESTAMP,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,  -- Soft delete
    
    -- Constraints
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes (CRITICAL for performance)
CREATE INDEX idx_journal_user_date ON journal_entries(user_id, entry_date DESC);
CREATE INDEX idx_journal_mood ON journal_entries(mood);
CREATE INDEX idx_journal_created ON journal_entries(created_at DESC);
CREATE INDEX idx_journal_category ON journal_entries(category);
CREATE INDEX idx_journal_deleted ON journal_entries(deleted_at);  -- For soft deletes

-- Full-text search index (SQLite FTS5)
CREATE VIRTUAL TABLE journal_fts USING fts5(
    content,
    title,
    content='journal_entries',
    content_rowid='id'
);

-- Trigger to keep FTS in sync
CREATE TRIGGER journal_ai AFTER INSERT ON journal_entries BEGIN
    INSERT INTO journal_fts(rowid, content, title)
    VALUES (new.id, new.content, new.title);
END;

CREATE TRIGGER journal_au AFTER UPDATE ON journal_entries BEGIN
    UPDATE journal_fts SET content = new.content, title = new.title
    WHERE rowid = old.id;
END;

CREATE TRIGGER journal_ad AFTER DELETE ON journal_entries BEGIN
    DELETE FROM journal_fts WHERE rowid = old.id;
END;
```

**Purpose:** Primary storage for all journal entries

**Key Features:**
- Soft deletes (deleted_at)
- Full-text search support
- Multiple mood/energy tracking
- Embedding reference for ChromaDB

---

#### **Table: `events`**

```sql
CREATE TABLE events (
    -- Primary Key
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Foreign Keys
    journal_entry_id INTEGER,  -- Can be NULL for standalone events
    user_id INTEGER NOT NULL,
    
    -- Event Info
    event_title VARCHAR(200) NOT NULL,
    event_description TEXT,
    event_type VARCHAR(50),  -- 'meeting', 'achievement', 'social', 'health'
    
    -- Timing
    event_date DATE NOT NULL,
    event_time TIME,
    duration_minutes INTEGER,
    
    -- Significance
    importance INTEGER CHECK(importance >= 1 AND importance <= 5),
    emotional_impact INTEGER CHECK(emotional_impact >= -5 AND emotional_impact <= 5),
    
    -- Outcome
    outcome VARCHAR(20),  -- 'positive', 'negative', 'neutral', 'mixed'
    
    -- People Involved (JSON array)
    people TEXT DEFAULT '[]',  -- ["Alice", "Bob"]
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    FOREIGN KEY (journal_entry_id) REFERENCES journal_entries(id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_events_user_date ON events(user_id, event_date DESC);
CREATE INDEX idx_events_type ON events(event_type);
CREATE INDEX idx_events_importance ON events(importance);
```

**Purpose:** Track specific events/occurrences

---

#### **Table: `decisions`**

```sql
CREATE TABLE decisions (
    -- Primary Key
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Foreign Keys
    journal_entry_id INTEGER,
    user_id INTEGER NOT NULL,
    
    -- Decision Info
    decision_title VARCHAR(200) NOT NULL,
    decision_description TEXT,
    decision_category VARCHAR(50),  -- 'career', 'health', 'finance', 'relationship'
    
    -- Context
    decision_date DATE NOT NULL,
    decision_time TIME,
    
    -- Emotional State
    mood_when_decided INTEGER CHECK(mood_when_decided >= 1 AND mood_when_decided <= 10),
    confidence_level INTEGER CHECK(confidence_level >= 1 AND confidence_level <= 10),
    stress_level INTEGER CHECK(stress_level >= 1 AND stress_level <= 10),
    
    -- Decision Process
    time_to_decide_hours INTEGER,  -- How long did it take to decide?
    alternatives_considered INTEGER,
    consulted_people TEXT,  -- JSON array
    
    -- Importance
    importance INTEGER CHECK(importance >= 1 AND importance <= 5),
    
    -- Expected Outcome
    outcome_expected TEXT,
    success_criteria TEXT,
    
    -- Actual Outcome (filled later)
    outcome_actual TEXT,
    outcome_date DATE,
    satisfaction INTEGER CHECK(satisfaction >= 1 AND satisfaction <= 10),
    would_decide_same_again BOOLEAN,
    
    -- Reversal
    decision_reversed BOOLEAN DEFAULT FALSE,
    reversal_date DATE,
    reversal_reason TEXT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    FOREIGN KEY (journal_entry_id) REFERENCES journal_entries(id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_decisions_user_date ON decisions(user_id, decision_date DESC);
CREATE INDEX idx_decisions_category ON decisions(decision_category);
CREATE INDEX idx_decisions_satisfaction ON decisions(satisfaction);
```

**Purpose:** Track decisions and their outcomes for pattern analysis

---

#### **Table: `goals`**

```sql
CREATE TABLE goals (
    -- Primary Key
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Foreign Keys
    user_id INTEGER NOT NULL,
    parent_goal_id INTEGER,  -- For sub-goals
    
    -- Goal Info
    goal_title VARCHAR(200) NOT NULL,
    goal_description TEXT,
    goal_category VARCHAR(50),  -- 'career', 'health', 'learning', 'personal'
    
    -- Timeline
    start_date DATE NOT NULL,
    target_date DATE,
    completed_date DATE,
    
    -- Complexity
    complexity INTEGER CHECK(complexity >= 1 AND complexity <= 10),
    estimated_hours INTEGER,
    
    -- Status
    status VARCHAR(20) DEFAULT 'active',  -- 'active', 'completed', 'abandoned', 'on_hold'
    progress INTEGER DEFAULT 0 CHECK(progress >= 0 AND progress <= 100),
    
    -- Metadata
    priority INTEGER CHECK(priority >= 1 AND priority <= 5) DEFAULT 3,
    is_recurring BOOLEAN DEFAULT FALSE,
    recurrence_pattern VARCHAR(50),  -- 'daily', 'weekly', 'monthly'
    
    -- Motivation
    motivation_level INTEGER CHECK(motivation_level >= 1 AND motivation_level <= 10),
    why_important TEXT,
    
    -- Tracking
    last_progress_update DATE,
    
    -- Outcome (when completed/abandoned)
    achievement_level INTEGER CHECK(achievement_level >= 1 AND achievement_level <= 5),
    satisfaction INTEGER CHECK(satisfaction >= 1 AND satisfaction <= 10),
    completion_notes TEXT,
    lessons_learned TEXT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_goal_id) REFERENCES goals(id) ON DELETE SET NULL
);

-- Indexes
CREATE INDEX idx_goals_user_status ON goals(user_id, status);
CREATE INDEX idx_goals_target_date ON goals(target_date);
CREATE INDEX idx_goals_category ON goals(goal_category);
```

**Purpose:** Track short and long-term goals

---

#### **Table: `goal_milestones`**

```sql
CREATE TABLE goal_milestones (
    -- Primary Key
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Foreign Keys
    goal_id INTEGER NOT NULL,
    
    -- Milestone Info
    milestone_title VARCHAR(200) NOT NULL,
    milestone_description TEXT,
    milestone_order INTEGER,  -- Sequence in goal
    
    -- Timing
    target_date DATE,
    completed_date DATE,
    completed BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_milestones_goal ON goal_milestones(goal_id);
CREATE INDEX idx_milestones_completed ON goal_milestones(completed);
```

---

#### **Table: `habits`**

```sql
CREATE TABLE habits (
    -- Primary Key
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Foreign Keys
    user_id INTEGER NOT NULL,
    related_goal_id INTEGER,  -- Optional: link to goal
    
    -- Habit Info
    habit_name VARCHAR(100) NOT NULL,
    habit_description TEXT,
    habit_category VARCHAR(50),  -- 'health', 'productivity', 'learning', 'social'
    
    -- Configuration
    target_frequency VARCHAR(50),  -- 'daily', '3x_per_week', 'weekly'
    target_days TEXT,  -- JSON: [1, 3, 5] for Mon, Wed, Fri
    target_time TIME,
    reminder_enabled BOOLEAN DEFAULT TRUE,
    
    -- Status
    status VARCHAR(20) DEFAULT 'active',  -- 'active', 'paused', 'completed'
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    
    -- Timeline
    start_date DATE NOT NULL,
    end_date DATE,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (related_goal_id) REFERENCES goals(id) ON DELETE SET NULL
);

-- Indexes
CREATE INDEX idx_habits_user_status ON habits(user_id, status);
CREATE INDEX idx_habits_category ON habits(habit_category);
```

---

#### **Table: `habit_logs`**

```sql
CREATE TABLE habit_logs (
    -- Primary Key
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Foreign Keys
    habit_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    journal_entry_id INTEGER,
    
    -- Log Info
    log_date DATE NOT NULL,
    log_time TIME,
    
    -- Completion
    completed BOOLEAN NOT NULL,
    
    -- Context
    difficulty INTEGER CHECK(difficulty >= 1 AND difficulty <= 5),
    satisfaction INTEGER CHECK(satisfaction >= 1 AND satisfaction <= 5),
    energy_before INTEGER CHECK(energy_before >= 1 AND energy_before <= 10),
    energy_after INTEGER CHECK(energy_after >= 1 AND energy_after <= 10),
    
    -- Notes
    notes TEXT,
    skip_reason VARCHAR(100),  -- If not completed
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE(habit_id, log_date),  -- One log per habit per day
    FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (journal_entry_id) REFERENCES journal_entries(id) ON DELETE SET NULL
);

-- Indexes
CREATE INDEX idx_habit_logs_habit_date ON habit_logs(habit_id, log_date DESC);
CREATE INDEX idx_habit_logs_completed ON habit_logs(completed);
CREATE INDEX idx_habit_logs_user_date ON habit_logs(user_id, log_date DESC);
```

**Purpose:** Track daily habit completion

---

#### **Table: `mood_logs`**

```sql
CREATE TABLE mood_logs (
    -- Primary Key
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Foreign Keys
    user_id INTEGER NOT NULL,
    journal_entry_id INTEGER,
    
    -- Timing
    log_date DATE NOT NULL,
    log_time TIME NOT NULL,
    
    -- Mood Data
    mood_value INTEGER NOT NULL CHECK(mood_value >= 1 AND mood_value <= 10),
    energy_level INTEGER CHECK(energy_level >= 1 AND energy_level <= 10),
    stress_level INTEGER CHECK(stress_level >= 1 AND stress_level <= 10),
    anxiety_level INTEGER CHECK(anxiety_level >= 1 AND anxiety_level <= 10),
    
    -- Context
    mood_tags TEXT,  -- JSON: ["happy", "motivated", "tired"]
    trigger TEXT,  -- What caused this mood?
    activity TEXT,  -- What were you doing?
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (journal_entry_id) REFERENCES journal_entries(id) ON DELETE SET NULL
);

-- Indexes
CREATE INDEX idx_mood_logs_user_date ON mood_logs(user_id, log_date DESC, log_time DESC);
CREATE INDEX idx_mood_logs_value ON mood_logs(mood_value);
```

**Purpose:** Detailed mood tracking (can have multiple per day)

---

### **2. ML & Prediction Tables**

#### **Table: `predictions`**

```sql
CREATE TABLE predictions (
    -- Primary Key
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Foreign Keys
    user_id INTEGER NOT NULL,
    
    -- Prediction Info
    prediction_type VARCHAR(50) NOT NULL,  -- 'mood', 'habit_success', 'energy', 'goal_achievement'
    prediction_target VARCHAR(100),  -- What was predicted (habit name, goal ID, etc.)
    
    -- Timing
    prediction_date DATE NOT NULL,  -- When prediction was made
    target_date DATE NOT NULL,  -- What date was predicted for
    
    -- Prediction Results
    predicted_value REAL NOT NULL,
    confidence REAL NOT NULL CHECK(confidence >= 0 AND confidence <= 1),
    
    -- Model Info
    model_name VARCHAR(50),
    model_version VARCHAR(20),
    features_used TEXT,  -- JSON: feature values used
    
    -- Verification (filled when actual outcome known)
    actual_value REAL,
    actual_date DATE,
    prediction_error REAL,  -- |predicted - actual|
    prediction_accuracy REAL,  -- Calculated accuracy
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_predictions_user_type ON predictions(user_id, prediction_type);
CREATE INDEX idx_predictions_target_date ON predictions(target_date);
CREATE INDEX idx_predictions_model ON predictions(model_name, model_version);
```

**Purpose:** Store ML predictions and track accuracy

---

#### **Table: `ml_models`**

```sql
CREATE TABLE ml_models (
    -- Primary Key
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Foreign Keys
    user_id INTEGER NOT NULL,
    
    -- Model Info
    model_name VARCHAR(100) NOT NULL,  -- 'mood_predictor', 'habit_success_predictor'
    model_version VARCHAR(20) NOT NULL,
    model_type VARCHAR(50),  -- 'RandomForest', 'XGBoost', 'Prophet'
    
    -- Training Info
    training_date TIMESTAMP NOT NULL,
    training_samples INTEGER,
    training_duration_seconds INTEGER,
    
    -- Performance Metrics
    accuracy REAL,
    precision_score REAL,
    recall_score REAL,
    f1_score REAL,
    mae REAL,  -- Mean Absolute Error
    rmse REAL,  -- Root Mean Squared Error
    r2_score REAL,  -- R-squared
    
    -- Model Storage
    model_file_path VARCHAR(500),
    model_size_bytes INTEGER,
    
    -- Features
    feature_names TEXT,  -- JSON array
    feature_importance TEXT,  -- JSON object
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_ml_models_user_name ON ml_models(user_id, model_name);
CREATE INDEX idx_ml_models_active ON ml_models(is_active);
```

**Purpose:** Track ML model versions and performance

---

#### **Table: `ml_features`**

```sql
CREATE TABLE ml_features (
    -- Primary Key
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Foreign Keys
    user_id INTEGER NOT NULL,
    
    -- Feature Info
    feature_date DATE NOT NULL,
    feature_type VARCHAR(50),  -- 'mood', 'habit', 'energy'
    
    -- Features (JSON)
    features TEXT NOT NULL,
    -- {
    --   "day_of_week": 1,
    --   "hour": 14,
    --   "avg_mood_7d": 7.2,
    --   "sleep_hours": 7.5,
    --   "exercise_yesterday": true,
    --   ...
    -- }
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE(user_id, feature_date, feature_type),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_ml_features_user_date ON ml_features(user_id, feature_date DESC);
CREATE INDEX idx_ml_features_type ON ml_features(feature_type);
```

**Purpose:** Pre-computed features for ML models

---

### **3. AI & Memory Tables**

#### **Table: `chat_history`**

```sql
CREATE TABLE chat_history (
    -- Primary Key
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Foreign Keys
    user_id INTEGER NOT NULL,
    conversation_id VARCHAR(100),  -- Group related messages
    
    -- Message Info
    role VARCHAR(20) NOT NULL,  -- 'user' or 'assistant'
    message TEXT NOT NULL,
    
    -- Context
    related_journal_entries TEXT,  -- JSON array of entry IDs
    sources_used TEXT,  -- JSON: sources used for response
    
    -- AI Metadata
    tokens_used INTEGER,
    model_used VARCHAR(50),
    response_time_ms INTEGER,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_chat_user_time ON chat_history(user_id, created_at DESC);
CREATE INDEX idx_chat_conversation ON chat_history(conversation_id);
```

**Purpose:** Store chat conversations with AI

---

#### **Table: `insights`**

```sql
CREATE TABLE insights (
    -- Primary Key
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Foreign Keys
    user_id INTEGER NOT NULL,
    
    -- Insight Info
    insight_type VARCHAR(50) NOT NULL,  -- 'pattern', 'anomaly', 'suggestion', 'warning'
    insight_category VARCHAR(50),  -- 'mood', 'productivity', 'health', 'habits'
    
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    
    -- Confidence
    confidence REAL NOT NULL CHECK(confidence >= 0 AND confidence <= 1),
    importance INTEGER CHECK(importance >= 1 AND importance <= 5),
    
    -- Actionable
    is_actionable BOOLEAN DEFAULT FALSE,
    suggested_action TEXT,
    
    -- Supporting Data
    supporting_data TEXT,  -- JSON: evidence for insight
    related_entries TEXT,  -- JSON array of journal entry IDs
    
    -- User Interaction
    viewed BOOLEAN DEFAULT FALSE,
    viewed_at TIMESTAMP,
    dismissed BOOLEAN DEFAULT FALSE,
    dismissed_at TIMESTAMP,
    action_taken BOOLEAN DEFAULT FALSE,
    action_taken_at TIMESTAMP,
    
    -- Feedback
    helpful_rating INTEGER CHECK(helpful_rating >= 1 AND helpful_rating <= 5),
    feedback_notes TEXT,
    
    -- Expiry
    expires_at TIMESTAMP,  -- Time-sensitive insights
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_insights_user_type ON insights(user_id, insight_type);
CREATE INDEX idx_insights_dismissed ON insights(dismissed);
CREATE INDEX idx_insights_expires ON insights(expires_at);
```

**Purpose:** AI-generated insights and patterns

---

#### **Table: `letta_memory`**

```sql
CREATE TABLE letta_memory (
    -- Primary Key
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Foreign Keys
    user_id INTEGER NOT NULL,
    agent_id VARCHAR(100),  -- Letta agent ID
    
    -- Memory Info
    memory_type VARCHAR(20) NOT NULL,  -- 'core', 'archival', 'recall'
    memory_key VARCHAR(100),  -- For core memory: 'human', 'persona'
    memory_content TEXT NOT NULL,
    
    -- For archival memory
    embedding_id VARCHAR(100),  -- Reference to ChromaDB
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMP,
    
    -- Constraints
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_letta_user_type ON letta_memory(user_id, memory_type);
CREATE INDEX idx_letta_agent ON letta_memory(agent_id);
```

**Purpose:** Store Letta's memory state

---

### **4. System Tables**

#### **Table: `system_logs`**

```sql
CREATE TABLE system_logs (
    -- Primary Key
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Log Info
    log_level VARCHAR(20) NOT NULL,  -- 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    log_source VARCHAR(100),  -- Component that generated log
    message TEXT NOT NULL,
    
    -- Additional Data
    details TEXT,  -- JSON: additional details
    stack_trace TEXT,  -- For errors
    
    -- Context
    user_id INTEGER,
    request_id VARCHAR(100),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Indexes
CREATE INDEX idx_logs_level_time ON system_logs(log_level, created_at DESC);
CREATE INDEX idx_logs_source ON system_logs(log_source);
CREATE INDEX idx_logs_user ON system_logs(user_id);
```

---

#### **Table: `api_usage`**

```sql
CREATE TABLE api_usage (
    -- Primary Key
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- API Info
    api_name VARCHAR(50),  -- 'gemini_text', 'gemini_embedding'
    endpoint VARCHAR(200),
    
    -- Usage
    request_date DATE NOT NULL,
    request_count INTEGER DEFAULT 1,
    tokens_used INTEGER,
    
    -- Cost (if tracking)
    estimated_cost DECIMAL(10,4),
    
    -- Status
    successful_requests INTEGER DEFAULT 0,
    failed_requests INTEGER DEFAULT 0,
    rate_limit_hits INTEGER DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_api_usage_date ON api_usage(request_date DESC);
CREATE INDEX idx_api_usage_api ON api_usage(api_name);
```

---

## 🔄 Database Operations & Patterns

### **1. Data Flow: Creating a Journal Entry**

```python
# Step 1: Save to SQLite (MASTER)
def create_journal_entry(user_id: int, content: str, mood: int, **kwargs):
    """
    Create journal entry with full data consistency.
    """
    # Begin transaction
    with db.transaction():
        # 1. Insert into journal_entries
        entry = JournalEntry(
            user_id=user_id,
            entry_date=date.today(),
            content=content,
            mood=mood,
            **kwargs
        )
        db.add(entry)
        db.flush()  # Get entry.id
        
        # 2. Generate embedding
        embedding = generate_embedding(content)
        
        # 3. Store in ChromaDB
        chroma_collection.add(
            documents=[content],
            embeddings=[embedding],
            metadatas=[{
                "entry_id": entry.id,
                "user_id": user_id,
                "date": str(entry.entry_date),
                "mood": mood
            }],
            ids=[f"entry_{entry.id}"]
        )
        
        # 4. Update entry with embedding reference
        entry.embedding_id = f"entry_{entry.id}"
        entry.embedding_generated_at = datetime.now()
        
        # 5. Update Letta memory
        if letta_agent:
            letta_agent.archival_memory_insert(
                f"[Entry #{entry.id} - {entry.entry_date}] {content[:200]}..."
            )
        
        # 6. Extract ML features (async)
        extract_features_async(entry)
        
        db.commit()
        
        return entry
```

---

### **2. Data Flow: Querying with Smart Search**

```python
def smart_search(user_id: int, query: str):
    """
    Multi-tier search across all storage systems.
    """
    results = {
        "sql_results": [],
        "semantic_results": [],
        "total_found": 0
    }
    
    # Tier 1: Full-text search in SQLite
    sql_results = db.query(JournalEntry).join(
        journal_fts
    ).filter(
        journal_fts.content.match(query)
    ).filter(
        JournalEntry.user_id == user_id
    ).limit(10).all()
    
    results["sql_results"] = sql_results
    
    # Tier 2: Semantic search in ChromaDB
    query_embedding = generate_embedding(query)
    semantic_results = chroma_collection.query(
        query_embeddings=[query_embedding],
        n_results=10,
        where={"user_id": user_id}
    )
    
    # Convert ChromaDB results to journal entries
    entry_ids = [
        int(meta["entry_id"]) 
        for meta in semantic_results["metadatas"][0]
    ]
    
    semantic_entries = db.query(JournalEntry).filter(
        JournalEntry.id.in_(entry_ids)
    ).all()
    
    results["semantic_results"] = semantic_entries
    
    # Merge and deduplicate
    all_entries = list(set(sql_results + semantic_entries))
    results["total_found"] = len(all_entries)
    
    return results
```

---

### **3. Data Flow: Updating an Entry**

```python
def update_journal_entry(entry_id: int, **updates):
    """
    Update entry with consistency across all stores.
    """
    with db.transaction():
        # 1. Update SQLite (MASTER)
        entry = db.query(JournalEntry).get(entry_id)
        
        for key, value in updates.items():
            setattr(entry, key, value)
        
        entry.updated_at = datetime.now()
        
        # 2. If content changed, regenerate embedding
        if 'content' in updates:
            new_embedding = generate_embedding(updates['content'])
            
            # Update ChromaDB
            chroma_collection.update(
                ids=[f"entry_{entry_id}"],
                documents=[updates['content']],
                embeddings=[new_embedding],
                metadatas=[{
                    "entry_id": entry_id,
                    "updated": True,
                    "updated_at": str(datetime.now())
                }]
            )
            
            # Note in Letta memory
            if letta_agent:
                letta_agent.archival_memory_insert(
                    f"[UPDATED Entry #{entry_id}] {updates['content'][:200]}..."
                )
        
        db.commit()
        
        return entry
```

---

### **4. Data Flow: Deleting an Entry**

```python
def delete_journal_entry(entry_id: int):
    """
    Cascade delete across all stores.
    """
    with db.transaction():
        # 1. Get entry
        entry = db.query(JournalEntry).get(entry_id)
        
        # 2. Soft delete in SQLite
        entry.deleted_at = datetime.now()
        
        # 3. Delete from ChromaDB
        chroma_collection.delete(ids=[f"entry_{entry_id}"])
        
        # 4. Note in Letta
        if letta_agent:
            letta_agent.archival_memory_insert(
                f"[DELETED Entry #{entry_id} on {datetime.now()}]"
            )
        
        db.commit()
        
        return True
```

---

## 📊 Query Patterns & Optimization

### **Common Queries with Indexes**

#### **1. Get Recent Entries (Fast)**

```sql
-- Optimized with index: idx_journal_user_date
SELECT *
FROM journal_entries
WHERE user_id = ?
  AND deleted_at IS NULL
ORDER BY entry_date DESC, created_at DESC
LIMIT 50;
```

**Performance:** <10ms with index

---

#### **2. Mood Trend Analysis**

```sql
-- Optimized with index: idx_mood_logs_user_date
SELECT 
    DATE(log_date) as date,
    AVG(mood_value) as avg_mood,
    MIN(mood_value) as min_mood,
    MAX(mood_value) as max_mood,
    COUNT(*) as log_count
FROM mood_logs
WHERE user_id = ?
  AND log_date >= DATE('now', '-30 days')
GROUP BY DATE(log_date)
ORDER BY date DESC;
```

**Performance:** <50ms with index

---

#### **3. Habit Success Rate**

```sql
-- Optimized with index: idx_habit_logs_habit_date
SELECT 
    h.habit_name,
    COUNT(*) as total_logs,
    SUM(CASE WHEN hl.completed THEN 1 ELSE 0 END) as completed_count,
    ROUND(100.0 * SUM(CASE WHEN hl.completed THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate
FROM habit_logs hl
JOIN habits h ON hl.habit_id = h.id
WHERE hl.user_id = ?
  AND hl.log_date >= DATE('now', '-90 days')
GROUP BY h.id, h.habit_name
ORDER BY success_rate DESC;
```

---

#### **4. Goal Progress**

```sql
SELECT 
    g.goal_title,
    g.progress,
    g.target_date,
    JULIANDAY(g.target_date) - JULIANDAY('now') as days_remaining,
    COUNT(gm.id) as total_milestones,
    SUM(CASE WHEN gm.completed THEN 1 ELSE 0 END) as completed_milestones
FROM goals g
LEFT JOIN goal_milestones gm ON g.id = gm.goal_id
WHERE g.user_id = ?
  AND g.status = 'active'
GROUP BY g.id
ORDER BY g.priority DESC, g.target_date ASC;
```

---

## 🔧 Database Maintenance

### **1. Regular Maintenance Tasks**

```python
# Daily maintenance
def daily_maintenance():
    # 1. Vacuum database (optimize storage)
    db.execute("VACUUM")
    
    # 2. Analyze tables (update statistics)
    db.execute("ANALYZE")
    
    # 3. Clean old system logs (>30 days)
    db.execute("""
        DELETE FROM system_logs
        WHERE created_at < DATE('now', '-30 days')
    """)
    
    # 4. Archive old predictions (>90 days)
    db.execute("""
        UPDATE predictions
        SET archived = TRUE
        WHERE prediction_date < DATE('now', '-90 days')
    """)
```

---

### **2. Backup Strategy**

```python
def backup_database():
    """
    Create backup of SQLite database.
    """
    from datetime import datetime
    import shutil
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    source = "./data/database.db"
    destination = f"./backups/database_{timestamp}.db"
    
    # Copy database file
    shutil.copy2(source, destination)
    
    # Compress (optional)
    import gzip
    with open(destination, 'rb') as f_in:
        with gzip.open(f"{destination}.gz", 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    # Remove uncompressed
    os.remove(destination)
    
    print(f"✅ Backup created: {destination}.gz")
```

---

### **3. Data Integrity Checks**

```python
def check_data_integrity():
    """
    Verify data consistency across stores.
    """
    issues = []
    
    # 1. Check orphaned embeddings in ChromaDB
    all_entry_ids = set([
        e.id for e in db.query(JournalEntry.id).all()
    ])
    
    chroma_ids = set([
        int(id.replace("entry_", ""))
        for id in chroma_collection.get()["ids"]
    ])
    
    orphaned = chroma_ids - all_entry_ids
    if orphaned:
        issues.append(f"Orphaned ChromaDB entries: {orphaned}")
    
    # 2. Check missing embeddings
    entries_without_embeddings = db.query(JournalEntry).filter(
        JournalEntry.embedding_id.is_(None)
    ).count()
    
    if entries_without_embeddings > 0:
        issues.append(f"{entries_without_embeddings} entries missing embeddings")
    
    # 3. Check habit logs consistency
    invalid_logs = db.query(HabitLog).filter(
        ~HabitLog.habit_id.in_(
            db.query(Habit.id).filter(Habit.status != 'deleted')
        )
    ).count()
    
    if invalid_logs > 0:
        issues.append(f"{invalid_logs} habit logs for deleted habits")
    
    return issues
```

---

## 🚀 Performance Optimization

### **1. Database Settings**

```python
# In SQLAlchemy setup
engine = create_engine(
    'sqlite:///data/database.db',
    echo=False,
    pool_pre_ping=True,
    connect_args={
        "check_same_thread": False,
        # Performance tuning
        "timeout": 30,
        "isolation_level": None  # Autocommit mode
    }
)

# Execute pragmas for performance
with engine.connect() as conn:
    conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-64000")  # 64MB cache
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA mmap_size=30000000000")  # Memory-mapped I/O
```

---

### **2. Batch Operations**

```python
def batch_insert_mood_logs(logs: List[dict]):
    """
    Efficient batch insert.
    """
    with db.transaction():
        # Use bulk insert
        db.bulk_insert_mappings(MoodLog, logs)
        db.commit()
```

---

## 📦 Database Migration

### **Using Alembic for Schema Changes**

```bash
# Initialize Alembic
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Add energy_level to journal_entries"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## 🎯 Summary

### **Database Architecture Principles:**

1. **SQLite as Master** - Single source of truth
2. **ChromaDB as Index** - Vector search only
3. **Letta as Cache** - Active working memory
4. **Proper Indexing** - Fast queries
5. **Soft Deletes** - Data recovery
6. **JSON for Flexibility** - Extensible schemas
7. **Regular Backups** - Data safety
8. **Integrity Checks** - Consistency
9. **Performance Tuning** - WAL mode, pragmas
10. **Migration Support** - Schema evolution

### **Key Tables:**
- ✅ journal_entries (core)
- ✅ mood_logs (tracking)
- ✅ habits + habit_logs (behavior)
- ✅ goals + milestones (objectives)
- ✅ decisions (pattern analysis)
- ✅ predictions (ML tracking)
- ✅ chat_history (AI conversations)
- ✅ insights (AI-generated)

**Your database is now production-ready!** 🚀
