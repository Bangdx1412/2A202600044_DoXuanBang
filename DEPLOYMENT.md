# Deployment Information

## Platform
Render

## Blueprint File
`06-lab-complete/render.yaml`

## Current Status
- Local production stack for `Part 6` has been prepared and tested.
- Render deployment configuration has been prepared for this monorepo.
- Public Render URL is not recorded in this file yet because that deployment has not been verified from terminal output.

## Render Setup
1. Push the repository to GitHub.
2. In Render Dashboard, choose `New -> Blueprint`.
3. Select this repository.
4. Set `Blueprint Path` to `06-lab-complete/render.yaml`.
5. Provide secret values for:
   - `AGENT_API_KEY`
   - `OPENAI_API_KEY` if you want a real LLM instead of the mock response

## Expected Test Commands

### Health Check
```bash
curl https://your-render-domain.onrender.com/health
```

### Ready Check
```bash
curl https://your-render-domain.onrender.com/ready
```

### Authenticated API Test
```bash
curl -X POST https://your-render-domain.onrender.com/ask \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test-user","question":"Hello"}'
```

## Required Environment Variables
- `PORT`
- `REDIS_URL`
- `AGENT_API_KEY`
- `OPENAI_API_KEY`
- `RATE_LIMIT_PER_MINUTE`
- `MONTHLY_BUDGET_USD`
- `LOG_LEVEL`
