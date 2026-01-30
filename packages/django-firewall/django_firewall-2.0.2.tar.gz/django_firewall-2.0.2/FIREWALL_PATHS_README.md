# Firewall Path Rules Management

This document explains how to manage firewall path rules (blacklist and whitelist) through the Django admin interface.

## Overview

The firewall system now supports dynamic management of URL path patterns through a database model. You can create, update, and delete firewall rules via the Django admin interface without modifying code.

## Features

- **Database-driven rules**: Manage path patterns in the database instead of hardcoded lists
- **Admin interface**: Create, update, and delete rules through Django Admin
- **Rule types**: Support for both blacklist (block) and whitelist (allow) rules
- **Priority system**: Control the order in which rules are evaluated
- **Enable/disable**: Temporarily disable rules without deleting them
- **Caching**: Rules are cached for 5 minutes to maintain performance
- **Fallback support**: Falls back to hardcoded rules if database is empty

## Database Model

### FirewallPathRule

Fields:

- `path_pattern`: Regular expression pattern for the path (e.g., `r'/admin/.*'` or `'/config.json'`)
- `rule_type`: Either 'blacklist' or 'whitelist'
- `enabled`: Boolean to enable/disable the rule
- `priority`: Integer for ordering (lower = higher priority)
- `description`: Optional description of what the rule does

## Getting Started

### 1. Run Migrations

First, apply the database migrations:

```bash
python manage.py migrate django_firewall
```

### 2. Import Existing Rules

Import the hardcoded rules from `endpoint_list.py` into the database:

```bash
# Dry run to see what would be imported
python manage.py import_firewall_rules --dry-run

# Import rules (skip existing)
python manage.py import_firewall_rules

# Clear all existing rules and import fresh
python manage.py import_firewall_rules --clear
```

### 3. Access Admin Interface

1. Log in to Django admin as a superuser
2. Navigate to **Django Firewall** → **Firewall Path Rules**
3. You'll see all your imported rules

## Managing Rules via Admin

### Creating a New Rule

1. Click "Add Firewall Path Rule"
2. Fill in the fields:
   - **Path Pattern**: Use regex pattern (e.g., `r'/api/secret/.*'` or `'/admin/.env'`)
   - **Rule Type**: Choose 'blacklist' (block) or 'whitelist' (allow)
   - **Enabled**: Check to activate the rule
   - **Priority**: Lower numbers run first (default: 100)
   - **Description**: Add notes about this rule
3. Click "Save"

### Editing a Rule

1. Click on the rule in the list
2. Modify any field
3. Click "Save"

Note: Changes are automatically cached and will take effect within 5 minutes (or immediately on server restart).

### Deleting a Rule

1. Select the rule(s) to delete
2. Choose "Delete selected items" from the actions dropdown
3. Confirm deletion

### Disabling vs Deleting

Instead of deleting a rule, you can temporarily disable it:

1. Edit the rule
2. Uncheck the "Enabled" field
3. Save

This is useful for testing or temporary changes.

## Rule Evaluation Logic

### Order of Evaluation

1. **Whitelist rules** are checked first (in priority order)
   - If a path matches a whitelist rule, it's **allowed** immediately

2. **Blacklist rules** are checked next (in priority order)
   - If a path matches a blacklist rule, the IP is **blocked**

3. If no rules match, the request proceeds normally

### Priority System

- Rules with **lower priority numbers** are evaluated **first**
- Whitelist rules are always checked before blacklist rules regardless of priority
- When importing, rules are assigned priorities in increments of 10 (10, 20, 30, etc.) to allow easy reordering

### Example Priority Usage

```text
Priority 10:  r'/.*/js/config.js'  (whitelist - high priority)
Priority 50:  r'/admin/.*'         (blacklist - medium priority)
Priority 100: r'/.*.php'           (blacklist - default priority)
Priority 200: r'/backup.php'       (blacklist - low priority, redundant)
```

## Regular Expression Patterns

### Pattern Syntax

The firewall uses Python's `re.match()` which anchors at the start of the string. Common patterns:

```python
'/config.json'          # Exact match
r'/admin/.*'            # /admin/ followed by anything
r'/.*.php'              # Any path ending in .php
r'/api/(v1|v2)/.*'      # /api/v1/ or /api/v2/ followed by anything
r'/.*/\.env.*'          # .env file anywhere in path
```

### Common Patterns

