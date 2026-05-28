# Cloud Migration Best Practices (AWS-Focused)

## The 7 Rs Migration Strategy Framework
Every application in a migration portfolio should be assigned a disposition using the 7 Rs
framework: Retire (decommission), Retain (keep on-premises for now), Rehost (lift and
shift to EC2), Relocate (move VMware workloads with minimal change), Repurchase (move to a
SaaS equivalent), Replatform (lift and optimize, for example move a self-managed database
to Amazon RDS), and Refactor (re-architect into cloud-native services). Most enterprise
portfolios are 60% rehost or replatform and 10-20% refactor; refactoring everything is a
common and expensive mistake.

## Migration Phases
A disciplined migration follows three phases: Assess, Mobilize, and Migrate-and-Modernize.
In Assess, build the application portfolio inventory, capture dependencies, and produce a
business case with total cost of ownership. In Mobilize, build the landing zone, establish
the operating model, close skills gaps, and run a small proof-of-concept migration wave to
de-risk the approach. In Migrate-and-Modernize, execute migration in waves grouped by
dependency, with each wave following a repeatable runbook.

## Landing Zone and Foundation
Before migrating any workload, establish a secure, multi-account landing zone. Use AWS
Organizations with separate accounts for production, non-production, security, logging, and
shared services. Apply Service Control Policies for guardrails, centralize logging with
CloudTrail and CloudWatch, and codify everything with infrastructure as code such as
Terraform or AWS CDK. A landing zone built by hand does not scale and is not auditable.

## Wave Planning
Group applications into migration waves based on dependency clusters, not arbitrary dates.
Applications that share a database or chatty integrations must move together to avoid
cross-environment latency. Sequence waves from low-risk and low-complexity to high-risk so
the team builds muscle and the runbook matures before tackling critical systems.

## Reliability and Scalability
To improve scalability, design for horizontal scaling using Auto Scaling Groups or
container orchestration with Amazon ECS or EKS, and decouple components with managed queues
such as Amazon SQS. Use managed services (RDS, ElastiCache, S3) instead of self-managed
equivalents to offload operational burden. Multi-AZ deployment is the baseline for
production reliability; multi-Region is reserved for workloads with strict recovery
objectives because it materially increases cost and complexity.

## Cutover and Hypercare
Each wave ends with a planned cutover during an agreed maintenance window, with a documented
rollback plan tested in advance. After cutover, run a hypercare period (typically two to
four weeks per wave) where the delivery team monitors closely and resolves incidents before
handing operations to the run team. An engagement is not done at cutover; it is done at
hypercare exit.

## Common Risks and Mitigations
The most common migration risks are undiscovered dependencies, data transfer time for large
datasets, and performance regressions after migration. Mitigate dependencies with automated
discovery tooling, mitigate data transfer with services like AWS DataSync or Snowball for
very large volumes, and mitigate performance regressions with load testing against the
target environment before cutover. Underestimating the effort of the landing zone and the
operating model is the single most common cause of cloud program overruns.

## Cost Management
Establish cost visibility from day one with tagging standards and AWS Cost Explorer. Right
size instances after observing real utilization rather than copying on-premises sizing.
Reserved Instances or Savings Plans should be purchased only after workloads stabilize.
