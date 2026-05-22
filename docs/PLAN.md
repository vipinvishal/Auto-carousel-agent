# Project Plan

## Architecture

## Phases

### Phase 1 — Core Pipeline (build first)
- [ ] config.py
- [ ] transcript.py
- [ ] claude_api.py
- [ ] carousel.py
- [ ] export.py
- [ ] emailer.py
- [ ] agent.py
- [ ] Test end-to-end with a known video ID

### Phase 2 — Server + Trigger
- [ ] main.py (FastAPI)
- [ ] WebSub subscription on startup
- [ ] WebSub renewal (every 5 days)
- [ ] Test with real ping

### Phase 3 — Deploy
- [ ] requirements.txt
- [ ] render.yaml
- [ ] Deploy to Render.com
- [ ] Update CALLBACK_BASE_URL
- [ ] Re-subscribe WebSub with live URL
- [ ] End-to-end live test

## Testing Strategy
- Phase 1: Run agent.py directly with a hardcoded video ID
- Phase 2: Use a WebSub tester to simulate Google's ping
- Phase 3: Wait for Vaibhav to post or manually trigger

## Known Constraints
- YouTube transcript API may fail if captions are disabled
- WebSub subscription expires every 10 days — must auto-renew
- Render.com free tier sleeps after 15min inactivity — use paid $7/month plan or ping service
- Gmail SMTP limit: 500 emails/day (more than enough)