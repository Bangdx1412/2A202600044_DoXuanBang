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
