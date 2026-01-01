# Fork Setup Guide

**Purpose**: Step-by-step guide for customizing StartupWebApp for your business

---

## 🚧 TODO (Next Session): Fill in full content

**This is a STUB file created during documentation reorganization.**

**Planned Outline** (~500 lines when complete):

### 1. Before You Fork
- Prerequisites (AWS account, GitHub, Stripe account)
- Cost expectations (~$98/month AWS baseline)
- What you're getting (Django API + jQuery/React frontend template)
- Tech stack overview

### 2. Customize the Code
- Update `settings_secret.py` with YOUR Stripe keys (live mode for real business)
- Modify data migrations for YOUR products
- Update email templates with YOUR branding
- Change domain names from startupwebapp.com to yours
- Customize terms of use, privacy policy
- Update product images and descriptions

### 3. Deploy to AWS
- Run infrastructure scripts (`scripts/infra/`)
- Configure GitHub secrets for CI/CD
- Deploy backend (ECS Fargate)
- Deploy frontend (S3 + CloudFront)
- Test checkout flow end-to-end

### 4. Configure Your Products
- How to add products via Django admin
- How to set up SKUs and pricing
- How to configure shipping methods
- How to create discount codes
- Image management (S3/CloudFront setup)

### 5. Launch Checklist
- ✅ Switch Stripe from TEST to LIVE mode
- ✅ Configure production email (AWS SES or SendGrid)
- ✅ Set up monitoring/alerts (CloudWatch)
- ✅ Test complete checkout with real card
- ✅ Verify order confirmation emails
- ✅ Configure custom domain
- ✅ SSL certificate setup
- ✅ GDPR compliance review
- ✅ Security audit checklist

---

**Next Session**: Fill in this content based on actual fork customization patterns and AWS deployment experience.
