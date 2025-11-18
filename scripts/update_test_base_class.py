#!/usr/bin/env python3
"""
Script to update all test files to use PostgreSQLTestCase base class.

This script:
1. Finds all test files in the project
2. Updates imports to include PostgreSQLTestCase
3. Replaces TestCase inheritance with PostgreSQLTestCase
4. Preserves all other code structure

Usage:
    # Dry run (no changes, just preview):
    python scripts/update_test_base_class.py --dry-run

    # Single file test:
    python scripts/update_test_base_class.py --single-file StartupWebApp/order/tests/test_product_browsing.py

    # Run for real (updates all files):
    python scripts/update_test_base_class.py

    # Validate (check syntax without modifying):
    python scripts/update_test_base_class.py --validate
"""

import os
import re
import sys
import argparse
from pathlib import Path


def update_test_file(file_path, dry_run=False):
    """
    Update a single test file to use PostgreSQLTestCase.

    Returns: (success: bool, message: str, changes: list)
    """
    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except Exception as e:
        return False, f"Error reading file: {e}", []

    original_content = content
    changes = []

    # Check if file uses TestCase
    if 'TestCase' not in content:
        return False, "No TestCase found", []

    # Check if already using PostgreSQLTestCase
    if 'PostgreSQLTestCase' in content or 'test_base' in content:
        return False, "Already using PostgreSQLTestCase", []

    # Step 1: Update the import statement
    # Look for: from django.test import TestCase
    if 'from django.test import TestCase' in content:
        # Check if there are other imports from django.test
        django_test_import_pattern = r'from django\.test import ([^\n]+)'
        match = re.search(django_test_import_pattern, content)

        if match:
            imports = match.group(1)
            # If only importing TestCase, replace the entire line
            if imports.strip() == 'TestCase':
                old_import = 'from django.test import TestCase'
                new_import = 'from django.test import TestCase\nfrom StartupWebApp.utilities.test_base import PostgreSQLTestCase'
                content = content.replace(old_import, new_import)
                changes.append(f"Added import: from StartupWebApp.utilities.test_base import PostgreSQLTestCase")
            else:
                # Other imports exist, add PostgreSQLTestCase on new line
                content = re.sub(
                    r'(from django\.test import [^\n]+)',
                    r'\1\nfrom StartupWebApp.utilities.test_base import PostgreSQLTestCase',
                    content,
                    count=1
                )
                changes.append(f"Added import after existing django.test imports")

    # Step 2: Replace class inheritance
    # Pattern: class SomeTest(TestCase):
    # Replace with: class SomeTest(PostgreSQLTestCase):
    class_pattern = r'class\s+(\w+)\(TestCase\):'

    matches = re.findall(class_pattern, content)
    if matches:
        for class_name in matches:
            changes.append(f"Updated class {class_name}(TestCase) -> {class_name}(PostgreSQLTestCase)")

        content = re.sub(
            class_pattern,
            r'class \1(PostgreSQLTestCase):',
            content
        )

    # If no changes were made
    if content == original_content:
        return False, "No changes needed", []

    # Write back if not dry run
    if not dry_run:
        try:
            with open(file_path, 'w') as f:
                f.write(content)
        except Exception as e:
            return False, f"Error writing file: {e}", changes

    return True, "Updated" if not dry_run else "Would update", changes


def find_test_files(base_dir):
    """Find all test files in the project."""
    test_files = []

    # Apps to search
    apps = ['order', 'user', 'clientevent', 'StartupWebApp']

    for app in apps:
        tests_dir = base_dir / app / 'tests'
        if tests_dir.exists():
            test_files.extend(sorted(tests_dir.glob('test_*.py')))

    return test_files


def validate_python_syntax(file_path):
    """Validate Python syntax of a file."""
    try:
        with open(file_path, 'r') as f:
            compile(f.read(), file_path, 'exec')
        return True, "Valid Python syntax"
    except SyntaxError as e:
        return False, f"Syntax error: {e}"


def main():
    parser = argparse.ArgumentParser(
        description='Update test files to use PostgreSQLTestCase base class',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without modifying files'
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate Python syntax without modifying files'
    )
    parser.add_argument(
        '--single-file',
        type=str,
        help='Update only a single file (for testing)'
    )

    args = parser.parse_args()

    # Determine base directory
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent / 'StartupWebApp'

    # Get files to process
    if args.single_file:
        test_files = [Path(args.single_file)]
    else:
        test_files = find_test_files(base_dir)

    if not test_files:
        print("No test files found!")
        return 1

    print(f"Found {len(test_files)} test files")
    print("-" * 80)

    if args.dry_run:
        print("🔍 DRY RUN MODE - No files will be modified")
        print("-" * 80)

    if args.validate:
        print("✅ VALIDATION MODE - Checking syntax only")
        print("-" * 80)

    updated_count = 0
    skipped_count = 0
    error_count = 0

    for test_file in test_files:
        relative_path = test_file.relative_to(base_dir) if base_dir in test_file.parents else test_file

        if args.validate:
            # Validation mode
            valid, message = validate_python_syntax(test_file)
            status = "✅" if valid else "❌"
            print(f"{status} {relative_path}: {message}")
            if not valid:
                error_count += 1
        else:
            # Update mode
            success, message, changes = update_test_file(test_file, dry_run=args.dry_run)

            if success:
                icon = "➜" if args.dry_run else "✓"
                print(f"{icon} {relative_path}: {message}")
                for change in changes:
                    print(f"    - {change}")
                updated_count += 1
            elif "Error" in message:
                print(f"❌ {relative_path}: {message}")
                error_count += 1
            else:
                print(f"  {relative_path}: {message}")
                skipped_count += 1

    print("-" * 80)

    if args.validate:
        print(f"Validation: {len(test_files) - error_count}/{len(test_files)} files have valid syntax")
        if error_count > 0:
            print(f"⚠️  {error_count} files have syntax errors!")
            return 1
    else:
        action = "Would update" if args.dry_run else "Updated"
        print(f"Summary: {action} {updated_count} files, skipped {skipped_count} files")
        if error_count > 0:
            print(f"⚠️  {error_count} files had errors!")
            return 1

        if args.dry_run and updated_count > 0:
            print("\n💡 Run without --dry-run to apply changes")

    return 0


if __name__ == '__main__':
    sys.exit(main())
