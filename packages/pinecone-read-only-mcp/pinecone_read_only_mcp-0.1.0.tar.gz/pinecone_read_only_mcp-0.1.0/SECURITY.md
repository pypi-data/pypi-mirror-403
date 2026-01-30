# Security Policy

## Supported Versions

Use this section to tell people about which versions of your project are currently being supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of our software seriously. If you believe you've found a security vulnerability in Pinecone Read-Only MCP, please follow these steps:

1. **Email**: Send a report to will@cppalliance.org with the details of the vulnerability.
2. **Subject Line**: Use "Pinecone Read-Only MCP Security Vulnerability" as your subject line.
3. **Details**: Please provide as much information as possible about the vulnerability, including:
   - Steps to reproduce
   - Potential impact
   - Suggested fixes (if any)
4. **Response Time**: We aim to acknowledge receipt of your report within 48 hours.
5. **Disclosure**: We request that you do not publicly disclose the issue until we've had a chance to address it.

## Security Measures

Pinecone Read-Only MCP implements several security measures:

1. **Input Validation**: All user inputs are validated before processing.
2. **API Key Protection**: Pinecone API keys are handled securely and never logged.
3. **Error Handling**: Error messages are sanitized to prevent information leakage in production.
4. **Dependency Scanning**: Regular scanning for vulnerabilities in dependencies.
5. **Query Limits**: Query results are capped to prevent resource exhaustion.

## Security Considerations for Users

When running Pinecone Read-Only MCP, consider the following security practices:

1. **Protect API Keys**: Never commit API keys to version control. Use environment variables.
2. **Run with Least Privileges**: Always run the server with the minimum necessary privileges.
3. **Restrict Network Access**: When using SSE transport, configure firewalls appropriately.
4. **Keep Updated**: Regularly update the package to receive security fixes.
5. **Monitor Logs**: Watch server logs for unusual patterns that might indicate abuse.

## Environment Variables Security

The following environment variables contain sensitive information:

- `PINECONE_API_KEY`: Your Pinecone API key (required)

Ensure these are set securely and not exposed in logs or error messages.
