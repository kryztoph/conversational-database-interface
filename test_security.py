#!/usr/bin/env python3
"""
Security Test Suite for Read-Only SQL Mode
Tests SQL injection protection and write operation blocking
"""

import sys
from chat import DatabaseManager

def test_query_validation():
    """Test the query validation logic"""
    db = DatabaseManager()
    
    print("=" * 70)
    print("SECURITY TEST SUITE - Read-Only SQL Mode")
    print("=" * 70)
    print()
    
    # Test cases: (query, should_pass, description)
    test_cases = [
        # Valid SELECT queries (should pass)
        ("SELECT * FROM users", True, "Simple SELECT query"),
        ("SELECT id, name FROM products WHERE price > 100", True, "SELECT with WHERE clause"),
        ("SELECT COUNT(*) FROM orders", True, "SELECT with aggregate function"),
        ("WITH cte AS (SELECT * FROM users) SELECT * FROM cte", True, "Common Table Expression (CTE)"),
        ("SELECT * FROM users;", True, "SELECT with trailing semicolon"),
        ("  SELECT  *  FROM  users  ", True, "SELECT with extra whitespace"),
        
        # Invalid write operations (should fail)
        ("INSERT INTO users VALUES (1, 'test')", False, "INSERT operation"),
        ("UPDATE users SET name = 'hacked'", False, "UPDATE operation"),
        ("DELETE FROM users WHERE id = 1", False, "DELETE operation"),
        ("DROP TABLE users", False, "DROP TABLE operation"),
        ("CREATE TABLE hackers (id INT)", False, "CREATE TABLE operation"),
        ("ALTER TABLE users ADD COLUMN evil TEXT", False, "ALTER TABLE operation"),
        ("TRUNCATE TABLE users", False, "TRUNCATE operation"),
        
        # SQL injection attempts (should fail)
        ("SELECT * FROM users; DROP TABLE users;", False, "Multi-statement injection"),
        ("SELECT * FROM users; DELETE FROM users WHERE 1=1;", False, "Stacked queries injection"),
        ("'; DROP TABLE users; --", False, "Comment-based injection"),
        
        # Edge cases
        ("EXECUTE sp_malicious", False, "EXECUTE stored procedure"),
        ("CALL malicious_function()", False, "CALL function"),
        ("GRANT ALL ON users TO hacker", False, "GRANT privileges"),
        ("REVOKE ALL ON users FROM admin", False, "REVOKE privileges"),
    ]
    
    passed = 0
    failed = 0
    
    for query, should_pass, description in test_cases:
        try:
            db.validate_read_only_query(query)
            result = "PASS"
            actual_pass = True
        except Exception as e:
            result = "BLOCK"
            actual_pass = False
            error_msg = str(e)
        
        expected = "PASS" if should_pass else "BLOCK"
        status = "✅" if (actual_pass == should_pass) else "❌"
        
        if actual_pass == should_pass:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} [{result:5}] {description}")
        print(f"   Query: {query[:60]}")
        if not actual_pass:
            print(f"   Reason: {error_msg[:60]}")
        print()
    
    print("=" * 70)
    print(f"Test Results: {passed} passed, {failed} failed out of {len(test_cases)} total")
    print("=" * 70)
    
    if failed == 0:
        print("\n✅ ALL TESTS PASSED - Security measures are working correctly!")
        return 0
    else:
        print(f"\n❌ {failed} TEST(S) FAILED - Review security implementation!")
        return 1

if __name__ == "__main__":
    sys.exit(test_query_validation())
