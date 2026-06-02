---
name: claim_checker
track: team
kind: local_guardrail
requires_env: []
inputs: [claim, context]
outputs: [risk_level, required_evidence, publish_guidance]
side_effect: false
---
# claim_checker

Assesses whether a factual claim is ready for a public research brief, Telegram
post, or external-facing summary. It does not verify the claim by itself; it
classifies risk and recommends the evidence needed before publishing.
