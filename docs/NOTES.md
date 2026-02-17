# CloudPulse - Comprehensive Project Notes

## 1. Business Overview

### Vision
A simple, affordable cloud cost monitoring tool for startups and small DevOps teams.
Enterprise tools (Vantage, CloudHealth) cost $500+/mo — we target $29-49/mo.

### Target Audience
- Startups with AWS accounts spending $1k-50k/month
- Small DevOps teams (1-5 engineers)
- Freelance cloud consultants managing client infrastructure
- Platform engineering teams at mid-size companies

### Value Proposition
- **Save money**: Surface hidden waste (idle EC2, unused EBS, old snapshots)
- **Prevent surprises**: Anomaly alerts before bills spiral
- **Simple**: Not enterprise-bloated — set up in 5 minutes
- **Affordable**: 10x cheaper than enterprise alternatives

---

## 2. Business Model

### Pricing Tiers (Planned)
- **Free**: 1 AWS account, daily email summary, 7-day history
- **Pro ($29/mo)**: 3 AWS accounts, anomaly alerts, Slack integration, 90-day history
- **Team ($49/mo)**: 10 AWS accounts, multi-user, recommendations engine, 1-year history
- **Custom ($99+/mo)**: Unlimited accounts, priority support, custom integrations

### Revenue Targets
- 3 months: 10 paying customers, $500 MRR
- 6 months: 50 customers, $2,500 MRR
- 12 months: 150 customers, $7,500 MRR
- 18 months: 300 customers, $15,000 MRR

### Budget Allocation ($10k)
- Validation: $500 (ads, landing page testing)
- MVP Development: $2,000 (time investment + tools)
- Infrastructure: $600 (6 months hosting, APIs)
- Marketing: $4,000 (content, SEO, ads, outreach)
- Legal/Admin: $500 (LLC, terms of service)
- Reserve: $2,400 (iteration runway)

---

## 3. Competitive Landscape (Updated 2026-02-16)

### Tier 1: Enterprise FinOps Platforms ($500+/mo)

**Vantage** — Market leader for mid-to-large companies
- 25+ native integrations (AWS, Azure, GCP, K8s, Snowflake, Datadog, OpenAI, MongoDB)
- Virtual tagging (cost allocation without real AWS tags)
- Autopilot: auto-purchases Reserved Instances/Savings Plans (5% of savings fee)
- Terraform provider (FinOps as Code)
- MCP server for ChatGPT/Claude integration
- Anomaly detection with root-cause resource drill-down
- K8s efficiency metrics (pod waste, cluster idle costs)
- Pricing: Free up to $2.5k tracked spend; then % of spend or fixed annual contract
- Weaknesses: 24-hour data latency, limited dashboard customization, no dark mode

**CloudHealth (Broadcom/VMware)** — Legacy enterprise
- Enterprise governance, compliance, multi-cloud
- Weaknesses: Steep learning curve, dated UI, slow innovation post-acquisition, opaque pricing

**Cloudability (Apptio/IBM)** — Enterprise FinOps
- Dashboards, budgets/forecasting, scorecards, True Cost Explorer
- Weaknesses: Complex, expensive, long implementation

### Tier 2: Mid-Market Tools ($99-299/mo)

**CloudForecast** — Closest direct competitor
- Hacker Plan: $99/mo, Growth: $299/mo
- Focused on email/Slack daily cost reports ("understand in 30 seconds")
- "Why?" drill-down for cost anomalies (their killer feature)
- Monthly CFO/finance reports
- Team-level cost group reports
- PagerDuty/Opsgenie integrations
- 4-minute setup, first report in 24 hours
- Weaknesses: AWS-only, no recommendations engine, no resource scanning, basic UI

### Tier 3: Open Source / Free Tools

**Infracost** — Terraform cost estimation in pull requests
- Shows cost impact BEFORE deployment ("shift FinOps left")
- CI/CD integration (GitHub, GitLab, Azure DevOps)
- Different use case: pre-deploy estimation, not post-deploy monitoring
- $100/seat/month for cloud version

**Komiser** — Open-source cloud inventory
- Multi-cloud asset inventory (AWS, GCP, Azure)
- Finds orphaned resources
- Weaknesses: Complex for beginners, requires self-hosting

**OpenCost / Kubecost** — Kubernetes-specific
- Pod/namespace/deployment cost allocation
- Only useful for K8s workloads

**AWS Cost Explorer / AWS Budgets** — Built-in
- Free but clunky, no smart anomaly detection
- Threshold-only alerts, no drill-down, no recommendations

### CloudPulse Positioning
We sit between Tier 2 and Tier 3 — simpler and cheaper than CloudForecast,
but more actionable than free/open-source tools.

### Feature Gap Analysis: CloudPulse vs Competitors

