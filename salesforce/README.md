# FP&A Salesforce DX Extension

This source package complements the Python FP&A service with Salesforce-native UI, Apex, SOSL search, Platform Events, and tests.

## Local quality checks

```powershell
cd salesforce
npm install
npm run test:lwc
sf org login web --alias fpa-dev
sf project deploy start --source-dir force-app --target-org fpa-dev
sf apex run test --class-names FpaPipelineControllerTest --target-org fpa-dev --result-format human --wait 20
```

The deployment target is intentionally supplied at execution time; no org credentials or identifiers are stored in this repository.
