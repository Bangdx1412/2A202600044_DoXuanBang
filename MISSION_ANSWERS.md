# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
1. `OPENAI_API_KEY` và `DATABASE_URL` bị hardcode trực tiếp trong `01-localhost-vs-production/develop/app.py`.
2. Cấu hình như `DEBUG`, `MAX_TOKENS`, `host`, `port` không lấy từ environment variables.
3. Dùng `print()` thay vì structured logging.
4. Log lộ secret với dòng `print(f"[DEBUG] Using key: {OPENAI_API_KEY}")`.
5. Không có health check endpoint như `/health` hoặc `/ready`.
6. App bind vào `localhost` nên không phù hợp khi chạy trong container hoặc cloud.
7. Port bị cố định là `8000`, không đọc từ biến `PORT`.
8. `reload=True` được bật sẵn, phù hợp cho development nhưng không nên dùng trong production.
9. Không có graceful shutdown hoặc xử lý `SIGTERM`.
10. Endpoint `/ask` của bản `develop` nhận `question` dưới dạng query parameter, nên nếu gửi JSON body theo ví dụ trong lab thì sẽ bị `422`.

### Exercise 1.2: Running the basic version
- `GET /` hoạt động bình thường và trả về thông báo app đang chạy local.
- `POST /ask?question=Hello` hoạt động và trả về mock response.
- `POST /ask` với JSON body `{"question": "Hello"}` hiện tại trả về `422 Unprocessable Entity` vì code đang khai báo `question: str` như query parameter.
- Kết luận: bản basic chạy được trên máy local, nhưng chưa production-ready vì cấu hình cứng, lộ secret, thiếu health check, thiếu graceful shutdown và contract API chưa ổn định.

### Exercise 1.3: Comparison table
| Feature | Develop | Production | Why Important? |
|---------|---------|------------|----------------|
| Config | Hardcode ngay trong `app.py` | Tách sang `config.py` và đọc từ env vars | Giúp đổi cấu hình theo môi trường mà không sửa code và tránh lộ secrets |
| Secrets | API key và database URL hardcode | Secrets lấy từ environment variables | An toàn hơn khi deploy và không làm rò rỉ key lên GitHub |
| Host binding | `localhost` | `0.0.0.0` | Cho phép app nhận traffic từ container, reverse proxy và cloud platform |
| Port | Cố định `8000` | Đọc từ `PORT` | Tương thích Railway, Render và các nền tảng cloud inject port runtime |
| Logging | `print()` thủ công | Structured JSON logging | Dễ parse log, filter log và đưa vào hệ thống giám sát |
| Health check | Không có | Có `/health` | Platform biết container còn sống để restart khi lỗi |
| Readiness | Không có | Có `/ready` với readiness flag | Load balancer chỉ route traffic khi app đã sẵn sàng |
| Request validation | `question` là query param, dễ lệch với client | Đọc JSON body và trả `422` nếu thiếu field | API contract rõ ràng và dễ tích hợp hơn |
| Shutdown | Tắt đột ngột | Có lifespan và handler cho `SIGTERM` | Cho phép dừng app an toàn và giảm rơi request đang xử lý |
| Startup behavior | Chạy kiểu local debug | Có startup log, readiness state và production-safe defaults | Dễ quan sát hệ thống và gần với thực tế deploy hơn |

### Checkpoint 1
- Hardcoded secrets nguy hiểm vì chỉ cần push nhầm lên GitHub là key có thể bị lộ và bị lạm dụng.
- Environment variables giúp cùng một codebase chạy được ở dev, staging và production với cấu hình khác nhau.
- Health check endpoint giúp platform biết khi nào container còn sống để giữ service ổn định.
- Graceful shutdown là cơ chế cho app ngừng nhận request mới, hoàn tất request đang xử lý rồi mới tắt hẳn.

### Notes from local verification
- Bản `develop` đã được kiểm tra local và đúng là chạy được, nhưng endpoint `/ask` đang hợp với query string hơn là JSON body.
- Bản `production` đã được kiểm tra local với kết quả: `/health` trả `200`, `/ready` trả `200`, và `POST /ask` với JSON body trả `200`.

## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. Base image: `python:3.11`. Đây là image nền mà container được build từ đó, đã có sẵn Python 3.11 để chạy ứng dụng.
2. Working directory: `/app`. Đây là thư mục làm việc chính bên trong container, nên các lệnh tiếp theo như `COPY`, `RUN`, `CMD` sẽ chạy theo ngữ cảnh thư mục này.
3. `COPY requirements.txt` trước để tận dụng Docker layer cache. Nếu code thay đổi nhưng dependencies không đổi, Docker không cần cài lại thư viện và thời gian build sẽ nhanh hơn.
4. `CMD` đặt lệnh mặc định khi container khởi động và có thể bị ghi đè lúc `docker run`. `ENTRYPOINT` thường dùng để cố định lệnh chính của container, còn tham số thêm vào khi chạy sẽ được nối vào sau.

### Exercise 2.2: Build and run results
- Build command used: `docker build -f 02-docker/develop/Dockerfile -t my-agent:develop .`
- Run command used: `docker run -p 8000:8000 my-agent:develop`
- Test result for `GET /`: `{"message":"Agent is running in a Docker container!"}`
- Test result for `POST /ask?question=What%20is%20Docker?`: `{"answer":"Container là cách đóng gói app để chạy ở mọi nơi. Build once, run anywhere!"}`
- Image size from `docker images my-agent:develop`: `DISK USAGE = 1.66GB`, `CONTENT SIZE = 424MB`
- Observation: image build và container run thành công. Image còn khá lớn vì đang dùng `python:3.11` bản đầy đủ, đây là lý do Part 2.3 dùng multi-stage build để tối ưu hơn.
- Note: code hiện tại nhận `question` qua query parameter, nên khi test thực tế dùng `POST /ask?question=...` thay vì JSON body theo ví dụ trong lab.

