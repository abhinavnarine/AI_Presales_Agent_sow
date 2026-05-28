# HIPAA and Healthcare Compliance Guidelines for Cloud Engagements

## When HIPAA Applies
HIPAA applies whenever a system creates, receives, maintains, or transmits Protected Health
Information (PHI). In a cloud migration for a healthcare client, any workload touching PHI
brings the full HIPAA Security Rule and Privacy Rule into scope. The cloud provider is a
Business Associate, and a Business Associate Agreement (BAA) must be executed before any PHI
is placed in the environment. On AWS, the BAA governs which services are HIPAA-eligible; only
HIPAA-eligible services may process PHI.

## Technical Safeguards
The HIPAA Security Rule requires technical safeguards across four areas. Access control
requires unique user identification, automatic logoff, and role-based access enforced with
least privilege. Audit controls require logging and review of access to systems containing
PHI; on AWS this means CloudTrail, CloudWatch Logs, and immutable log storage. Integrity
controls require mechanisms to detect improper alteration of PHI. Transmission security
requires encryption of PHI in transit using TLS 1.2 or higher.

## Encryption Requirements
Encrypt PHI at rest and in transit. At rest, use AWS KMS-managed keys with services such as
S3, EBS, and RDS encryption enabled by default. In transit, enforce TLS everywhere and
disable plaintext endpoints. Key management must support rotation and access auditing.
Although HIPAA technically lists encryption as "addressable," in practice encryption of PHI
is treated as mandatory and its absence must be formally justified, which is rarely
defensible.

## Administrative and Physical Safeguards
Administrative safeguards include a formal risk analysis, a risk management plan, workforce
security training, and an incident response plan. A documented HIPAA risk analysis is a
foundational deliverable for any healthcare cloud engagement and is the first thing auditors
request. Physical safeguards are largely inherited from the cloud provider under the shared
responsibility model, but the client retains responsibility for endpoint and facility
controls on their side.

## Shared Responsibility in Healthcare Cloud
Under the shared responsibility model the cloud provider secures the infrastructure of the
cloud, while the client secures what they put in the cloud: data classification, access
management, encryption configuration, and application-level controls. A migration SOW for a
healthcare client must explicitly map who owns each control so there is no compliance gap at
go-live.

## Audit and Evidence
Maintain an evidence trail demonstrating that controls operate effectively. This includes
access reviews, encryption configuration reports, audit log retention (commonly six years
for HIPAA documentation), and penetration test results. Build compliance evidence collection
into the delivery process rather than scrambling for it before an audit.

## De-identification and Minimum Necessary
Where full PHI is not required, apply de-identification (Safe Harbor or Expert
Determination) to reduce risk, and enforce the minimum-necessary principle so that systems
and users access only the PHI required for their function. Non-production environments should
use de-identified or synthetic data, never live PHI.

## Other Regulated-Industry Notes
For financial services, the analogous frameworks are PCI-DSS for cardholder data and SOX for
financial reporting controls. For any regulated workload, the pattern is the same: identify
the sensitive data, apply encryption and access controls, log everything, and maintain an
auditable evidence trail.
