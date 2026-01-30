"""
DEPRECATED: This package has been renamed to aws-cis-controls-assessment

This is a deprecation shim that redirects to the new package.
"""

import warnings
import sys

# Show deprecation warning
warnings.warn(
    "\n\n"
    "=" * 80 + "\n"
    "⚠️  DEPRECATION WARNING\n"
    "=" * 80 + "\n"
    "The package 'aws-cis-assessment' has been renamed to 'aws-cis-controls-assessment'\n"
    "\n"
    "Please uninstall this package and install the new one:\n"
    "  pip uninstall aws-cis-assessment\n"
    "  pip install aws-cis-controls-assessment\n"
    "\n"
    "This deprecation package will not receive updates.\n"
    "All development continues under 'aws-cis-controls-assessment'.\n"
    "=" * 80 + "\n",
    DeprecationWarning,
    stacklevel=2
)

__version__ = "1.0.3.post1"
__deprecated__ = True


def main():
    """
    Entry point that shows deprecation warning and delegates to the new package.
    """
    print("\n" + "=" * 80)
    print("⚠️  DEPRECATION WARNING")
    print("=" * 80)
    print("The package 'aws-cis-assessment' has been renamed to 'aws-cis-controls-assessment'")
    print()
    print("Please uninstall this package and install the new one:")
    print("  pip uninstall aws-cis-assessment")
    print("  pip install aws-cis-controls-assessment")
    print()
    print("Attempting to run the new package...")
    print("=" * 80 + "\n")
    
    try:
        # Try to import and run the new package
        from aws_cis_assessment.cli.main import main as new_main
        new_main()
    except ImportError:
        print("\n" + "=" * 80)
        print("❌ ERROR: The new package 'aws-cis-controls-assessment' is not installed.")
        print("=" * 80)
        print()
        print("Please install it manually:")
        print("  pip install aws-cis-controls-assessment")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
