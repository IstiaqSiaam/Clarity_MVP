"""
Queue service for enqueueing background jobs
"""
from rq import Queue
from app.core.database import get_redis_client
from app.models.events import JournalEntryCreatedEvent


def get_queue() -> Queue:
    """Get the RQ queue for NLP tasks"""
    redis_client = get_redis_client()
    return Queue("nlp", connection=redis_client)


def enqueue_analysis_job(event: JournalEntryCreatedEvent) -> str:
    """
    Enqueue a journal entry analysis job
    
    Args:
        event: The JournalEntryCreated event payload
        
    Returns:
        Job ID
    """
    queue = get_queue()
    
    # Enqueue the job with the event data
    job = queue.enqueue(
        "nlp.worker.jobs.analyze_journal_entry",
        event.model_dump(),
        job_timeout="5m",
        result_ttl=86400,  # Keep results for 24 hours
        failure_ttl=86400,  # Keep failed job info for 24 hours
    )
    
    return job.id
