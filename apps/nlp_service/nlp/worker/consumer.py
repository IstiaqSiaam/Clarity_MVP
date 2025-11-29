# apps/nlp_service/nlp/worker/consumer.py
import os
from rq import Queue, Worker
from redis import Redis

def run():
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    conn = Redis.from_url(redis_url)

    # Use a named queue, e.g., "nlp"
    q = Queue("nlp", connection=conn)

    # Create a worker bound to the same connection
    w = Worker([q], connection=conn)
    # If you also run an RQ scheduler, use with_scheduler=True, otherwise False
    w.work(with_scheduler=True)

if __name__ == "__main__":
    run()
