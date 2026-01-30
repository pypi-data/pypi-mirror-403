# Firewall Path Rules - Quick Setup Guide

## What's New?

You can now manage firewall blacklist and whitelist paths through the Django admin interface instead of editing code!

## Quick Setup (3 Steps)

### Step 1: Run the Migration

```bash
python manage.py migrate django_firewall
```

### Step 2: Import Existing Rules

```bash
# See what will be imported (dry run)
python manage.py import_firewall_rules --dry-run

# Import the rules
python manage.py import_firewall_rules
```

This will import all blacklist and whitelist rules from `endpoint_list.py` into the database.

### Step 3: Access Django Admin

1. Go to your Django admin: `https://your-domain/admin/`
2. Navigate to: **Django Firewall → Firewall Path Rules**
3. You can now create, edit, and delete rules!

## Common Tasks

### Add a New Blocked Path

1. In admin, click "Add Firewall Path Rule"
2. Enter:
   - **Path Pattern**: `r'/api/internal/.*'` (example)
   - **Rule Type**: Blacklist
   - **Enabled**: ✓ (checked)
   - **Priority**: 100 (default)
   - **Description**: "Block internal API endpoints"
3. Click "Save"

### Allow a Specific Path

1. In admin, click "Add Firewall Path Rule"
2. Enter:
   - **Path Pattern**: `r'/api/public/health'` (example)
   - **Rule Type**: Whitelist
   - **Enabled**: ✓ (checked)
   - **Priority**: 10 (low number = high priority)
   - **Description**: "Allow health check endpoint"
3. Click "Save"

### Temporarily Disable a Rule

1. Click on the rule in the admin list
2. Uncheck "Enabled"
3. Click "Save"

### Delete a Rule

1. Select the rule(s) by checking the box
2. Choose "Delete selected items" from the Actions dropdown
3. Click "Go" and confirm

## How It Works

### Rule Evaluation

1. **Whitelist rules** are checked first (lowest priority first)
   - If matched → request is **allowed**

2. **Blacklist rules** are checked next (lowest priority first)
   - If matched → IP is **blocked** and logged

3. No match → request proceeds normally

### Caching

- Rules are cached for **5 minutes** for performance
- Cache is auto-cleared when you create/update/delete rules
- Changes take effect immediately after cache refresh

### Fallback

- If database is empty or unavailable, falls back to hardcoded rules in `endpoint_list.py`
- This ensures the firewall keeps working even during database issues

## Testing

### Test Pattern Matching

```python
# In Django shell
python manage.py shell

>>> import re
>>> pattern = r'/admin/.*'
>>> path = '/admin/users'
>>> print(re.match(pattern, path))  # Should match
```

### Check Active Rules

```python
# In Django shell
python manage.py shell

>>> from django_firewall.models import FirewallPathRule
>>>
>>> # Count rules
>>> print(f"Blacklist: {FirewallPathRule.objects.filter(rule_type='blacklist', enabled=True).count()}")
>>> print(f"Whitelist: {FirewallPathRule.objects.filter(rule_type='whitelist', enabled=True).count()}")
>>>
>>> # List all enabled rules
>>> for rule in FirewallPathRule.objects.filter(enabled=True).order_by('rule_type', 'priority'):
>>>     print(f"{rule.rule_type:10} | {rule.priority:3} | {rule.path_pattern}")
```

## Files Changed

1. **`django_firewall/models.py`** - Added `FirewallPathRule` model
2. **`django_firewall/admin.py`** - Added admin interface for path rules
3. **`django_firewall/middleware.py`** - Updated to use database rules with caching
4. **`django_firewall/migrations/0003_firewallpathrule.py`** - Database migration
5. **`django_firewall/management/commands/import_firewall_rules.py`** - Import command

## Need More Help?

See the detailed documentation: `django_firewall/FIREWALL_PATHS_README.md`

## Rollback (if needed)

If you need to rollback:

```bash
# Revert migration
python manage.py migrate django_firewall 0002

# The middleware will automatically fall back to hardcoded rules
```

---

**Ready to use!** Your firewall can now be managed through the admin interface.
