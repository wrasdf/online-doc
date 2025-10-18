FROM python:3.11-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml .

RUN uv pip install --system --no-cache-dir -e .

COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]