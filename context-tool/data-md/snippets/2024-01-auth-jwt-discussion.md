---
type: snippet
date: 2024-01-15 14:30
source: Slack conversation
tags:
  - auth
  - jwt
  - security
  - api
people:
  - "[[Sarah Mitchell]]"
projects:
  - "[[Context Tool]]"
---

# JWT Authentication Discussion

Discussed implementing JWT-based authentication for the new API with [[Sarah Mitchell]].

## Key Points

- Use **RS256** algorithm instead of HS256 for better security
- Access tokens should be short-lived (15 minutes)
- Refresh tokens stored in httpOnly cookies to prevent XSS
- Implement refresh token rotation on each use
- Store token family ID to detect token reuse attacks

## Action Items

- [ ] Update auth service to use RS256
- [ ] Implement refresh token rotation
- [ ] Add token family tracking to database
- [ ] Update API documentation

## References

- [[OAuth]]
- [[JWT]]
- RFC 6749 (OAuth 2.0)
