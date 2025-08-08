SRE Maturity Model
This model provides a structured framework for assessing the reliability and operational excellence of your services. It is organized into four key pillars.

Pillar 1: Observability
The ability to understand the internal state of a system from its external outputs.

Capability

Green (Mature)

Yellow (Developing)

Red (Inadequate)

Logging

All logs are structured (JSON), include a correlation ID, and use appropriate log levels.

Logs are mostly structured, but correlation IDs may be missing in some services.

Logs are unstructured text, making them difficult to search and analyze.

Metrics

Dashboards exist for all four Golden Signals (Latency, Traffic, Errors, Saturation) for every service.

Basic metrics (CPU/Mem) are tracked, but the Golden Signals are not consistently measured or visible.

Monitoring is reactive, relying on basic host-level checks only.

Tracing

End-to-end distributed tracing is implemented, allowing for the analysis of a request across all services.

Tracing is implemented within some services but is not connected across service boundaries.

No distributed tracing is in place.

Pillar 2: Reliability & Performance
The principles and practices that ensure a service meets its availability and performance targets.

Capability

Green (Mature)

Yellow (Developing)

Red (Inadequate)

SLIs & SLOs

SLIs are clearly defined and tracked, and customer-facing SLOs are published and visible on dashboards.

SLIs are defined but are not consistently measured or tied to user experience. SLOs are internal goals only.

No formal SLIs or SLOs exist for the service.

Error Budgets

Error budgets are automatically calculated from SLOs and are used to gate high-risk releases.

An error budget is calculated but is only used as a reporting metric, not for decision-making.

The concept of an error budget is not used.

Performance Testing

Automated performance and load testing are integrated into the CI/CD pipeline.

Performance testing is done manually and infrequently before major releases.

No performance testing is conducted.

Pillar 3: Incident Management & Response
The process for responding to, resolving, and learning from incidents.

Capability

Green (Mature)

Yellow (Developing)

Red (Inadequate)

Alerting

Alerts are highly actionable, have a low false-positive rate, and link directly to a detailed runbook.

Alerts exist but are often noisy, and runbooks are either missing or out of date.

Alerting is either non-existent or so noisy that it is ignored.

Postmortems

A blameless postmortem process is consistently followed for all significant incidents, with action items tracked to completion.

Postmortems are conducted, but they often focus on blame, and action items are not consistently tracked.

No formal postmortem process exists.

Pillar 4: Automation & Toil Reduction
The practice of automating repetitive, manual tasks to free up engineers for more valuable work.

Capability

Green (Mature)

Yellow (Developing)

Red (Inadequate)

CI/CD

The entire path to production is fully automated, with automated quality and security gates at each stage.

Builds and tests are automated, but deployments are manual or require significant human intervention.

The build and deployment process is entirely manual.

Capacity Planning

Capacity planning is based on automated forecasting from historical usage data, with proactive scaling.

Capacity is reviewed manually on a quarterly or annual basis, often leading to over or under-provisioning.

Capacity is only added reactively after a capacity-related incident occurs.
