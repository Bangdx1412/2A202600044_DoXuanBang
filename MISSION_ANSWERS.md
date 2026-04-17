# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Các anti-pattern tìm được
1. Hardcode `OPENAI_API_KEY` và `DATABASE_URL` trong code.
2. `DEBUG`, `MAX_TOKENS`, `host`, `port` không lấy từ biến môi trường.
3. Dùng `print()` thay vì logging chuẩn.
4. In thẳng secret ra log.
5. Không có endpoint `/health` hoặc `/ready`.
6. App bind vào `localhost`, không phù hợp khi chạy container/cloud.
7. Port cố định là `8000`, không đọc từ `PORT`.
8. Bật `reload=True`, chỉ phù hợp cho môi trường dev.
9. Không có graceful shutdown hoặc xử lý `SIGTERM`.
10. Endpoint `/ask` của bản `develop` nhận `question` qua query parameter, nên gửi JSON body sẽ bị `422`.

### Exercise 1.2: Kết quả chạy bản basic
- `GET /` chạy bình thường.
- `POST /ask?question=Hello` chạy bình thường.
- `POST /ask` với JSON `{"question":"Hello"}` trả `422`.
- Kết luận: bản basic chạy được ở local nhưng chưa sẵn sàng cho production.

### Exercise 1.3: So sánh develop và production
| Tính năng | Develop | Production | Ý nghĩa |
|---|---|---|---|
| Cấu hình | Hardcode trong `app.py` | Đọc từ env vars | Dễ đổi môi trường, tránh lộ config |
| Secret | Hardcode | Lấy từ env vars | An toàn hơn khi deploy |
| Host | `localhost` | `0.0.0.0` | Nhận được traffic từ container/cloud |
| Port | Cố định `8000` | Đọc từ `PORT` | Hợp với Railway/Render |
| Logging | `print()` | JSON logging | Dễ theo dõi và phân tích log |
| Health check | Không có | Có `/health` | Platform biết service còn sống |
| Readiness | Không có | Có `/ready` | Chỉ nhận traffic khi app sẵn sàng |
| Request body | Query param | JSON body | API rõ ràng hơn |
| Shutdown | Tắt đột ngột | Graceful shutdown | Giảm rơi request đang xử lý |

### Checkpoint 1
- Hardcode secret rất nguy hiểm nếu push nhầm lên GitHub.
- Dùng env vars giúp cùng một code chạy được ở nhiều môi trường.
- Health check giúp platform restart service khi lỗi.
- Graceful shutdown giúp app dừng an toàn hơn.

## Part 2: Docker

### Exercise 2.1: Dockerfile cơ bản
1. Base image: `python:3.11`.
2. Working directory: `/app`.
3. `COPY requirements.txt` trước để tận dụng Docker layer cache, giúp build nhanh hơn khi chỉ đổi source code.
4. `CMD` là lệnh mặc định khi container chạy; `ENTRYPOINT` thường dùng để cố định lệnh chính của container.

### Exercise 2.2: Build và run
- Lệnh build: `docker build -f 02-docker/develop/Dockerfile -t my-agent:develop .`
- Lệnh run: `docker run -p 8000:8000 my-agent:develop`
- `GET /` trả: `{"message":"Agent is running in a Docker container!"}`
- `POST /ask?question=What%20is%20Docker?` trả câu trả lời mock hợp lệ.
- Kích thước image `my-agent:develop`: `1.66GB` (`CONTENT SIZE = 424MB`).
- Nhận xét: image chạy được nhưng còn khá lớn.

### Exercise 2.3: Multi-stage build
- Stage 1 (`builder`) dùng để cài build tools và dependencies.
- Stage 2 (`runtime`) chỉ giữ phần cần để chạy app.
- Image nhỏ hơn vì không mang theo compiler, cache và file chỉ dùng lúc build.
- Lệnh build: `docker build -f 02-docker/production/Dockerfile -t my-agent:advanced .`
- Kích thước `my-agent:advanced`: `236MB` (`CONTENT SIZE = 56.6MB`).
- So với `develop`, bản `advanced` nhỏ hơn rất nhiều và phù hợp hơn cho production.

