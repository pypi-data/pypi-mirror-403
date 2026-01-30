# List of URLs/patterns that should be BLOCKED by the firewall
# These are common attack vectors and sensitive file paths
FirewallURLsList = [
    # PHP attacks
    "/access.php",
    "/alive.php",
    "/backup.php",
    "/phpinfo.php",
    "/php.ini",
    r"/.*\.php",
    r"/.*\.php7",

    # Configuration files
    "/config.json",
    "/env",
    r"/.env.*",
    r"/.*/.env.*",
    r"/app-settings.*",

    # Apache/Nginx sensitive files
    "/.htaccess",
    "/.htpasswd",
    "/admin/.htaccess",
    "/admin/.htpasswd",
    r"/admin/.env.*",

    # Application directories
    r"/application/.env.*",
    r"/application/.htaccess",
    r"/application/.htpasswd",
    r"/backend/.env.*",
    r"/backend/.htaccess",
    r"/backend/.htpasswd",
    r"/dev/.env.*",

    # Config directories
    r"/.*/config",
    r"/config/.*",

    # AWS credentials
    r"/.aws/.*",
    r"/aws.*",
    "/.s3cfg",

    # Firebase
    r"/firebase.*",

    # Git repository
    r"/.git/.*",

    # JavaScript config exposure
    r"/js/config.*",
    r"/js/.env.*",
    r"/js/env.*",
    r"/js/settings.*",

    # Symfony profiler
    r"/_profiler/.*",

    # WordPress attacks
    r"/.*/wlwmanifest.xml",
    r"/wp-admin/.*",
    r"/wp-content/.*",
    r"/wp-includes/.*",
]

# List of URLs/patterns that should be ALLOWED (whitelist)
# These patterns will bypass the firewall check
FirewallURLWhiteList = [
    # Allow legitimate JavaScript config files
    r"/.*/js/config.js",
]


def build_wildcard_or_expression(patterns: list[str]) -> str:
    """
    Build a Cloudflare-style wildcard OR expression from a list of path patterns.

    This is useful for creating Cloudflare WAF rules from the URL list.

    Example output line for one entry:
        (http.request.uri.path wildcard r"/admin/.htaccess")

    The function simply wraps each provided pattern as a raw-quoted string and
    joins them using " or\\n" to keep it readable.

    Args:
        patterns: List of URL patterns

    Returns:
        str: Cloudflare-compatible OR expression
    """
    # Convert regex-like ".*" to wildcard "*" before wrapping
    normalized = [p.replace(".*", "*") for p in patterns]
    parts = [f'(http.request.uri.path wildcard r"{p}")' for p in normalized]
    return " or\n".join(parts)


# Pre-built expression for convenience import/use elsewhere
FirewallURLsExpression: str = build_wildcard_or_expression(FirewallURLsList)
