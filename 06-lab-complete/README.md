# Lab 12 - Complete Production Agent

Part 6 final project cho Day 12. Stack local gồm `nginx + 3 agent instances + redis`, còn deploy cloud được chuẩn bị sẵn bằng `render.yaml`.

## Thành phần chính

- `app/main.py`: FastAPI app, conversation history trong Redis, structured JSON logging
- `app/auth.py`: API key authentication
- `app/rate_limiter.py`: Redis sliding-window rate limit `10 req/phut/user`
- `app/cost_guard.py`: Redis monthly budget guard `$10/thang/user`
- `Dockerfile`: multi-stage, non-root, chạy được trên Render
- `docker-compose.yml`: local stack với `agent + redis + nginx`
- `render.yaml`: Blueprint cho Render trong monorepo này

## Chạy local

```bash
cd 06-lab-complete
docker compose up --build --scale agent=3 -d
```

Test:

```bash
curl http://localhost:8090/health
curl http://localhost:8090/ready
curl -X POST http://localhost:8090/ask \
  -H "X-API-Key: change-me-before-deploy" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"demo-user","question":"Hello"}'
```

Xem history:

```bash
curl http://localhost:8090/history/demo-user \
  -H "X-API-Key: change-me-before-deploy"
```

Dừng stack:

```bash
docker compose down
```

## Deploy lên Render

1. Push code lên GitHub
2. Vào Render Dashboard -> `New -> Blueprint`
3. Chọn repo này
4. Đặt `Blueprint Path` là `06-lab-complete/render.yaml`
5. Render sẽ tạo:
   - `ai-agent-production` web service
   - `ai-agent-cache` Render Key Value
6. Khi tạo lần đầu, nhập secrets:
   - `AGENT_API_KEY`
   - `OPENAI_API_KEY` nếu muốn thay mock LLM

Lưu ý:

- `render.yaml` đang dùng `rootDir: 06-lab-complete` vì repo này là monorepo
- Render free web service và free key value đều hỗ trợ deploy thử nghiệm, nhưng free key value là ephemeral

## Kiểm tra nhanh

```bash
python check_production_ready.py
```

## Công nghệ chính

- FastAPI
- Redis
- Docker multi-stage
- Nginx load balancing
- Render Blueprint
