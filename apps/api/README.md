# Journal Service

The journal service provides a REST API for creating, retrieving, and managing journal entries with automatic NLP analysis.

## Features

- ✅ **Create Journal Entries**: Store user journal entries in MongoDB
- ✅ **Retrieve Entries**: Get specific entries or paginated lists
- ✅ **Automatic NLP Analysis**: Each entry is automatically enqueued for sentiment analysis and theme extraction
- ✅ **Input Validation**: Pydantic models ensure data integrity
- ✅ **Pagination Support**: Efficient pagination for large datasets
- ✅ **Health Checks**: Monitor service status

## Architecture

```
┌─────────┐     POST /journal      ┌──────────┐
│ Client  │ ─────────────────────► │   API    │
└─────────┘                        │ Service  │
                                   └────┬─────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
                    ▼                   ▼                   ▼
            ┌──────────────┐    ┌──────────┐      ┌──────────────┐
            │   MongoDB    │    │  Redis   │      │ NLP Worker   │
            │ (journal_    │    │  Queue   │◄─────│  (RQ)        │
            │  entries)    │    └──────────┘      └──────────────┘
            └──────────────┘
```

## API Endpoints

### Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "ok",
  "service": "clarity-api"
}
```

### Create Journal Entry

```http
POST /journal
Content-Type: application/json

{
  "text": "Your journal entry text (1-10000 characters)"
}
```

**Response (201 Created):**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "user_id": "user_demo",
  "text": "Your journal entry text",
  "created_at": "2025-11-02T10:30:00.123000",
  "updated_at": "2025-11-02T10:30:00.123000",
  "enc_blob": null
}
```

**Side Effects:**
- Entry is stored in MongoDB
- JournalEntryCreated event is enqueued for NLP analysis

### Get Paginated Journal Entries

```http
GET /journal?page=1&page_size=10
```

**Query Parameters:**
- `page` (optional, default=1): Page number (starts at 1)
- `page_size` (optional, default=10): Number of entries per page (1-100)

**Response:**
```json
{
  "entries": [
    {
      "id": "...",
      "user_id": "user_demo",
      "text": "...",
      "created_at": "...",
      "updated_at": "...",
      "enc_blob": null
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 10,
  "total_pages": 5
}
```

**Notes:**
- Entries are sorted by `created_at` in descending order (newest first)
- Only returns entries for the current user

### Get Specific Journal Entry

```http
GET /journal/{entry_id}
```

**Path Parameters:**
- `entry_id`: MongoDB ObjectId of the entry

**Response (200 OK):**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "user_id": "user_demo",
  "text": "Your journal entry text",
  "created_at": "2025-11-02T10:30:00.123000",
  "updated_at": "2025-11-02T10:30:00.123000",
  "enc_blob": null
}
```

**Error Responses:**
- `400 Bad Request`: Invalid entry ID format
- `404 Not Found`: Entry doesn't exist or doesn't belong to user

## Data Models

### JournalEntryDocument (MongoDB)

```python
{
  "_id": ObjectId,
  "user_id": str,
  "text": str,  # 1-10000 characters
  "created_at": datetime,
  "updated_at": datetime,
  "enc_blob": str | None  # Reserved for future encryption
}
```

### Event Payloads

See [EVENT_PAYLOADS.md](../../docs/EVENT_PAYLOADS.md) for detailed event specifications.

## MongoDB Collections

### journal_entries

**Indexes:**
- `user_id` (ascending)
- `created_at` (ascending)

**Sample Document:**
```json
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  "user_id": "user_123",
  "text": "Today was productive...",
  "created_at": ISODate("2025-11-02T10:30:00.000Z"),
  "updated_at": ISODate("2025-11-02T10:30:00.000Z"),
  "enc_blob": null
}
```

## NLP Integration

When a journal entry is created:

1. **JournalEntryCreatedEvent** is published to the `nlp` queue
2. NLP worker picks up the job and analyzes the text
3. Worker returns **AnalysisCompletedEvent** with:
   - `sentiment`: -1.0 to 1.0
   - `themes`: Array of identified themes
   - `summary`: AI-generated summary

Current implementation uses a placeholder analyzer. Future versions will integrate:
- OpenAI GPT models
- Local Hugging Face models
- Custom fine-tuned sentiment analyzers

## Testing

### Interactive API Documentation

Visit http://localhost:8000/docs for Swagger UI

### Automated Test Script

```bash
cd apps/api
./test_journal.sh
```

### Manual cURL Examples

```bash
# Create an entry
curl -X POST http://localhost:8000/journal \
  -H "Content-Type: application/json" \
  -d '{"text": "Today I learned about FastAPI!"}'

# Get all entries
curl http://localhost:8000/journal

# Get specific entry
curl http://localhost:8000/journal/507f1f77bcf86cd799439011

# Paginated request
curl "http://localhost:8000/journal?page=2&page_size=5"
```

## Configuration

Environment variables (`.env`):

```env
MONGO_URL=mongodb://clarity:clarity@mongo:27017/?authSource=admin
REDIS_URL=redis://redis:6379/0
```

For Docker deployment, service names (`mongo`, `redis`) are used instead of `localhost`.

## Development

### Running Locally

```bash
# Start services
cd infra
docker-compose up -d

# Check logs
docker-compose logs -f api

# Check NLP worker
docker-compose logs -f nlp
```

### File Structure

```
apps/api/app/
├── main.py                 # FastAPI app with lifespan management
├── core/
│   ├── database.py        # MongoDB and Redis connections
│   └── settings.py        # Environment configuration
├── models/
│   ├── journal.py         # Journal entry models and schemas
│   └── events.py          # Event payload models
├── routes/
│   └── journal.py         # Journal API endpoints
└── services/
    └── queue.py           # RQ job enqueueing
```

## Future Enhancements

- [ ] User authentication and authorization
- [ ] Entry encryption (utilize `enc_blob` field)
- [ ] Real-time NLP analysis results via WebSocket
- [ ] Entry editing and deletion
- [ ] Tags and categories
- [ ] Search functionality
- [ ] Export journal entries
- [ ] Analytics dashboard
- [ ] Mood tracking integration

## Troubleshooting

### "MongoDB not connected" error

Ensure MongoDB is running and accessible:
```bash
docker-compose ps mongo
docker-compose logs mongo
```

### Jobs not being processed

Check NLP worker status:
```bash
docker-compose logs nlp
docker-compose ps nlp
```

Verify Redis connection:
```bash
docker-compose exec redis redis-cli ping
```

### Database indexes

Indexes are created automatically on startup. To verify:
```bash
docker-compose exec mongo mongosh -u clarity -p clarity --authenticationDatabase admin
use clarity
db.journal_entries.getIndexes()
```

## API Rate Limits

No rate limits implemented yet. Recommended for production:
- 100 requests/minute per user
- 1000 requests/hour per user

## License

Part of the Clarity MVP project.
