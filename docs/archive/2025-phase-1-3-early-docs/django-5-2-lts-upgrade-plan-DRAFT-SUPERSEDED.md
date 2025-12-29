# Django 5.2 LTS Upgrade Plan

**Date**: TBD (Q1 2026)
**Status**: 📋 Planning (Not yet started)
**Priority**: HIGH - Django 4.2 LTS support ends April 2026

---

## Executive Summary

Django 4.2 LTS security support ends April 2026 (~4 months). This document outlines the plan to upgrade from Django 4.2.16 to Django 5.2 LTS, ensuring continued security patch support until April 2028.

**Timeline**: Start January 2026, complete by March 2026 (before Django 4.2 EOL)

---

## Background

### Current State (December 2025)
- **Django Version**: 4.2.16 LTS
- **Support Timeline**:
  - Mainstream support: Ended April 2025
  - Security fixes: Until April 2026 (~4 months remaining)
- **Tests**: 730 backend tests + 88 frontend tests (all passing)
- **Production**: Stable, zero known issues

### Target State
- **Django Version**: 5.2 LTS (to be released April 2025)
- **Support Timeline**:
  - Mainstream support: April 2025 - December 2026
  - Security fixes: Until April 2028 (3+ years)
- **Python**: 3.12.x (already compatible)
- **PostgreSQL**: 16 (already compatible)

---

## Upgrade Path Options

### Option 1: Direct Upgrade (4.2 → 5.2)
- **Approach**: Upgrade directly from 4.2.16 to 5.2.x in one step
- **Pros**: Faster, fewer intermediate steps
- **Cons**: More breaking changes to handle at once, higher risk
- **Estimated Effort**: 12-16 hours

### Option 2: Incremental Upgrade (4.2 → 5.0 → 5.1 → 5.2)
- **Approach**: Upgrade through each major version
- **Pros**: Smaller changesets, easier debugging, lower risk
- **Cons**: More time-consuming, more intermediate testing
- **Estimated Effort**: 16-24 hours

### Recommendation: TBD
- Will decide based on Django 5.2 release notes (expected April 2025)
- Django 5.0/5.1 release notes will inform complexity assessment

---

## Key Considerations

### Breaking Changes to Review
- **Django 5.0**:
  - CSRF_USE_SESSIONS and CSRF_COOKIE_MASKED defaults changed
  - Deprecated features removed (from Django 3.x)
- **Django 5.1**: TBD (not yet released)
- **Django 5.2**: TBD (not yet released)

### Dependencies to Review
- **Stripe**: Currently 14.0.1 (check compatibility with Django 5.2)
- **Selenium**: Currently 4.27.1 (should be compatible)
- **Other packages**: Review all requirements.txt for Django 5.2 compatibility

### Test Strategy
- Apply same TDD methodology as Django 4.2 upgrade (Phase 4)
- Run full test suite after each incremental upgrade
- Zero tolerance for test regressions
- Functional tests must pass 100%

---

## Success Criteria

**Django 5.2 Upgrade Complete When:**
- ✅ Django upgraded to 5.2.x LTS
- ✅ All 730 backend unit tests passing
- ✅ All 37 functional tests passing
- ✅ All 88 frontend unit tests passing
- ✅ Zero deprecation warnings in logs
- ✅ Production deployment successful
- ✅ Zero regression issues in production
- ✅ Documentation updated

---

## Timeline (Tentative)

**Phase 1: Research & Planning** (January 2026)
- Wait for Django 5.2 LTS release (expected April 2025)
- Review Django 5.0, 5.1, 5.2 release notes
- Assess breaking changes
- Decide on upgrade path (direct vs incremental)
- Create detailed session-by-session plan

**Phase 2: Local Development Upgrade** (February 2026)
- Upgrade local development environment
- Fix breaking changes
- Run full test suite
- Document all changes

**Phase 3: Production Deployment** (March 2026)
- Deploy to production
- Monitor for issues
- Rollback plan ready

**Buffer**: Complete by March 31, 2026 (before April 2026 EOL)

---

## References

**Django Release Schedule:**
- Django 5.0: Released December 2024
- Django 5.1: Expected August 2025
- Django 5.2 LTS: Expected April 2025
- Source: https://www.djangoproject.com/download/#supported-versions

**Previous Django Upgrades:**
- Phase 4: Django 2.2.28 → 4.2.16 (November 2025)
  - See: `docs/PROJECT_HISTORY.md` Phase 4
  - Approach: Incremental 6-step process
  - Result: Zero test regressions, minimal code changes

**Decision:**
- Skip Django 6.0 (not LTS, released December 2025)
- Target Django 5.2 LTS for maximum support timeline

---

## Next Steps

**Before Starting:**
1. Wait for Django 5.2 LTS release (April 2025)
2. Review release notes for 5.0, 5.1, 5.2
3. Create detailed upgrade plan
4. Schedule upgrade sessions for Q1 2026

**This document will be updated in January 2026 with specific upgrade steps.**

---

**Document Status**: Planning placeholder
**Next Update**: January 2026 (after Django 5.2 release)
**Owner**: TBD
