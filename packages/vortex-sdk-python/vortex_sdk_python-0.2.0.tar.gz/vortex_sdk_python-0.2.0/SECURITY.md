# Security Policy

## Supported Versions

We release patches for security vulnerabilities for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of the Vortex SDK Python wrapper seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### Please DO NOT:

- Open a public GitHub issue
- Publicly disclose the vulnerability before it has been addressed

### Please DO:

**Report security vulnerabilities to: security@pendulumchain.tech**

Include the following information:

- Type of vulnerability
- Full paths of source file(s) related to the vulnerability
- Location of the affected source code (tag/branch/commit or direct URL)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

### What to Expect:

1. **Acknowledgment**: We will acknowledge your email within 48 hours
2. **Investigation**: We will investigate and validate the vulnerability
3. **Updates**: We will keep you informed about our progress
4. **Fix**: We will work on a fix and coordinate the release
5. **Credit**: We will publicly credit you for responsible disclosure (unless you prefer to remain anonymous)

### Security Update Process:

1. The vulnerability is confirmed and a fix is developed
2. A security advisory is prepared
3. A new version is released with the fix
4. The security advisory is published
5. Users are notified through GitHub Security Advisories

## Security Best Practices

When using the Vortex SDK Python wrapper:

### Protect Sensitive Data

- Never commit API keys, private keys, or credentials to version control
- Use environment variables for sensitive configuration
- Implement proper access controls on systems running the SDK

### Keep Dependencies Updated

```bash
# Check for outdated packages
pip list --outdated

# Update the SDK
pip install --upgrade vortex-sdk-python

# Update Node.js dependencies
npm update @vortexfi/sdk
```

### Validate Input

- Always validate and sanitize user input before passing to SDK methods
- Be cautious with wallet addresses and transaction data
- Implement rate limiting for API calls

### Use HTTPS

- Always use HTTPS endpoints for API calls
- Verify SSL certificates

### Monitor for Issues

- Subscribe to GitHub Security Advisories for this repository
- Review the CHANGELOG.md for security-related updates
- Monitor dependencies for known vulnerabilities

## Known Security Considerations

### Node.js Subprocess Execution

This package executes Node.js code via subprocess. Consider the following:

- The SDK executes JavaScript code from the `@vortexfi/sdk` npm package
- Ensure you install the SDK from trusted sources (npm registry)
- Keep the npm package updated to receive security patches

### Network Communication

- All API communications should use HTTPS
- Validate API responses before processing
- Implement timeouts for network operations (default: 60s)

## Dependency Security

We regularly monitor dependencies for security vulnerabilities:

### Python Dependencies
- Currently minimal (no runtime dependencies)
- Development dependencies are regularly updated

### Node.js Dependencies
- `@vortexfi/sdk` - Official Vortex SDK package
- Transitive dependencies are managed by the SDK maintainers

## Disclosure Policy

- Security vulnerabilities will be disclosed after a fix is available
- We aim to release fixes within 30 days of vulnerability confirmation
- Critical vulnerabilities will be prioritized for faster release

## Comments on This Policy

If you have suggestions on how this process could be improved, please submit a pull request or open an issue.
