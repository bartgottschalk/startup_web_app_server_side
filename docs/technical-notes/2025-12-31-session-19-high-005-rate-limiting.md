# Session 19: HIGH-005 Rate Limiting Implementation

**Date**: December 31, 2025
**Branch**: `feature/high-005-rate-limiting`
**PR**: #63 (pending)
**Status**: ✅ COMPLETE - Ready for merge

## Overview

Implemented rate limiting on critical public endpoints to prevent abuse (account creation spam, password reset email bombing, login brute force attacks).

## Implementation

### Endpoints Protected

1. **user/login**: 10 requests/hour per IP → HTTP 403
2. **user/create-account**: 5 requests/hour per IP → HTTP 403
3. **user/reset-password**: 5 requests/hour per username → HTTP 403

### Technology Stack

- **Library**: django-ratelimit 4.1.0
- **Cache Backend**: local-memory (dev), Redis-ready (production)
- **Response**: HTTP 403 Forbidden (django-ratelimit default)
- **Fail Mode**: Fail-open (requests succeed if cache unavailable)

### Key Design Decisions

**1. HTTP 403 vs HTTP 429**
- Django-ratelimit raises `Ratelimited` exception → Django converts to HTTP 403
- Decision: Acceptable - rate-limited users should see an error
- Simpler than custom error handling (one decorator, automatic blocking)

**2. Test Isolation**
- Rate limiting disabled during general tests: `RATELIMIT_ENABLE = 'test' not in sys.argv`
- Re-enabled for dedicated rate limit tests via `@override_settings(RATELIMIT_ENABLE=True)`
- Prevents test interference while maintaining rate limit test coverage

**3. Fail-Open Mode**
- `RATELIMIT_FAIL_OPEN = True` - requests succeed if cache fails
- Rationale: Availability > security for startup validation tool
- Production monitoring will alert on cache failures

## Files Modified

```
requirements.txt                      - Added django-ratelimit==4.1.0
StartupWebApp/settings.py            - Cache + rate limit config
user/views.py                         - 3 rate limit decorators
user/tests/test_rate_limiting.py     - NEW: 10 comprehensive tests
```

## Testing

**Test Coverage**:
- 10 new rate limiting tests (all passing)
- Below-limit requests succeed
- Exceeding limits returns HTTP 403
- Per-IP tracking works correctly
- Per-username tracking works correctly (password reset)
- Fail-open mode verified

**Test Results**:
```
✅ 712/712 tests passing (702 existing + 10 new)
✅ Zero linting errors
✅ Rate limiting tests: 10/10 passing
✅ Order tests: 306/306 passing
✅ User tests: all passing
```

## Configuration

### Development (Current)
```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

RATELIMIT_ENABLE = 'test' not in sys.argv  # Disabled during tests
RATELIMIT_FAIL_OPEN = True
```

### Production (Future - Requires Infrastructure)
```python
# settings_production.py (future)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://elasticache-endpoint:6379',
    }
}
```

## Deployment Strategy: Incremental Approach

**Decision: Deploy Phase 1 (Local-Memory Cache) Now**

This implementation uses a two-phase deployment strategy:

### Phase 1: Local-Memory Cache (THIS DEPLOYMENT)
- **Status**: Ready to deploy
- **Cache Backend**: `LocMemCache` (Django built-in)
- **Protection Level**: Single-container scenarios (dev, low-traffic production)
- **Multi-Container Limitation**: Each ECS task has separate memory cache - rate limits NOT shared
- **Risk Mitigation**: `RATELIMIT_FAIL_OPEN = True` prevents outages if cache fails
- **Deployment Impact**: Zero infrastructure changes, safe to deploy immediately

### Phase 2: ElastiCache Redis (Future Session - 2-3 hours)
- ElastiCache Redis cluster (cache.t4g.micro ~$12/month)
- Security group configuration (ECS → Redis port 6379)
- Add redis-py to requirements.txt
- Update settings_production.py with Redis connection
- CloudWatch alarms for rate limit violations
- **Code Changes Required**: None (just configuration)

### Why Deploy Phase 1 First?

1. **Production-Safe**: Fail-open mode prevents service disruption
2. **Partial Protection**: Single-container deployments get full rate limiting
3. **No Code Changes Later**: Phase 2 is purely infrastructure + config
4. **Ship Incrementally**: Get value sooner, iterate based on real traffic patterns
5. **CI/CD Verified**: All 712 tests passing, zero linting errors

### Current Production Behavior

**Multi-Container Scenario (Current Auto-Scaling: 1-4 tasks)**:
- Each ECS task maintains its own rate limit counters in memory
- An attacker could bypass limits by triggering requests across different containers
- Example: 10 req/hour login limit becomes 40 req/hour with 4 containers
- **Mitigation**: Limits are still 4x better than no limits, CloudWatch monitoring active

**Single-Container Scenario**:
- Full rate limiting protection as designed
- Covers: development, low-traffic periods, initial deployments

## Security Impact

**HIGH-005 Status**: ✅ Core endpoints protected (Phase 1)

**Attack Vectors Mitigated**:
- ✅ Account creation spam (5/hour limit per container)
- ✅ Password reset email bombing (5/hour per username per container)
- ✅ Login brute force (10/hour per IP per container)

**Known Limitations (Phase 1)**:
- ⚠️ Multi-container bypass (4x higher limits with 4 containers)
- ⚠️ Not suitable for high-traffic scenarios without ElastiCache
- ✅ Still better than no rate limiting (current state)

**Remaining Risks** (acceptable for validation tool):
- Client event flooding (no limits yet - analytics data)
- Shared IP false positives (corporate networks - limits chosen to minimize)
- DDoS attacks (would require AWS WAF - add when traffic justifies cost)
- Multi-container rate limit bypass (Phase 2 will fix)

## Future Work

### Phase 2: ElastiCache Redis (Next Priority)
- ElastiCache Redis setup (~$12/month for cache.t4g.micro)
- Security group configuration (ECS → Redis)
- Add redis-py to requirements.txt
- Update settings_production.py with Redis connection
- CloudWatch alarms for rate limit violations

### Additional Endpoints (HIGH-009)
- clientevent endpoints (pageview, ajaxerror, etc.)
- user/pythonabot-notify-me
- Custom error messages for rate-limited requests

### AWS WAF (Optional - If Needed)
- Triggers: Traffic >100 req/sec, DDoS attacks, high costs
- Cost: ~$6-10/month additional
- Defense in depth (edge blocking + Django rate limiting)

## Notes

**Test Pattern**: The approach of disabling rate limiting during general tests and re-enabling for specific test classes is a standard Django pattern. This ensures:
- Tests remain deterministic
- No cross-test contamination from cached rate limits
- Rate limiting functionality still thoroughly tested
- Minimal impact on existing test suite

**CI/CD Compatibility**: Verified that rate limiting auto-disables during `python manage.py test` via `'test' not in sys.argv` check. All 712 tests pass in CI without any configuration changes.

## References

- PRE_FORK_SECURITY_FIXES.md - Updated with Session 19 details
- django-ratelimit documentation: https://django-ratelimit.readthedocs.io/