### Exercise 2.4: Docker Compose stack
- Stack gồm 4 service: `agent`, `redis`, `qdrant`, `nginx`.
- Luồng giao tiếp:
  - Client gọi vào `nginx`
  - `nginx` chuyển request sang `agent`
  - `agent` dùng `redis` và `qdrant`

```text
Client -> Nginx -> Agent -> Redis
                      \-> Qdrant
```

- Kết quả thực tế sau khi sửa cấu hình:
  - `production-agent-1`: `Up (healthy)`
  - `production-nginx-1`: `Up`
  - `production-redis-1`: `Up (healthy)`
  - `production-qdrant-1`: `Up (healthy)`
- `GET /health` chạy thành công qua Nginx.
- `POST /ask` chạy thành công với `Invoke-RestMethod`.
- `curl.exe` trong PowerShell vẫn có lúc lỗi do cách gửi JSON body.

## Part 3: Cloud Deployment

### Exercise 3.1: Deploy Railway
- `railway init` chạy thành công.
- Domain public của service:
  - `https://2a202600044-production.up.railway.app`
- Test health:
  - `curl.exe https://2a202600044-production.up.railway.app/health`
  - Kết quả: trả `status: ok`
- Test API:
  - `Invoke-RestMethod -Method Post -Uri "https://2a202600044-production.up.railway.app/ask" -ContentType "application/json" -Body '{"question":"Hello"}'`
  - Kết quả: trả về `question` và `answer`
- Kết luận: deploy Railway thành công, public URL hoạt động.

### Exercise 3.2: So sánh `render.yaml` và `railway.toml`
- Cả hai file đều dùng để cấu hình deploy cloud.
- Cả hai đều có `startCommand` chạy `uvicorn` và health check `/health`.
- `railway.toml` ngắn gọn hơn, chủ yếu cấu hình cho một service:
  - `builder`
  - `startCommand`
  - `healthcheckPath`
  - `restartPolicy`
- `render.yaml` chi tiết hơn, mô tả cả hạ tầng:
  - `type: web`
  - `runtime`
  - `region`
  - `plan`
  - `buildCommand`
  - `envVars`
  - thêm service `redis`
- Kết luận: `render.yaml` thiên về mô tả nhiều service trong một blueprint, còn `railway.toml` tập trung vào build và chạy một app trên Railway.
- Ghi chú đúng thực tế: mình chỉ xác nhận nội dung file cấu hình, chưa ghi là Render deploy thành công vì phần đó chưa được kiểm tra xong bằng terminal.

## Part 4: API Security

### Exercise 4.1: API Key authentication
- API key được kiểm tra trong hàm `verify_api_key()` của `04-api-gateway/develop/app.py`.
- App đọc key từ biến môi trường `AGENT_API_KEY`; nếu không set thì dùng giá trị mặc định `demo-key-change-in-production`.
- Endpoint `/ask` được bảo vệ bằng `Depends(verify_api_key)`, nên phải gửi header `X-API-Key`.
- Kết quả test thực tế:
  - Không có key: `401`
  - Sai key: `403`
  - Đúng key: `200`
- Cách rotate key: đổi giá trị `AGENT_API_KEY` trong environment rồi restart app.
- Ghi chú: bản `develop` nhận `question` qua query parameter, nên khi test local dùng `POST /ask?question=Hello`.

### Exercise 4.2: JWT authentication
- Route lấy token trong repo hiện tại là `POST /auth/token`.
- Kết quả test thực tế khi login:
  - server trả về `access_token`
  - `token_type: bearer`
  - `expires_in_minutes: 60`
  - có `hint` hướng dẫn gửi `Authorization: Bearer <token>`
- Token đã được tạo thành công cho user `student`.
- Output thực tế tiếp theo trả `422` với lỗi thiếu `username` và `password` khi body gửi lên là `{"question":"Explain JWT"}`.
- Từ output đó chỉ có thể kết luận:
  - bước lấy JWT đã thành công
  - lần test sau chưa chứng minh được `/ask` chạy thành công
- Tài khoản demo theo code hiện tại:
  - `student / demo123`
  - `teacher / teach456`