### Exercise 2.3: Multi-stage build
- Stage 1 (`builder`) dùng để cài các build dependencies như `gcc`, `libpq-dev` và cài Python packages từ `requirements.txt`. Stage này chỉ phục vụ build, không dùng để deploy.
- Stage 2 (`runtime`) tạo image cuối cùng để chạy app. Stage này chỉ copy các package đã cài từ stage 1, copy source code cần thiết, tạo non-root user, thêm `HEALTHCHECK` và chạy `uvicorn`.
- Image nhỏ hơn vì image cuối không mang theo compiler, build tools, apt cache và các file chỉ cần trong lúc build. Ngoài ra Dockerfile còn dùng `python:3.11-slim` thay vì bản full nên nhẹ hơn đáng kể.

### Exercise 2.3: Image size comparison
- Build command used: `docker build -f 02-docker/production/Dockerfile -t my-agent:advanced .`
- Develop image size: `1.66GB` (`CONTENT SIZE = 424MB`)
- Advanced image size: `236MB` (`CONTENT SIZE = 56.6MB`)
- Difference: advanced image nhỏ hơn rất nhiều so với develop, phù hợp hơn cho production vì pull nhanh hơn, tốn ít storage hơn và deploy hiệu quả hơn.

### Exercise 2.4: Docker Compose stack
- Compose file defines 4 services: `agent`, `redis`, `qdrant`, `nginx`.
- Observed communication flow from the configuration and terminal tests:
  - Client sends requests to `nginx` on `localhost:80`
  - `nginx` forwards requests to `agent:8000`
  - `agent` is configured to use `redis://redis:6379/0`
  - `agent` is configured to use `http://qdrant:6333`
- Architecture diagram:

```text
Client
  |
  v
Nginx (port 80)
  |
  v
Agent (FastAPI)
  | \
  |  \
  v   v
Redis  Qdrant
```

### Exercise 2.4: Actual terminal results
- `docker compose ps -a` showed these containers created and running after fixes:
  - `production-agent-1` — `Up (healthy)`
  - `production-nginx-1` — `Up`
  - `production-redis-1` — `Up (healthy)`
  - `production-qdrant-1` — `Up (healthy)`
- `curl.exe http://localhost/health` returned:
  - `{"status":"ok","uptime_seconds":4.1,"version":"2.0.0","timestamp":"2026-04-17T08:46:09.715876"}`
- `curl.exe -X POST "http://localhost/ask" ...` in PowerShell still returned `Internal Server Error`.
- `Invoke-RestMethod -Method Post -Uri "http://localhost/ask" -ContentType "application/json" -Body '{"question":"Explain microservices"}'` returned a successful response with field `answer`.
- Conclusion from actual testing: the Compose stack was running and `/health` worked through Nginx. The `/ask` endpoint also worked when tested with `Invoke-RestMethod`; the failure observed with `curl.exe` was specific to how JSON body was sent from PowerShell during testing.

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment
- Project initialization was completed successfully with `railway init`.
- Railway service already had a public domain:
  - `https://2a202600044-production.up.railway.app`
- Public health check test:
  - Command: `curl.exe https://2a202600044-production.up.railway.app/health`
  - Result: `{"status":"ok","uptime_seconds":67.9,"platform":"Railway","timestamp":"2026-04-17T09:08:34.463169+00:00"}`
- Public API test:
  - Command: `Invoke-RestMethod -Method Post -Uri "https://2a202600044-production.up.railway.app/ask" -ContentType "application/json" -Body '{"question":"Hello"}'`
  - Result: returned fields `question` and `answer`
- Notes from actual terminal behavior:
  - `railway domain` only worked inside `03-cloud-deployment/railway` because that is the linked directory.
  - `curl http://student-agent-domain/health` failed because `student-agent-domain` in the lab is only a placeholder, not a real domain.
  - Raw URL pasted directly into PowerShell was treated as a command, not a browser action.
  - `curl.exe -X POST ...` to `/ask` still returned `Internal Server Error` in PowerShell, while `Invoke-RestMethod` worked successfully. Based on the successful `Invoke-RestMethod` result, the deployed API was reachable and functioning.

### Exercise 3.2: Compare `render.yaml` and `railway.toml`
- `render.yaml` and `railway.toml` both configure cloud deployment and both define a start command that runs the app with `uvicorn` on `0.0.0.0` and `$PORT`.
- Both files also define a health check path of `/health`.
- `railway.toml` is shorter and focuses on one service's deployment settings:
  - builder: `NIXPACKS`
  - `startCommand`
  - `healthcheckPath`
  - `healthcheckTimeout`
  - `restartPolicyType`
  - `restartPolicyMaxRetries`
- `render.yaml` is more detailed and infrastructure-oriented. In the current file it defines:
  - a `web` service named `ai-agent`
  - `runtime: python`
  - `region: singapore`
  - `plan: free`
  - `buildCommand`
  - `startCommand`
  - `healthCheckPath`
  - `autoDeploy: true`
  - environment variables under `envVars`
  - a second service of type `redis` named `agent-cache`
- Therefore, the main difference is that `render.yaml` describes multiple services and more infrastructure details, while `railway.toml` mainly describes how Railway should build and run one deployed app service.
- Factual note from local repo inspection: `03-cloud-deployment/render` currently contains `render.yaml`, while the runnable sample app used in Part 3.1 is in `03-cloud-deployment/railway`. I did not record a successful Render deployment in this answer because that deployment was not fully verified from terminal output.
