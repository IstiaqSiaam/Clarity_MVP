FROM python:3.11-slim
WORKDIR /app
RUN pip install uv
COPY . /app
RUN uv sync
CMD ["uv", "run", "python", "-m", "nlp.worker.consumer"]
