---
type: abbreviation
abbr: JWT
category: Security
examples:
  - Access token
  - ID token
  - Refresh token
related:
  - "[[OAuth]]"
  - "[[Auth]]"
  - "[[API]]"
  - "[[JSON]]"
links:
  - https://jwt.io
  - https://tools.ietf.org/html/rfc7519
---

# JWT - JSON Web Token

**JSON Web Token** (JWT) is a compact, URL-safe means of representing claims to be transferred between two parties. It's commonly used for authentication and information exchange in web applications and APIs.

## Structure

A JWT consists of three parts separated by dots:

```
header.payload.signature
```

### Parts

1. **Header** - Token type and hashing algorithm
2. **Payload** - Claims (user data, expiration, etc.)
3. **Signature** - Verification using secret or private key

## Common Use Cases

### Authentication
After login, each subsequent request includes the JWT, allowing access to protected routes and resources without server-side sessions.

### Information Exchange
JWTs can securely transmit information between parties because they can be signed, ensuring the sender is who they claim to be.

## Algorithms

- **HS256** - HMAC with SHA-256 (symmetric)
- **RS256** - RSA with SHA-256 (asymmetric) - more secure
- **ES256** - ECDSA with SHA-256

## Security Best Practices

- ✅ Use short expiration times (15 minutes for access tokens)
- ✅ Use RS256 for production
- ✅ Store in httpOnly cookies (not localStorage)
- ✅ Implement refresh token rotation
- ❌ Don't store sensitive data in payload (it's base64, not encrypted)
- ❌ Don't use weak secrets

## Example Token

```json
{
  "alg": "RS256",
  "typ": "JWT"
}
{
  "sub": "1234567890",
  "name": "Sarah Mitchell",
  "role": "admin",
  "iat": 1516239022,
  "exp": 1516242622
}
```

## Related

- [[OAuth]] - Authorization framework that uses JWT
- [[API]] - JWTs commonly used for API authentication
- [[Auth]] - Authentication concepts
- [[Sarah Mitchell]] - Working on JWT implementation
