"""
Base test classes for StartupWebApp test suite.

This module provides base test case classes that all tests should inherit from.
These base classes handle database-specific configurations and ensure consistent
test behavior across different database backends (SQLite, PostgreSQL, etc.).

PostgreSQL Multi-Tenant Architecture:
- Tests use reset_sequences=True to handle PostgreSQL's sequence management
- This ensures tests with explicit IDs (id=1, id=2, etc.) don't conflict
- Critical for multi-database support where tests may run against different forks

Usage:
    from StartupWebApp.utilities.test_base import PostgreSQLTestCase

    class MyTest(PostgreSQLTestCase):
        def test_something(self):
            # Test code here
            pass
"""

from django.test import TestCase, TransactionTestCase


class PostgreSQLTestCase(TransactionTestCase):
    """
    Base test case for all StartupWebApp tests.

    This class configures Django's TransactionTestCase for PostgreSQL compatibility
    and provides a foundation for future test infrastructure improvements.

    IMPORTANT: Uses TransactionTestCase instead of TestCase
    - TestCase doesn't support reset_sequences (Django limitation)
    - TransactionTestCase is slightly slower but necessary for PostgreSQL sequence management
    - Each test runs in its own transaction (no transaction wrapping)

    Key Features:
    - reset_sequences=True: Resets database sequences after each test
      This is critical for PostgreSQL when tests use explicit IDs (e.g., id=1)
      SQLite handles this automatically, but PostgreSQL requires explicit resets

    Why reset_sequences is needed:
    - Many tests create objects with explicit IDs: Model.objects.create(id=1, ...)
    - PostgreSQL's auto-increment sequences don't advance when explicit IDs are used
    - Without reset_sequences, subsequent tests fail with "duplicate key" errors
    - With reset_sequences, Django resets sequences to max(id)+1 after each test

    Performance Note:
    - TransactionTestCase is slower than TestCase (no transaction shortcuts)
    - But necessary for PostgreSQL multi-tenant architecture
    - Test suite may run 20-30% slower, but ensures correctness

    Future Enhancements:
    - Multi-database routing for fork-specific test databases
    - Transaction isolation helpers
    - PostgreSQL-specific assertion methods
    - Connection pooling test utilities

    Example:
        class OrderAPITest(PostgreSQLTestCase):
            def setUp(self):
                # This will work correctly with PostgreSQL sequences
                Skutype.objects.create(id=1, title='product')
                Skuinventory.objects.create(id=1, title='In Stock')

            def test_order_creation(self):
                # Sequences are reset after setUp, so auto-IDs work correctly
                order = Order.objects.create(...)  # Gets next available ID
    """
    reset_sequences = True


# Alias for backward compatibility and shorter imports
BaseTestCase = PostgreSQLTestCase
