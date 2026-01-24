# /speckit.versioning
MAJOR.MINOR.PATCH

Breaking changes:
- Required env vars renamed
- Tool schemas changed incompatibly
- Behavior changes that alter booking confirmations or FAQ grounding
- Removal or renaming of supported run modes

Minor changes:
- New optional env vars
- New scheduler providers behind same interface
- New FAQ sources behind same interface

Patch:
- Bug fixes, perf, docs, tests

## Evaluation methodology
- Use human evaluators for golden scenarios
- Automated checks for robustness scenarios
- A/B testing for conversation quality improvements
- Regular review of failure cases to identify patterns