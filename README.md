# BeatoBot 🎸  
A Reddit bot that monitors a subreddit for comments and posts referencing musical chords or progressions, and optionally responds or notifies via Discord. Powered by PRAW, MongoDB, and an LLM API via FastAPI.

---

## Features

- ⛓️ Detects Roman numeral, numerical, or named chord progressions in Reddit posts/comments
- 💬 Sends matches to a Discord channel
- 🧠 LLM analysis to identify subtle or informal references
- 🗃️ MongoDB-backed persistence for GitHub Pages integration
- 🔥 Docker support

---

## 📦 Environment Variables

### Reddit (PRAW)
| Key                  | Description                      |
|----------------------|----------------------------------|
| `REDDIT_CLIENT_ID`   | Reddit app client ID             |
| `REDDIT_CLIENT_SECRET` | Reddit app client secret       |
| `REDDIT_USER_AGENT`  | Custom user agent string         |
| `SUBREDDIT_NAME`     | Subreddit to monitor             |

### MongoDB
| Key          | Description                            |
|--------------|----------------------------------------|
| `MONGO_URI`  | Full connection URI for MongoDB Atlas |

### Discord
| Key                    | Description                         |
|------------------------|-------------------------------------|
| `DISCORD_WEBHOOK_URL`  | Discord webhook for notifications   |

### LLM Server
| Key                  | Description                         |
|----------------------|-------------------------------------|
| `LLM_REPO_ID`        | HF model repo for llama-cpp         |
| `LLM_FILENAME`       | GGUF model filename in container    |

---

## 🔧 Example docker-compose.yml
```yaml
version: "3.9"

services:
  bot:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      LOG_LEVEL: ${LOG_LEVEL:-INFO}  # Defaults to INFO if not provided
      DISCORD_WEBHOOK_URL: "https://discord.com/api/webhooks/your-webhook-url"
      MONGO_URI: "your_mongo_connection_string"
      REDDIT_CLIENT_ID: "your_reddit_client_id"
      REDDIT_CLIENT_SECRET: "your_reddit_client_secret"
      REDDIT_USER_AGENT: "your_app_user_agent"
      SUBREDDIT_NAME: "patfinnerty"
    volumes:
      - ./logs:/app/logs  # Optional local logging
    depends_on:
      - llm

  llm:
    build:
      context: ./server
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      LLM_REPO_ID: "hugging-quants/Llama-3.2-1B-Instruct-Q4_K_M-GGUF"  # Default, can override
      LLM_FILENAME: "llama-3.2-1b-instruct-q4_k_m.gguf"                # Default, can override
```

## Running with Docker
```bash
# Default log level
docker compose up -d

# With debug logging
LOG_LEVEL=DEBUG docker compose up -d

# View live logs
docker compose logs -f bot
```

# Run the LLM server
uvicorn server:app --host 0.0.0.0 --port 8000 --reload