### Exercise 4.3: Rate limiting
- File `rate_limiter.py` dùng thuật toán `Sliding Window Counter`.
- User thường dùng `rate_limiter_user`: `10 request / 60 giây`.
- Admin dùng `rate_limiter_admin`: `100 request / 60 giây`.
- Trong code hiện tại không có bypass hoàn toàn cho admin; admin chỉ có limit cao hơn.
- Kết quả test thực tế:
  - Login `student` thành công (`200`)
  - Login `teacher` thành công (`200`)
  - Với user `student`, request thứ 10 vẫn `200`, nhưng request 11 và 12 trả `429 Too Many Requests`
  - Body lỗi thực tế khi hit limit:
    - `{"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_after_seconds":59}}`
  - Với user `teacher`, từ request 10 đến request 12 vẫn `200`
- Kết luận: rate limit hoạt động đúng theo role. User thường bị giới hạn 10 request/phút, còn admin có hạn mức cao hơn.

### Exercise 4.4: Cost guard
- Theo `Solution` trong `CODE_LAB.md`, logic cần implement là:
  - hàm `check_budget(user_id, estimated_cost)`
  - mỗi user có budget `$10/tháng`
  - spending được lưu trong Redis theo key `budget:{user_id}:{YYYY-MM}`
  - nếu `current + estimated_cost > 10` thì trả `False`
  - nếu chưa vượt thì cộng thêm spending và set `expire` khoảng `32 ngày`
- Tuy nhiên, code thực tế trong `04-api-gateway/production/cost_guard.py` hiện đang khác solution của đề:
  - dùng `in-memory`, chưa dùng Redis
  - budget theo ngày, không phải theo tháng
  - budget mỗi user: `$1/ngày`
  - global budget: `$10/ngày`
  - cảnh báo khi user dùng đến `80%` budget
  - vượt budget user thì raise `HTTP 402`
  - vượt global budget thì raise `HTTP 503`
- Kết luận: solution trong đề dùng Redis và budget theo tháng, còn repo hiện tại đang demo cost guard đơn giản hơn bằng in-memory và budget theo ngày.

## Part 5: Scaling & Reliability

### Exercise 5.1: Health checks
- File `05-scaling-reliability/develop/app.py` hiện đã có sẵn 2 endpoint:
  - `GET /health`
  - `GET /ready`
- Kết quả test thực tế bằng `TestClient`:
  - `GET /health` trả `200`
  - `GET /ready` trả `200`
  - `POST /ask?question=health check demo` trả `200`
- Response `GET /health` có các field như:
  - `status`
  - `uptime_seconds`
  - `version`
  - `environment`
  - `timestamp`
  - `checks.memory`
- Kết luận: phần health/readiness đã được implement và hoạt động khi test local.

### Exercise 5.2: Graceful shutdown
- `05-scaling-reliability/develop/app.py` đã có:
  - `lifespan` để xử lý startup/shutdown
  - middleware đếm `_in_flight_requests`
  - signal handler cho `SIGTERM` và `SIGINT`
  - `timeout_graceful_shutdown=30` trong `uvicorn.run(...)`
- Kết quả quan sát thực tế khi test local:
  - log startup xuất hiện: `Agent starting up...`, `Agent is ready!`
  - log shutdown xuất hiện: `Graceful shutdown initiated...`, `Shutdown complete`
- Ghi chú đúng thực tế: mình quan sát được cơ chế shutdown qua vòng đời app khi test local, nhưng chưa chạy đúng kịch bản `kill -TERM` như ví dụ trong lab.

### Exercise 5.3: Stateless design
- `05-scaling-reliability/production/app.py` đã được viết theo hướng session storage tách khỏi request handler:
  - `save_session(...)`
  - `load_session(...)`
  - `append_to_history(...)`
- Khi Redis không sẵn sàng, code fallback sang in-memory store.
- Kết quả test thực tế local:
  - `GET /health` trả `200`
  - `GET /ready` trả `200`
  - request đầu tiên tới `/chat` trả `200` và tạo `session_id`
  - request thứ hai dùng lại `session_id` trả `200`
  - `GET /chat/{session_id}/history` trả `200` với `count = 4`
  - `DELETE /chat/{session_id}` trả `200`
  - gọi lại history sau khi xóa trả `404`
