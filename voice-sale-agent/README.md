# voice-sale-agent

Python rewrite of the Java `jc-voice-shopping` voice shopping agent.

## Stack

- FastAPI
- LangGraph `StateGraph` + `ToolNode` + `interrupt`
- PostgreSQL LangGraph `AsyncPostgresSaver` + `AsyncPostgresStore`
- SQLAlchemy async + asyncpg
- Redis
- PostgreSQL + pgvector
- DashScope chat / embedding / ASR / TTS
- Conda + `pip install -r requirements.txt`

## Quick Start

```powershell
conda create -n voice-sale-agent python=3.13.12
conda activate voice-sale-agent
pip install -r requirements.txt
Copy-Item .env.example .env
# Fill .env secrets first.
uvicorn app.main:app --host 0.0.0.0 --port 8010 --reload
```

Apply database migrations before starting an existing installation:

```powershell
alembic upgrade head
```

Python 服务不提供生产前端或浏览器登录入口。Vue 前端只连接 Java Gateway，
Python 仅由 Gateway 和 Java 门面通过内部网络访问。

## Product Embeddings

After loading `app/resources/sql/schema.sql` and `app/resources/sql/data.sql`, initialize
the product vectors with:

```powershell
python -m scripts.init_product_embeddings
```

The command follows the Java `/api/v1/admin/reindex` behavior and rebuilds all
on-sale product vectors. To only fill missing vectors:

```powershell
python -m scripts.init_product_embeddings --only-missing
```

Product search first uses pgvector. If embedding generation, vector dimensions, the
vector query, or vector recall fails, it falls back to parameterized PostgreSQL
keyword search over product names, brands, categories, descriptions, selling points,
and attributes.

## Internal API and identity

Java Gateway is the only external authentication boundary. It validates the
Sa-Token session, removes client-provided `X-Agent-*` headers, and injects
`X-Agent-User-Id` before forwarding to this service. Java's OpenFeign client
must forward the same header from the authenticated Java context.

Python does not issue or validate browser JWTs. It must not be published to the
public network. Missing or malformed `X-Agent-User-Id` returns HTTP 401; a
WebSocket handshake is closed with policy-violation code `1008`.

| Internal route | Consumer | Purpose |
| --- | --- | --- |
| `POST /internal/v1/sessions/start` | Java voice-agent facade | Create or reuse an Agent session |
| `POST /internal/v1/chat/text` | Java voice-agent facade | Text fallback conversation |
| `GET /internal/v1/orders/mine` | Java voice-agent facade | Agent demonstration orders |
| `WS /ws/voice?sessionId=<id>` | Gateway WebSocket proxy | PCM voice interaction |
| `GET /health` | Container platform only | PostgreSQL and Redis health check |

The WebSocket protocol is unchanged: the client sends 16kHz/16-bit/mono PCM
frames followed by `{"type":"audio_end"}` and receives `asr`,
`recommendation`, `caption`, `warning`, `complete`, or `error` JSON frames plus
PCM audio frames. `token` is deliberately not accepted as a query parameter.

The first session request creates a minimal `app_user` projection keyed by the
Java user ID. That table remains only to satisfy the Agent database's foreign
keys; it is not an account or login system.

## Container

```powershell
docker build -t voice-sale-agent .
docker run --env-file .env --network internal -p 127.0.0.1:8010:8010 voice-sale-agent
```

For production, do not publish the container port. Attach the service only to
the internal network that Gateway, the Java facade, and health probes use.

## Notes

- `.env.example` keeps secrets as placeholders; the service defaults to port `8010`.
- The project connects to the existing PostgreSQL and Redis after `.env` is filled.
- The Supervisor and all worker graphs are compiled during application startup. Request-scoped services are injected through LangGraph runtime context.
- Every graph invocation uses `thread_id=session_id`; order confirmation pauses with `interrupt()` and resumes on the next turn.
- A Redis `SET NX EX` lock serializes one Agent turn per `user_id + session_id`; a concurrent turn receives a retryable HTTP `409` or WebSocket `error` event.
- Short-term conversation messages are checkpointed by `AsyncPostgresSaver`; Redis List memory is not used.
- Cross-thread preferences use the Store namespace `("voice-shopping", "users", user_id, "preferences")` and semantic search.
- Worker handoffs use `Command(update=..., goto=...)` with `AIMessage`/`ToolMessage`; recommendation tools run in a bounded ReAct loop.
- Session state, pending orders, stores, and checkpoints are validated or partitioned by the Gateway-authenticated Java user.
- On Windows the application selects `WindowsSelectorEventLoopPolicy`, which is required by the async psycopg Checkpointer.
- Integration tests are marked `integration`; default `pytest` runs unit tests only.
