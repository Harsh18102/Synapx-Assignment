# Synapx — Autonomous Insurance Claims Processing Agent (Lite)

## What this repo contains
A lightweight FNOL extraction + routing agent that:
- extracts key fields from ACORD-like FNOL documents (policy, incident, claimant, vehicle, estimate, attachments)
- validates missing/inconsistent fields
- classifies claim type (motor / property / injury / other)
- routes claims using simple deterministic rules (Fast-track / Manual Review / Investigation / Specialist Queue)
- outputs JSON: `extractedFields`, `missingFields`, `flags`, `recommendedRoute`, `reasoning`