Features WE HAVE:
- ✅ Cost dashboard with daily/weekly/monthly views
- ✅ Service breakdown
- ✅ Anomaly detection with severity levels
- ✅ Email + Slack alerts
- ✅ Idle EC2, unused EBS, old snapshot recommendations
- ✅ 5-minute onboarding (IAM role)
- ✅ API-first design

Features WE NEED (Priority order for market readiness):

**P0 — Must have before launch:**
1. "Why?" Cost Drill-Down — explain WHY costs changed (like CloudForecast's killer feature)
2. Budgets & Budget Alerts — set monthly budgets, alert when approaching/exceeding
3. Cost Forecasting — predict end-of-month spend based on current trajectory
4. Daily Email Digest — automated daily summary (no login required to stay informed)
5. User Authentication — proper signup/login with JWT
6. Multi-account support — manage multiple AWS accounts in one dashboard

**P1 — Competitive advantages (our edge):**
7. AI Cost Insights — Use LLM to explain cost changes in plain English ("Your EC2 spend jumped 40% because i-0abc123 ran 24/7 instead of its usual 8hr schedule")
8. One-Click CloudFormation Setup — customer pastes a CF link, role is auto-created (vs manual IAM setup)
9. Cost-per-Tag Breakdown — group costs by team/project/environment tags
10. Savings Plan / RI Coverage Report — show how much is covered vs on-demand
11. Shareable Reports — public URL for a cost report (send to managers/finance)
12. Weekly PDF Report — auto-generated PDF emailed to stakeholders

**P2 — Growth features (post-launch):**
13. Multi-cloud (Azure, GCP)
14. Terraform Provider (manage CloudPulse via IaC)
15. Slack Bot (query costs via Slack commands)
16. Team RBAC (role-based access)
17. Custom alerts ("alert me if S3 spend > $X")
18. API webhooks for custom integrations
19. S3 lifecycle recommendations
20. RDS instance rightsizing

### CloudPulse's Competitive Edge (What Nobody Else Does Well)
1. **AI-powered plain-English explanations** — No one in the $29-49/mo range has this
2. **Fastest onboarding** — One-click CloudFormation vs manual IAM setup
3. **Developer-first pricing** — $29/mo vs CloudForecast's $99/mo minimum
4. **Actionable, not just visible** — Recommendations with estimated savings + one-click resolve
5. **Modern stack, modern UI** — React + Tailwind vs dated enterprise UIs

---

## 4. Technical Architecture

### System Design
```
User's AWS Account ──(read-only IAM role)──► CloudPulse Backend
                                                    │
                                    ┌───────────────┼───────────────┐
                                    ▼               ▼               ▼
                              PostgreSQL        Cron Jobs       Alert Engine
                              (Supabase)    (daily cost pull)  (email/Slack)
                                    ▲               │
                                    │               ▼
                              FastAPI Server    Anomaly Detector
                                    ▲           + Recommender
                                    │
                              Frontend (Next.js)
```

### Tech Stack Decisions
| Component | Choice | Rationale |
|-----------|--------|-----------|
| Language | Python 3.11+ | Founder's expertise, great AWS SDK (boto3) |
| Web Framework | FastAPI | Async, fast, auto-docs, modern Python |
| Database | PostgreSQL via Supabase | Free tier, built-in auth, real-time |
| ORM | SQLAlchemy 2.0 | Industry standard, async support |
| AWS SDK | boto3 | Official AWS SDK for Python |
| Task Scheduling | APScheduler / Railway cron | Daily cost data pulls |
| Email | SendGrid | Free tier (100 emails/day) |
| Slack | Incoming Webhooks | Simple, free |
| Payments | Stripe | Industry standard |
| Hosting | Railway | Easy Python deploys, cron support, ~$5-20/mo |
| Frontend | Next.js (later) | React-based, good for dashboards |

### AWS APIs Used
1. **Cost Explorer** (`ce:GetCostAndUsage`) - Historical and current spend data
2. **Cost Explorer** (`ce:GetCostForecast`) - Projected spend
3. **CloudWatch** (`cloudwatch:GetMetricStatistics`) - EC2 CPU utilization
4. **EC2** (`ec2:DescribeInstances`) - Instance inventory
5. **EC2** (`ec2:DescribeVolumes`) - EBS volume inventory
6. **EC2** (`ec2:DescribeSnapshots`) - Snapshot inventory
7. **STS** (`sts:AssumeRole`) - Cross-account access

### Database Schema (High Level)
- **users**: id, email, stripe_customer_id, plan, created_at
- **aws_accounts**: id, user_id, account_id, role_arn, external_id, status
- **cost_records**: id, aws_account_id, date, service, amount, currency
- **anomalies**: id, aws_account_id, date, service, expected_amount, actual_amount, severity
- **recommendations**: id, aws_account_id, resource_type, resource_id, recommendation, estimated_savings
- **alert_configs**: id, user_id, channel (email/slack), webhook_url, thresholds

### Security Considerations
- Customers grant access via IAM role with MINIMAL read-only permissions
- We never store AWS credentials — only role ARN + external ID
- External ID prevents confused deputy attacks
- All data encrypted at rest (Supabase default) and in transit (TLS)
- Stripe handles all payment data (PCI compliant)

---

## 5. MVP Feature Details

### Feature 1: AWS Account Connection
- User creates IAM role in their account using our CloudFormation template or manual policy
- User provides Role ARN to CloudPulse
- We validate access by making a test API call
- Store role_arn + external_id in database

### Feature 2: Cost Dashboard
- **Daily spend**: Bar chart, last 30 days
- **Service breakdown**: Pie chart of spend by AWS service
- **Trend**: Line chart showing spend trajectory
- **Period selector**: Daily / Weekly / Monthly views
- **Data refresh**: Daily via cron job

### Feature 3: Anomaly Detection
- Calculate rolling 7-day average spend per service
- Flag when daily spend exceeds average by configurable threshold (default 25%)
- Severity levels: INFO (25%+), WARNING (50%+), CRITICAL (100%+)
- Algorithm: Simple z-score against rolling window (start simple, improve later)

### Feature 4: Alerts
- Email alerts via SendGrid
- Slack alerts via incoming webhooks
- Configurable: which severity levels trigger alerts
- Daily summary email option (digest of spend + any anomalies)

### Feature 5: Recommendations
- **Idle EC2**: Instances with avg CPU < 5% over 7 days
- **Unused EBS**: Volumes not attached to any instance
- **Old Snapshots**: Snapshots older than 90 days
- **Estimated savings**: Calculate monthly cost of flagged resources
- Future: Reserved Instance recommendations, S3 lifecycle suggestions

---

## 6. Growth & Marketing Strategy

### Channels
1. **Build in Public**: Share progress on Twitter/X, Indie Hackers, Reddit
2. **Content Marketing**: Blog posts on AWS cost optimization (SEO play)
3. **Community**: Engage in r/aws, r/devops, DevOps Discord servers
4. **Product Hunt**: Launch when MVP is polished
5. **Cold Outreach**: Email CTOs/DevOps leads at startups (via Crunchbase)
6. **Partnerships**: Integrate with Terraform, Pulumi communities

### Content Ideas
- "How We Cut Our AWS Bill by 40% in 30 Minutes"
- "5 AWS Resources You're Paying For But Not Using"
- "AWS Cost Explorer vs CloudPulse: What You're Missing"
- "The $10k/month AWS Mistake Most Startups Make"

---

## 7. 90-Day Roadmap

### Month 1: Build MVP (Weeks 1-4)
- Week 1-2: Project setup, IAM onboarding, cost data fetching
- Week 3-4: Database, dashboard API, anomaly detection

### Month 2: Polish & Beta (Weeks 5-8)
- Week 5-6: Alert system, recommendations engine
- Week 7-8: Landing page, onboard 5-10 beta users

### Month 3: Launch & Iterate (Weeks 9-12)
- Week 9-10: Iterate on beta feedback, fix bugs
- Week 11-12: Add Stripe billing, public launch

---

## 8. Risk Register
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| AWS changes API pricing | Low | High | Monitor announcements, have fallback |
| Security breach of customer data | Low | Critical | Minimal permissions, encryption, audit logs |
| Low user adoption | Medium | High | Validate before building, pivot niche |
| AWS releases better native tools | Medium | Medium | Move faster, better UX, multi-cloud |
| Competitor undercuts pricing | Low | Medium | Focus on UX and niche, not price war |

---

## 9. Decision Log
| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-16 | Chose cloud cost monitoring over IaC drift detection | Larger market, easier sales pitch ("save money"), less competition at low price point |
| 2026-02-16 | Python + FastAPI stack | Founder expertise in Python, boto3 integration |
| 2026-02-16 | Start with AWS only | Most popular cloud, simplify MVP scope |
| 2026-02-16 | Supabase for database | Free tier, built-in auth, reduces scope |
| 2026-02-16 | Hybrid business model (service + SaaS) | Start with services for cash flow, productize over time |

---

## 10. Useful Links & Resources
- AWS Cost Explorer API: https://docs.aws.amazon.com/cost-management/latest/userguide/ce-api.html
- boto3 CE docs: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ce.html
- FastAPI docs: https://fastapi.tiangolo.com/
- Supabase docs: https://supabase.com/docs
- Stripe Python SDK: https://stripe.com/docs/api?lang=python
- SendGrid Python: https://docs.sendgrid.com/for-developers/sending-email/quickstart-python
