#!/usr/bin/env python3
"""
Standalone validation test - no database required
Tests only the query validation logic
"""

def validate_read_only_query(query: str) -> bool:
    """
    Validate that a query is read-only (SELECT only).
    Returns True if valid, raises Exception if not.
    """
    # Remove comments and normalize whitespace
    clean_query = ' '.join(query.split())
    clean_query = clean_query.upper().strip()
    
    # Remove leading/trailing whitespace and semicolons
    clean_query = clean_query.strip('; ')
    
    # Block any write operations
    forbidden_keywords = [
        'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER',
        'TRUNCATE', 'REPLACE', 'MERGE', 'GRANT', 'REVOKE',
        'EXECUTE', 'EXEC', 'CALL', 'DO'
    ]
    
    for keyword in forbidden_keywords:
        if keyword in clean_query:
            raise Exception(f"🛡️ SECURITY: {keyword} operations are not allowed. Read-only mode is enforced.")
    
    # Ensure query starts with SELECT or WITH (for CTEs)
    if not (clean_query.startswith('SELECT') or clean_query.startswith('WITH')):
        raise Exception("🛡️ SECURITY: Only SELECT queries are allowed in read-only mode.")
    
    # Additional check: look for semicolons that might indicate multiple statements
    # Allow only trailing semicolons, not mid-query ones
    semicolon_count = query.count(';')
    if semicolon_count > 1 or (semicolon_count == 1 and not query.strip().endswith(';')):
        raise Exception("🛡️ SECURITY: Multiple statements or inline semicolons are not allowed.")
    
    return True


def run_tests():
    """Test the query validation logic"""
    
    print("=" * 70)
    print("SECURITY VALIDATION TEST - Read-Only SQL Mode")
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
        
        # Additional edge cases
        ("select * from users", True, "Lowercase SELECT"),
        ("SeLeCt * FrOm users", True, "Mixed case SELECT"),
    ]
    
    passed = 0
    failed = 0
    
    for query, should_pass, description in test_cases:
        try:
            validate_read_only_query(query)
            result = "PASS"
            actual_pass = True
            error_msg = None
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
        if not actual_pass and error_msg:
            print(f"   Blocked: {error_msg[:60]}")
        elif actual_pass and not should_pass:
            print(f"   ERROR: Should have been blocked!")
        print()
    
    print("=" * 70)
    print(f"Test Results: {passed} passed, {failed} failed out of {len(test_cases)} total")
    print("=" * 70)
    
    if failed == 0:
        print("\n✅ ALL TESTS PASSED - Security validation is working correctly!")
        return 0
    else:
        print(f"\n❌ {failed} TEST(S) FAILED - Review security implementation!")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(run_tests())
