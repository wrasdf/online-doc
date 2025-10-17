FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
COPY .venv ./.venv

RUN . .venv/bin/activate && uv pip install --no-cache-dir -r pyproject.toml

COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