```python
# Block PHP files
r'/.*.php'

# Block WordPress paths
r'/wp-(admin|content|includes)/.*'

# Block .env files anywhere
r'/.*/\.env.*'

# Block specific directories
r'/admin/.*'
r'/backup/.*'

# Allow specific JS config file
r'/.*/js/config.js'
```

## Performance Considerations

### Caching

- Rules are cached for 5 minutes (300 seconds)
- Cache is automatically cleared when rules are created, updated, or deleted
- Cache keys: `firewall_blacklist_rules` and `firewall_whitelist_rules`

### Cache Control

To manually clear the cache:

```python
from django.core.cache import cache
cache.delete('firewall_blacklist_rules')
cache.delete('firewall_whitelist_rules')
```

### Fallback Behavior

If the database query fails or returns no results:

1. The system falls back to hardcoded rules from `DJANGO_FIREWALL_URLS_LIST` and `DJANGO_FIREWALL_URL_WHITE_LIST`
2. An error is logged
3. The firewall continues to function with hardcoded rules

## Best Practices

### 1. Start with Import

Always import existing rules before adding custom ones:

```bash
python manage.py import_firewall_rules
```

### 2. Use Priorities Wisely

- Use increments of 10 (10, 20, 30...) to leave room for insertion
- Keep whitelist priorities low (10-50) for critical allow rules
- Use higher priorities (100+) for general blacklist rules

### 3. Test with Dry Run

Before making bulk changes, test with `--dry-run`:

```bash
python manage.py import_firewall_rules --clear --dry-run
```

### 4. Add Descriptions

Always add descriptions to document why a rule exists:

```text
Description: "Block access to WordPress admin - we don't use WordPress"
Description: "Allow access to public JS config needed for frontend"
```

### 5. Use Enable/Disable for Testing

When troubleshooting, disable rules temporarily instead of deleting them.

## Troubleshooting

### Rules Not Taking Effect

1. **Check caching**: Wait 5 minutes or restart the server
2. **Verify enabled**: Ensure the rule's "Enabled" checkbox is checked
3. **Check pattern**: Test your regex pattern matches the actual path
4. **Review logs**: Check application logs for firewall debug messages

### Pattern Not Matching

Common issues:

- **Case sensitivity**: Patterns are case-sensitive
- **Anchoring**: `re.match()` anchors at start, use `.*` prefix if needed
- **Escaping**: Escape special regex characters: `\.`, `\(`, `\)`

Test patterns in Python:

```python
import re
pattern = r'/admin/.*'
path = '/admin/users'
print(re.match(pattern, path))  # Should match
```

### Cache Issues

If changes aren't appearing:

```bash
# Restart the application server
# Or wait 5 minutes for cache to expire
# Or clear cache manually in Django shell
python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
```

## Security Considerations

### Access Control

- Only **superusers** can manage firewall rules
- Rules are checked on every request (after caching)
- Invalid IP addresses are rejected with logging

### Audit Trail

- `created_at` and `updated_at` timestamps track changes
- Consider adding Django admin logging for rule changes
- Review logs regularly for blocked attempts

### Regular Expression Safety

- Avoid overly complex regex patterns (performance impact)
- Test patterns before deploying to production
- Be careful with `.` (matches any character) - use `\.` for literal dots

## Examples

### Block All PHP Files Except One

```python
# Whitelist (Priority: 10)
Path: r'/public/info.php'
Type: whitelist
Description: Allow public info.php for monitoring

# Blacklist (Priority: 100)
Path: r'/.*.php'
Type: blacklist
Description: Block all PHP files
```

### Block WordPress Paths

```python
Path: r'/wp-admin/.*'
Type: blacklist
Priority: 50
Description: Block WordPress admin (we don't use WP)

Path: r'/wp-content/.*'
Type: blacklist
Priority: 50
Description: Block WordPress content directory

Path: r'/wp-includes/.*'
Type: blacklist
Priority: 50
Description: Block WordPress includes directory
```

### Block Environment Files

```python
Path: r'/.*/\.env.*'
Type: blacklist
Priority: 10
Description: Block .env files anywhere (high priority for security)

Path: r'/.*/\.htaccess'
Type: blacklist
Priority: 10
Description: Block .htaccess files

Path: r'/.*/\.htpasswd'
Type: blacklist
Priority: 10
Description: Block .htpasswd files
```

## Support

For issues or questions:

1. Check logs in your application logging
2. Review this documentation
3. Test patterns in Python shell
4. Contact system administrator

---

**Last Updated**: January 2026
**Version**: 1.0
