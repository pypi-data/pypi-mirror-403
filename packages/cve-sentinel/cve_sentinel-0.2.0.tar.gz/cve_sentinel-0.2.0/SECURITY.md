# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in CVE Sentinel, please report it responsibly.

### How to Report

1. **Do NOT** create a public GitHub issue for security vulnerabilities
2. Email the maintainers or use [GitHub's private vulnerability reporting](https://github.com/cawa102/cveSentinel/security/advisories/new)
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 7 days
- **Resolution**: Depends on severity
  - Critical: Within 7 days
  - High: Within 14 days
  - Medium/Low: Within 30 days

### What to Expect

- We will acknowledge receipt of your report
- We will investigate and validate the issue
- We will work on a fix and coordinate disclosure
- We will credit you in the release notes (unless you prefer anonymity)

## Security Best Practices

When using CVE Sentinel:

1. **API Keys**: Never commit API keys to version control
2. **Environment Variables**: Use `CVE_SENTINEL_NVD_API_KEY` for API key storage
3. **Updates**: Keep CVE Sentinel updated to the latest version
4. **CI/CD**: Use `--fail-on` flag in CI pipelines to fail builds on vulnerabilities

## Scope

This security policy covers:

- The CVE Sentinel Python package
- The CLI tool (`cve-sentinel`)
- Configuration file handling
- API integrations (NVD, OSV)

Thank you for helping keep CVE Sentinel secure!
