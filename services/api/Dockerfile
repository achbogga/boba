FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY . /app

RUN uv sync --frozen --no-dev

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "boba_api.app:app", "--host", "0.0.0.0", "--port", "8000"]
