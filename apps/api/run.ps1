$env:API_PORT = $env:API_PORT -as [int]
uv run uvicorn app.main:app --reload --port ($env:API_PORT -as [int] -ne $null ? $env:API_PORT : 8000)
