# Hybrid Identity and ADFS Endpoint Detection

This document describes the new hybrid identity checking features added to Simple Port Checker.

## Overview

The new `hybrid-identity` command checks if a domain has hybrid identity setup, which typically includes:

- **ADFS (Active Directory Federation Services)** endpoints
- **Federation metadata** endpoints
- **Azure AD integration** 
- **OpenID Connect configuration**
- **DNS records** indicating Microsoft services

This is useful for:
- Security audits of enterprise domains
- Identifying federation services
- Checking Azure AD hybrid deployments
- Discovering authentication endpoints

## Features

### 1. ADFS Endpoint Detection

The tool uses **multiple detection methods** to find ADFS endpoints:

#### Method 1: Azure AD Login Flow (Most Reliable) 🎯

This is the **primary detection method** and simulates what happens when you try to login at Azure Portal:

1. Queries Azure AD's user realm API: `https://login.microsoftonline.com/common/userrealm/test@domain.com`
2. Checks if the domain is configured as "Federated" (vs "Managed")
3. Extracts the actual ADFS endpoint from the `AuthURL` field
4. Alternatively, uses the modern `GetCredentialType` API for federation redirect URL

**Why this is better:**
- ✅ Returns the **actual ADFS endpoint** configured in Azure AD
- ✅ Works even if ADFS is behind a firewall (endpoint is in Azure AD config)
- ✅ This is exactly how Azure Portal discovers ADFS endpoints
- ✅ No guessing of subdomains or paths needed

#### Method 2: Direct ADFS Endpoint Probing

If the Azure AD method doesn't find federation, the tool falls back to checking common ADFS paths:
- `/adfs/ls` - The standard ADFS login endpoint
- `/adfs/ls/IdpInitiatedSignOn.aspx` - IdP-initiated sign-on page
- `/adfs/ls/IdpInitiatedSignon.aspx` - Alternative sign-on page

It checks both the main domain and common ADFS subdomains:
- `adfs.domain.com`
- `sts.domain.com` (Security Token Service)
- `federation.domain.com`
- `fs.domain.com`

### 2. Federation Metadata Discovery

Checks for WS-Federation metadata endpoints:
- `/FederationMetadata/2007-06/FederationMetadata.xml`
- `/adfs/services/trust/2005/windowstransport`
- `/adfs/services/trust/mex`

### 3. Azure AD Integration Detection

Identifies Azure AD integration by:
- Checking for redirects to `login.microsoftonline.com`
- Checking for redirects to `login.windows.net`
- Analyzing response headers for Azure AD indicators

### 4. OpenID Connect Configuration

Looks for OpenID Connect discovery documents:
- `/.well-known/openid-configuration`
- `/adfs/.well-known/openid-configuration`

### 5. DNS Record Analysis

Examines DNS records for hybrid identity indicators:
- **A records** - IP addresses
- **CNAME records** - Canonical names
- **TXT records** - Microsoft domain verification records
- **MX records** - Microsoft 365 mail servers
- **ADFS subdomains** - Common federation service subdomains

## Usage

### Basic Command

Check a single domain:
```bash
port-checker hybrid-identity example.com
```

### Multiple Domains

Check multiple domains:
```bash
port-checker hybrid-identity domain1.com domain2.com domain3.com
```

### Batch Processing

Check domains from a file:
```bash
port-checker hybrid-identity $(cat domains.txt)
```

### With Output File

Save results to JSON:
```bash
port-checker hybrid-identity example.com --output results.json
```

### Verbose Mode

Show detailed information including DNS records:
```bash
port-checker hybrid-identity example.com --verbose
```

### Custom Timeout

Set a custom timeout (default is 10 seconds):
```bash
port-checker hybrid-identity example.com --timeout 15
```

### Concurrent Checks

Adjust the number of concurrent checks (default is 10):
```bash
port-checker hybrid-identity domain1.com domain2.com --concurrent 5
```

## Examples

### Example 1: Enterprise Domain Audit

```bash
port-checker hybrid-identity \
  contoso.com \
  fabrikam.com \
  northwind.com \
  --output audit-results.json \
  --verbose
```

### Example 2: Check Known Microsoft Domains

```bash
port-checker hybrid-identity \
  microsoft.com \
  azure.microsoft.com \
  login.microsoftonline.com \
  --verbose
```

### Example 3: Bulk Domain Check

```bash
# Create a file with domains
echo "example1.com" > domains.txt
echo "example2.com" >> domains.txt
echo "example3.com" >> domains.txt

# Check all domains
port-checker hybrid-identity $(cat domains.txt) --output results.json
```

## Output Format

### Console Output

The tool displays a detailed table for each domain showing:
- Overall status (Hybrid Identity Detected or Not Found)
- ADFS endpoint detection status and URL
- Federation metadata status
- Azure AD integration status
- OpenID configuration status
- DNS record information
- Response time

### Summary Table

After checking all domains, a summary table shows:
- Total domains checked
- Number with hybrid identity
- Number with ADFS endpoints
- Number with federation metadata
- Number with Azure AD integration
- Number with OpenID configuration
- Number of errors

### JSON Output

When using `--output`, results are saved in JSON format:

```json
{
  "scan_time": "2025-10-05T10:30:00",
  "total_time": 15.23,
  "total_targets": 3,
  "results": [
    {
      "fqdn": "example.com",
      "has_hybrid_identity": true,
      "has_adfs": true,
      "adfs_endpoint": "https://adfs.example.com/adfs/ls",
      "adfs_status_code": 200,
      "federation_metadata_found": true,
      "azure_ad_detected": false,
      "openid_config_found": true,
      "dns_records": {
        "A": ["192.0.2.1"],
        "CNAME": [],
        "TXT": ["MS=ms12345678"],
        "MX": ["mail.example.com"],
        "microsoft_verification": true,
        "adfs_subdomains": ["adfs", "sts"]
      },
      "error": null,
      "response_time": 5.12
    }
  ]
}
```