- Tuy nhiên, output thực tế cũng cho thấy:
  - `Redis not available — using in-memory store (not scalable!)`
  - `storage: in-memory`
- Kết luận: logic session hoạt động trong local test, nhưng lần test thực tế này chưa chứng minh được stateless thật sự giữa nhiều instance vì app đang fallback sang in-memory.

### Exercise 5.4: Load balancing
- Theo `docker-compose.yml`, stack dự kiến gồm:
  - `agent`
  - `redis`
  - `nginx`
- `nginx.conf` cấu hình upstream `agent_cluster` và thêm header `X-Served-By`.
- Mình đã bổ sung phần cấu hình tối thiểu để stack chạy được:
  - thêm `05-scaling-reliability/production/Dockerfile`
  - thêm `05-scaling-reliability/production/requirements.txt`
  - sửa `docker-compose.yml` để build từ `05-scaling-reliability/production/Dockerfile`
  - bỏ phụ thuộc vào `.env.local`
- Lệnh chạy thực tế:
  - `docker compose up --build --scale agent=3 -d`
- Kết quả verify thực tế bằng `docker compose ps`:
  - `production-agent-1` — `Up (healthy)`
  - `production-agent-2` — `Up (healthy)`
  - `production-agent-3` — `Up (healthy)`
  - `production-nginx-1` — `Up`
  - `production-redis-1` — `Up (healthy)`
- Test qua Nginx:
  - `curl.exe http://localhost:8080/health` trả `200`
  - response có `storage: "redis"` và `redis_connected: true`
- Kết luận: load balancing stack đã chạy được và traffic đã đi qua `nginx` tới các `agent` instances.

### Exercise 5.5: Test stateless
- File `05-scaling-reliability/production/test_stateless.py` có sẵn để test qua `http://localhost:8080`.
- Sau khi stack đã lên, mình chạy thật:
  - `python test_stateless.py`
- Kết quả thực tế:
  - script gửi 5 request liên tiếp
  - các request được phục vụ bởi 3 instance khác nhau:
    - `instance-b26b64`
    - `instance-ea7d44`
    - `instance-483da2`
  - `Instances used` hiển thị đủ 3 instance
  - conversation history cuối cùng có `10 messages`
  - script kết thúc với dòng:
    - `Session history preserved across all instances via Redis!`
- Kết luận: phần stateless đã được verify end-to-end khi scale nhiều instance.

### Checkpoint 5
- `5.1`: đã verify local, health và readiness hoạt động.
- `5.2`: code đã có graceful shutdown và có log shutdown khi test local.
- `5.3`: local test ban đầu dùng in-memory fallback, nhưng sau khi chạy stack đầy đủ thì app dùng Redis thật.
- `5.4`: đã verify load balancing với `nginx + 3 agent instances + redis`.
- `5.5`: đã chạy thành công `test_stateless.py` và xác nhận history vẫn giữ được khi request đi qua nhiều instance.

### Cập nhật từ terminal test thực tế
- Bản `develop`:
  - `GET /health` trả `200` với `status: ok`
  - `GET /ready` trả `200` với `ready: true`
  - `POST /ask?question=health%20check%20demo` trả `200`
  - khi dừng app bằng `Ctrl+C`, log có:
    - `Graceful shutdown initiated...`
    - `Shutdown complete`
- Bản `production`:
  - `GET /health` trả `200` với:
    - `status: ok`
    - `instance_id: instance-28e443`
    - `storage: in-memory`
    - `redis_connected: N/A`
  - `GET /ready` trả `200`
  - request đầu tiên tới `/chat` tạo được `session_id`
  - request thứ hai với cùng `session_id` vẫn trả `200`
  - `GET /chat/{session_id}/history` trả được history
  - `DELETE /chat/{session_id}` trả `200`
  - gọi lại history sau khi xóa trả lỗi:
    - `Session ... not found or expired`
- Ghi chú:
  - chuỗi tiếng Việt bị lỗi font trong PowerShell là vấn đề encoding của terminal
  - lần test local ban đầu chạy ở chế độ `in-memory`
  - khi chạy stack `5.4/5.5` qua Docker Compose, `/health` đã trả `storage: "redis"` và `redis_connected: true`
