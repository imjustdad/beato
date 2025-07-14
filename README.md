# BeatoBot
A Reddit bot that monitors the r/patfinnerty subreddit for 'beato' comments and posts. Powered by PRAW and a Hugging Face LLM via FastAPI.

## 🔧 Example docker-compose.yml
```yaml
version: "3.9"

services:
  bot:
    build:
      context: ./bot
      dockerfile: Dockerfile
    container_name: beato-bot
    environment:
      LOG_LEVEL: ${LOG_LEVEL:-INFO} # Defaults to INFO if not provided
      DISCORD_WEBHOOK_URL: "https://discord.com/api/webhooks/your-discord-webhook-url"
      MONGO_URI: "mongo atlas uri connection string"
      REDDIT_CLIENT_ID: "reddit_client_id"
      REDDIT_CLIENT_SECRET: "reddit_client_secret"
      REDDIT_USER_AGENT: "reddit_user_agent"
      FASTAPI_URL: "http://server:8000/llama"
      SUBREDDIT_NAME: "patfinnerty"
    volumes:
      - ./logs:/app/logs  # Optional local logging
    depends_on:
      server:
        condition: service_healthy
    restart: unless-stopped

  server:
    build:
      context: ./server
      dockerfile: Dockerfile
    container_name: beato-server
    ports:
      - "8000:8000"
    environment:
      LLM_REPO_ID: "hugging-quants/Llama-3.2-1B-Instruct-Q4_K_M-GGUF"   # Default, can override using a different repo from hugging face
      LLM_FILENAME: "llama-3.2-1b-instruct-q4_k_m.gguf"                 # Default, can override using a different file from hugging face
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 60s
```

## Running with Docker
```bash
# Start bot and server containers in the background
docker compose up -d

# Specify a specific container to start
docker compose up bot
docker compose up server

# With debug logging
LOG_LEVEL=DEBUG docker compose up
```