## Indicators of Hybrid Identity

The tool considers a domain to have hybrid identity if ANY of the following are found:

1. **ADFS endpoint** responding with ADFS indicators
2. **Federation metadata** endpoints accessible
3. **Azure AD integration** detected via redirects
4. **OpenID Connect** configuration found

Additionally, DNS records can provide supporting evidence:
- Microsoft domain verification TXT records
- Microsoft 365 MX records
- ADFS-related subdomains

## Use Cases

### Security Auditing

Check if your organization's domains properly expose (or hide) federation services:
```bash
port-checker hybrid-identity $(cat corporate-domains.txt) --output security-audit.json
```

### Migration Planning

Identify which domains have hybrid identity before cloud migration:
```bash
port-checker hybrid-identity \
  legacy-domain1.com \
  legacy-domain2.com \
  --verbose --output migration-assessment.json
```

### Troubleshooting

Verify ADFS endpoints are accessible:
```bash
port-checker hybrid-identity your-domain.com --verbose
```

### Reconnaissance (Ethical)

Identify authentication mechanisms for penetration testing (with permission):
```bash
port-checker hybrid-identity target.com --output recon-results.json
```

## Technical Details

### Network Behavior

The tool:
- Uses HTTPS for all endpoint checks
- Follows redirects when checking Azure AD integration
- Disables SSL verification for initial checks (can encounter self-signed certs)
- Sets a custom User-Agent: `SimplePortChecker/1.0 (Hybrid Identity Scanner)`
- Respects the configured timeout for all requests
- Performs concurrent checks up to the specified limit

### DNS Resolution

DNS checks use the system's default DNS resolver and query:
- A records for IP addresses
- CNAME records for canonical names
- TXT records for verification strings
- MX records for mail servers
- Common ADFS subdomains

### Error Handling

The tool gracefully handles:
- Network timeouts
- DNS resolution failures
- Connection errors
- SSL/TLS errors
- Invalid responses

Errors are reported per-domain without stopping the entire scan.

## Integration with Existing Features

This new command complements existing Simple Port Checker features:

### Used with L7 Detection
```bash
# First check for hybrid identity
port-checker hybrid-identity example.com --verbose

# Then check L7 protection
port-checker l7-check example.com --verbose
```

### Used with DNS Trace
```bash
# Check hybrid identity with DNS details
port-checker hybrid-identity example.com --verbose

# Compare with DNS trace
port-checker dns-trace example.com --verbose
```

### Used with Certificate Analysis
```bash
# Check hybrid identity
port-checker hybrid-identity example.com

# Analyze ADFS certificate
port-checker cert-check adfs.example.com
```

## Security Considerations

### What This Tool Does
- Performs **passive** reconnaissance
- Makes standard HTTPS requests
- Queries public DNS records
- Checks publicly accessible endpoints

### What This Tool Does NOT Do
- Attempt authentication
- Exploit vulnerabilities
- Perform brute force attacks
- Access unauthorized resources

### Best Practices
1. Only scan domains you own or have permission to test
2. Be aware that scans may be logged by target systems
3. Use rate limiting (--concurrent) to avoid overwhelming targets
4. Consider legal and compliance requirements in your jurisdiction

## Limitations

- Cannot detect hybrid identity setups that don't use standard paths
- May have false negatives if endpoints are blocked by firewalls
- Cannot verify actual authentication functionality
- DNS checks may not detect all Microsoft service integrations
- Requires network connectivity to targets

## Troubleshooting

### "No Hybrid Identity Found" but you know it exists

Try:
1. Increase timeout: `--timeout 30`
2. Use verbose mode to see details: `--verbose`
3. Check if endpoints use non-standard paths
4. Verify network connectivity to the domain
5. Check if a firewall is blocking requests

### Timeouts

If you see many timeouts:
1. Increase timeout: `--timeout 20`
2. Reduce concurrency: `--concurrent 5`
3. Check your internet connection
4. Verify the domain is accessible

### DNS Errors

If DNS resolution fails:
1. Check if the domain exists
2. Verify your DNS resolver is working
3. Try with a different network
4. Check for typos in domain names

## Future Enhancements

Potential future improvements:
- Support for SAML endpoints
- OAuth 2.0 discovery
- Kerberos realm detection
- Windows authentication detection
- Custom endpoint path configuration
- Certificate validation for ADFS endpoints
- Integration with Active Directory queries

## Related Commands

- `l7-check` - Check for L7 protection services (WAF, CDN)
- `dns-trace` - Trace DNS records and resolved IPs
- `cert-check` - Analyze SSL/TLS certificates
- `scan` - Port scanning
- `mtls-check` - Check mTLS authentication

## References

- [Microsoft Documentation: Hybrid Identity](https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ready/landing-zone/design-area/identity-access-active-directory-hybrid-identity)
- [ADFS Documentation](https://learn.microsoft.com/en-us/windows-server/identity/ad-fs/ad-fs-overview)
- [Azure AD Integration](https://learn.microsoft.com/en-us/azure/active-directory/hybrid/)
- [WS-Federation](https://en.wikipedia.org/wiki/WS-Federation)
- [OpenID Connect Discovery](https://openid.net/specs/openid-connect-discovery-1_0.html)
