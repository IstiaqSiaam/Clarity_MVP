# apps/nlp_service/nlp/worker/enqueue_test.py
import os
from redis import Redis
from rq import Queue

def main():
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    conn = Redis.from_url(redis_url)
    q = Queue("nlp", connection=conn)
    job = q.enqueue("nlp.worker.jobs.analyze_text_sync", "Hello from Clarity 👋")
    print("Enqueued job:", job.id)

if __name__ == "__main__":
    main()
