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
