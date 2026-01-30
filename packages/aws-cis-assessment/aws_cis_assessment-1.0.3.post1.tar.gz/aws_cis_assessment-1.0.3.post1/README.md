# ⚠️ DEPRECATED: aws-cis-assessment

## This package has been renamed to `aws-cis-controls-assessment`

**DO NOT USE THIS PACKAGE.** It exists only to redirect users to the new package name.

---

## Migration Instructions

### Uninstall the old package:
```bash
pip uninstall aws-cis-assessment
```

### Install the new package:
```bash
pip install aws-cis-controls-assessment
```

---

## Why the change?

The package name was changed from `aws-cis-assessment` to `aws-cis-controls-assessment` to better reflect its purpose: **assessing AWS environments against CIS Controls** (not CIS Benchmarks).

## Version History

| Package Name | Versions | Status |
|--------------|----------|--------|
| `aws-cis-assessment` | 1.0.0 - 1.0.3 | ⚠️ **DEPRECATED** |
| `aws-cis-controls-assessment` | 1.0.4+ | ✅ **ACTIVE** |

## What happens if I install this package?

This deprecation package (v1.0.3.post1) automatically installs `aws-cis-controls-assessment` as a dependency, so you'll get the correct package. However, you should explicitly install the new package name to avoid confusion.

## No Code Changes Required

The internal module structure remains the same (`aws_cis_assessment`), so your existing code will continue to work without modifications.

The CLI command also remains the same: `aws-cis-assess`

## Links

- **New Package on PyPI**: https://pypi.org/project/aws-cis-controls-assessment/
- **GitHub Repository**: https://github.com/yourusername/aws-cis-assessment
- **Documentation**: https://github.com/yourusername/aws-cis-assessment/blob/main/README.md

---

## For the Latest Version

Always use the new package name:

```bash
pip install aws-cis-controls-assessment
```

Current version: **1.0.5** (as of January 26, 2026)

---

**This package will not receive any further updates. All development continues under `aws-cis-controls-assessment`.**
