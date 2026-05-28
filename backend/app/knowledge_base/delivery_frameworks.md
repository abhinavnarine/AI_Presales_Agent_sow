# Delivery Frameworks, Estimation, and Engagement Models

## Delivery Methodology
Cloud migration and modernization engagements are best delivered with an iterative,
wave-based agile approach rather than a single big-bang waterfall. Use two-week sprints
within each phase, a prioritized backlog per workstream, and a regular cadence of demos to
the client. Governance is provided by a weekly steering committee for decisions and risk,
plus a daily stand-up at the delivery team level. This balances agile delivery with the
predictability enterprise clients expect.

## Team Topology
A typical mid-size cloud engagement staffs an Engagement Lead or Delivery Manager, a Cloud
Solution Architect, two to four Cloud or DevOps Engineers, an Application or Migration
Engineer per active wave, a Security and Compliance Specialist (essential for regulated
industries), and part-time QA and Project Management. The architect and security specialist
are continuous; engineering capacity flexes with the number of concurrent waves.

## Estimation Heuristics by Budget Band
Budget bands map to engagement size. A $100k-$250k engagement is a focused assessment plus a
small first wave, roughly three to four months. A $250k-$500k engagement is a full migration
program of moderate scope, roughly five to seven months with multiple waves. A $500k-$1M
engagement is a large multi-wave program with significant modernization, eight to twelve
months. When budget is unknown, infer the band from the number and ambition of objectives.

## Default Timeline Inference
When the timeline field is missing or null, infer a sensible default: assessment-only
engagements default to six to eight weeks; standard migrations default to six months;
large modernization programs default to nine to twelve months. Always state that the
timeline is an inferred default when the input did not provide one, so the SOW is honest
about its assumptions.

## Risk Management
Maintain a living risk register with probability, impact, owner, and mitigation for each
risk. The top recurring delivery risks are scope creep, resource availability on the client
side, dependency discovery surprises, and compliance evidence gaps. Reserve a contingency
(commonly 10-15% of effort) for the highest-uncertainty workstreams, typically discovery and
the first migration wave.

## Acceptance and Quality Gates
Define acceptance criteria for every deliverable and a phase-exit quality gate for every
phase. A wave does not proceed to cutover until its quality gate (testing complete, rollback
tested, runbook approved) is met. This prevents the most expensive failure mode: cutting over
an unready workload and triggering a production incident.

## Engagement Commercial Models
Fixed-fee suits well-defined scope and transfers risk to the delivery partner; it requires a
thorough discovery first. Time-and-materials suits uncertain or evolving scope and keeps the
client in control of priorities. Milestone-based billing is a hybrid that ties payment to
accepted deliverables and is common for migration programs. Match the model to how well the
scope is understood: the less certain the scope, the more the engagement should lean
time-and-materials or a paid discovery before a fixed-fee delivery.

## Knowledge Transfer and Exit
Every engagement must end with knowledge transfer to the client run team: documented
runbooks, architecture diagrams, an operations guide, and hands-on enablement sessions. The
hypercare exit report formally closes the engagement and lists any open items and
recommendations for the next phase.
