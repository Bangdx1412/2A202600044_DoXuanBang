#  Delivery Checklist — Day 12 Lab Submission

> **Student Name:** Đỗ Xuân Bằng  
> **Student ID:** 2A202600044  
> **Date:** 17/04/2026

---

##  Submission Requirements

Submit a **GitHub repository** containing:

### 1. Mission Answers (40 points)

Create a file `MISSION_ANSWERS.md` with your answers to all exercises:

```markdown
# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
1. [Your answer]
2. [Your answer]
...

### Exercise 1.3: Comparison table
| Feature | Develop | Production | Why Important? |
|---------|---------|------------|----------------|
| Config  | ...     | ...        | ...            |
...

## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. Base image: [Your answer]
2. Working directory: [Your answer]
...

### Exercise 2.3: Image size comparison
- Develop: [X] MB
- Production: [Y] MB
- Difference: [Z]%

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment
- URL: https://your-app.railway.app
- Screenshot: [Link to screenshot in repo]

## Part 4: API Security

### Exercise 4.1-4.3: Test results
[Paste your test outputs]

### Exercise 4.4: Cost guard implementation
[Explain your approach]

## Part 5: Scaling & Reliability

### Exercise 5.1-5.5: Implementation notes
[Your explanations and test results]
```

---

### 2. Full Source Code - Lab 06 Complete (60 points)

Your final production-ready agent with all files:

```
your-repo/
├── app/
│   ├── main.py              # Main application
│   ├── config.py            # Configuration
│   ├── auth.py              # Authentication
│   ├── rate_limiter.py      # Rate limiting
│   └── cost_guard.py        # Cost protection
├── utils/
│   └── mock_llm.py          # Mock LLM (provided)
├── Dockerfile               # Multi-stage build
├── docker-compose.yml       # Full stack
├── requirements.txt         # Dependencies
├── .env.example             # Environment template
├── .dockerignore            # Docker ignore
├── railway.toml             # Railway config (or render.yaml)
└── README.md                # Setup instructions
```

**Requirements:**
-  All code runs without errors
-  Multi-stage Dockerfile (image < 500 MB)
-  API key authentication
-  Rate limiting (10 req/min)
-  Cost guard ($10/month)
-  Health + readiness checks
-  Graceful shutdown
-  Stateless design (Redis)
-  No hardcoded secrets

---

### 3. Service Domain Link

Create a file `DEPLOYMENT.md` with your deployed service information:

```markdown
# Deployment Information

## Public URL
https://your-agent.railway.app

## Platform
Railway / Render / Cloud Run

## Test Commands

### Health Check
```bash
curl https://your-agent.railway.app/health
# Expected: {"status": "ok"}
```

### API Test (with authentication)
```bash
curl -X POST https://your-agent.railway.app/ask \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "question": "Hello"}'
```

## Environment Variables Set
- PORT
- REDIS_URL
- AGENT_API_KEY
- LOG_LEVEL

## Screenshots
- [Deployment dashboard](screenshots/dashboard.png)
- [Service running](screenshots/running.png)
- [Test results](screenshots/test.png)
```

##  Pre-Submission Checklist

- [x] Repository is public (or instructor has access)
- [x] `MISSION_ANSWERS.md` completed with all exercises
- [x] `DEPLOYMENT.md` has working public URL
- [ ] All source code in `app/` directory
- [x] `README.md` has clear setup instructions
- [x] No `.env` file committed (only `.env.example`)
- [ ] No hardcoded secrets in code
- [x] Public URL is accessible and working
- [ ] Screenshots included in `screenshots/` folder
- [x] Repository has clear commit history

### Current Status Notes

- `MISSION_ANSWERS.md` đã được cập nhật đầy đủ từ `Part 1` đến `Part 6`.
- Public URL đã verify hoạt động:
  - `https://ai-agent-production-hb3q.onrender.com`
  - `GET /health` trả `status: "ok"` và `redis_connected: true`
  - `GET /ready` trả `{"ready": true, ...}`
- `DEPLOYMENT.md` đã được cập nhật với public URL Render thật và lệnh test tương ứng cho `Part 6`.
- Source code final theo cấu trúc checklist hiện đang nằm trong `06-lab-complete/app/`, không phải `app/` ở repo root, nên mình chưa tick mục đó.
- Repo GitHub đã truy cập public được khi kiểm tra từ bên ngoài.
- Repo có các ví dụ `develop` và tài liệu học tập chứa chuỗi demo/fake secret để minh hoạ anti-pattern, nên mình chưa tick mục “No hardcoded secrets in code”.
- Thư mục `screenshots/` hiện chưa có.
- Endpoint `POST /ask` đã xác nhận yêu cầu `X-API-Key`; muốn chụp test `200 OK` thì cần dùng `AGENT_API_KEY` hiện tại trong Render Environment.

---

##  Self-Test

Before submitting, verify your deployment:

```bash
# 1. Health check
curl https://ai-agent-production-hb3q.onrender.com/health

# 2. Authentication required
curl -X POST https://ai-agent-production-hb3q.onrender.com/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","question":"Hello"}'
# Should return 401

# 3. With API key works
curl -H "X-API-Key: YOUR_KEY" https://ai-agent-production-hb3q.onrender.com/ask \
  -H "Content-Type: application/json" \
  -X POST -d '{"user_id":"test","question":"Hello"}'
# Should return 200

# 4. Rate limiting
for i in {1..15}; do 
  curl -H "X-API-Key: YOUR_KEY" https://ai-agent-production-hb3q.onrender.com/ask \
    -H "Content-Type: application/json" \
    -X POST -d '{"user_id":"test","question":"test"}'; 
done
# Should eventually return 429
```

---

##  Submission

**Link GitHub repository để nộp:**

```
https://github.com/Bangdx1412/2A202600044_DoXuanBang
```

**Link deploy public:**

```
https://ai-agent-production-hb3q.onrender.com
```

**Hạn nộp:** 17/4/2026

---

##  Quick Tips

1.  Test your public URL from a different device
2.  Make sure repository is public or instructor has access
3.  Include screenshots of working deployment
4.  Write clear commit messages
5.  Test all commands in DEPLOYMENT.md work
6.  No secrets in code or commit history

---

##  Need Help?

- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Review [CODE_LAB.md](CODE_LAB.md)
- Ask in office hours
- Post in discussion forum

---

**Good luck! **
