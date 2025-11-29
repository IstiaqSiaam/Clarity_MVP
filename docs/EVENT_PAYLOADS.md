# Event Payloads

This document defines the event payloads used in the Clarity MVP messaging system.

## JournalEntryCreated

Published when a new journal entry is created.

### Payload Structure

```json
{
  "entry_id": "string",
  "user_id": "string",
  "text": "string",
  "created_at": "ISO 8601 datetime"
}
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `entry_id` | string | Unique identifier for the journal entry (MongoDB ObjectId) |
| `user_id` | string | Identifier of the user who created the entry |
| `text` | string | The full text content of the journal entry |
| `created_at` | datetime | ISO 8601 timestamp when the entry was created |

### Example

```json
{
  "entry_id": "507f1f77bcf86cd799439011",
  "user_id": "user_123",
  "text": "Today was a good day. I felt productive and accomplished my goals.",
  "created_at": "2025-11-02T10:30:00Z"
}
```

### Queue

- **Queue Name**: `nlp`
- **Job Name**: `analyze_journal_entry`
- **Priority**: Normal

---

## AnalysisCompleted

Published when NLP analysis of a journal entry is completed.

### Payload Structure

```json
{
  "entry_id": "string",
  "user_id": "string",
  "sentiment": "float",
  "themes": ["string"],
  "summary": "string"
}
```

### Fields

| Field | Type | Range/Constraints | Description |
|-------|------|-------------------|-------------|
| `entry_id` | string | - | Unique identifier for the journal entry |
| `user_id` | string | - | Identifier of the user who owns the entry |
| `sentiment` | float | -1.0 to 1.0 | Sentiment score: -1 (very negative) to 1 (very positive) |
| `themes` | array[string] | - | List of identified themes/topics in the entry |
| `summary` | string | - | AI-generated summary of the journal entry |

### Example

```json
{
  "entry_id": "507f1f77bcf86cd799439011",
  "user_id": "user_123",
  "sentiment": 0.75,
  "themes": ["productivity", "achievement", "positive_mood"],
  "summary": "The user had a productive day and successfully achieved their goals, resulting in a positive emotional state."
}
```

### Queue

- **Queue Name**: `nlp`
- **Job Name**: `store_analysis_results`
- **Priority**: Normal

---

## Flow Diagram

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ POST /journal
       ▼
┌─────────────────┐
│   API Service   │
└────┬───────┬────┘
     │       │
     │       └──────► Enqueue: JournalEntryCreated
     │                     │
     │                     ▼
     │              ┌──────────────┐
     │              │ NLP Worker   │
     │              └──────┬───────┘
     │                     │ Process & Analyze
     │                     ▼
     │              Publish: AnalysisCompleted
     │                     │
     ▼                     ▼
┌─────────────────────────────┐
│   MongoDB (journal_entries) │
└─────────────────────────────┘
```

## Usage in Code

### Publishing JournalEntryCreated

```python
from app.models.events import JournalEntryCreatedEvent
from app.services.queue import enqueue_analysis_job

event = JournalEntryCreatedEvent(
    entry_id=str(entry.id),
    user_id=entry.user_id,
    text=entry.text,
    created_at=entry.created_at
)

enqueue_analysis_job(event)
```

### Consuming AnalysisCompleted

```python
from app.models.events import AnalysisCompletedEvent

# In the worker
def handle_analysis_completed(event_data: dict):
    event = AnalysisCompletedEvent(**event_data)
    # Store results, update UI, etc.
```

## Notes

- All datetime fields use ISO 8601 format with UTC timezone
- The `enc_blob` field in journal entries is reserved for future encryption features
- Sentiment scores use a normalized scale where 0 represents neutral sentiment
- Themes are extracted using NLP and may vary based on the analysis model
