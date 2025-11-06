---
type: snippet
date: 2025-10-20 14:30:00
source: meeting
tags: [auth, security, jwt, api]
---

# Authentication Implementation Discussion

Met with Sarah to discuss the authentication implementation for our API. We decided on the following approach:

## Key Decisions

1. **Token Type**: Use JWT (JSON Web Tokens) with RS256 signing
2. **Token Storage**: Store access tokens in httpOnly cookies to prevent XSS attacks
3. **Refresh Strategy**: Implement refresh token rotation for enhanced security
4. **Expiration**:
   - Access tokens: 15 minutes
   - Refresh tokens: 7 days

## Implementation Tasks

- [ ] Set up JWT signing with RS256 keys
- [ ] Implement token refresh endpoint
- [ ] Add httpOnly cookie middleware
- [ ] Write tests for token validation

## Security Considerations

Need to ensure we handle edge cases like:
- Token expiration during active sessions
- Concurrent refresh token usage
- Revocation of compromised tokens

## Related

- [[Sarah Mitchell]] - Auth Team Lead
- [[Context Tool]] - Project this is for
- [[OAuth]] - Alternative we considered
