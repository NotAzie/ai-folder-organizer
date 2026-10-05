# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of AI Folder Organizer seriously. If you discover a security vulnerability, please report it responsibly.

### How to Report

**Please do not open public GitHub issues for security vulnerabilities.**

Instead, report vulnerabilities by:

1. **Email**: Contact the maintainers directly (see contact information below)
2. **Include**:
   - Description of the vulnerability
   - Steps to reproduce the issue
   - Potential impact
   - Any suggestions for remediation (optional)

### What to Expect

- **Acknowledgment**: You will receive an acknowledgment of your report within 48 hours
- **Investigation**: We will investigate the vulnerability and determine its severity
- **Updates**: You will receive periodic updates on our progress
- **Resolution**: We will work on a fix and release timeline
- **Credit**: With your permission, we will credit you in the security advisory

### Security Considerations for This Project

When using or contributing to AI Folder Organizer, be aware of:

#### 1. API Key Security

**CRITICAL**: API keys must never be hardcoded in source code or committed to version control.

- Use environment variables: `AI_FOLDER_ORG_API_KEY`
- Configuration files with secrets should be in `.gitignore`
- Never share your API key publicly
- Rotate keys if they are accidentally exposed

#### 2. File Operation Safety

The tool performs file system operations (move, rename, create folder):

- Always review dry-run output before executing
- Keep rollback manifests until you're sure operations succeeded
- Test on non-critical folders first
- The tool creates backups via rollback manifests, but always have your own backups for important data

#### 3. LLM API Usage

- The tool sends folder structure information to LLM APIs
- Review what information is sent in prompts
- Be aware of API rate limits and costs
- Sensitive file names or paths may be visible to the LLM provider

#### 4. Third-Party Dependencies

- Keep dependencies updated to receive security patches
- Review dependency updates for breaking changes
- Use virtual environments to isolate project dependencies

### Disclosure Policy

When we receive a security report, we will:

1. Confirm receipt of the report
2. Assess the severity and impact
3. Develop and test a fix
4. Prepare a security advisory
5. Release the fix
6. Publish the security advisory (with credit to the reporter, if permitted)

We will not disclose the vulnerability publicly until a fix is available.

## Security Best Practices for Users

When using AI Folder Organizer:

- **Protect your API key**: Never commit it, share it, or expose it in logs
- **Review before executing**: Always use dry-run mode first
- **Backup important data**: Keep your own backups before organizing important folders
- **Start small**: Test on non-critical folders first
- **Keep software updated**: Use the latest version for security fixes
- **Use virtual environments**: Isolate project dependencies
- **Review permissions**: Ensure the tool only accesses folders you intend

## Contact

For security-related concerns, please contact the maintainers through [INSERT CONTACT METHOD].

Thank you for helping keep AI Folder Organizer secure!
