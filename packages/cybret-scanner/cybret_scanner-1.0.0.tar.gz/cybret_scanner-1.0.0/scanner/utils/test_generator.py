"""
Test Generator - Automatically generates security tests for fixes

This module provides automated test generation for:
- Security test cases for applied fixes
- Positive test cases (authorized access)
- Negative test cases (unauthorized access)
- Edge cases and boundary conditions
- Integration with popular testing frameworks
"""

import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


class TestGenerator:
    """
    Automatically generates security tests for applied fixes
    
    Features:
    - Generates test cases for each vulnerability type
    - Supports multiple testing frameworks (Jest, Mocha, PyTest, JUnit)
    - Creates positive and negative test cases
    - Includes edge cases and boundary conditions
    - Generates test data and fixtures
    """
    
    def __init__(
        self,
        codebase_path: str,
        test_framework: str = "auto",
        test_directory: str = "tests/security"
    ):
        """
        Initialize test generator
        
        Args:
            codebase_path: Path to the codebase root
            test_framework: Testing framework (jest, mocha, pytest, junit, auto)
            test_directory: Directory for generated tests
        """
        self.codebase_path = Path(codebase_path).resolve()
        self.test_framework = test_framework
        self.test_directory = self.codebase_path / test_directory
        
        # Auto-detect framework if needed
        if self.test_framework == "auto":
            self.test_framework = self._detect_test_framework()
    
    def generate_tests(
        self,
        llm_results: Dict[str, Any],
        applied_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate security tests for all applied fixes
        
        Args:
            llm_results: Results from LLM analysis
            applied_results: Results from fix application
            
        Returns:
            Dictionary with test generation results
        """
        try:
            # Create test directory if it doesn't exist
            self.test_directory.mkdir(parents=True, exist_ok=True)
            
            generated_tests = []
            approved_fixes = llm_results.get('approved_fixes', [])
            
            for fix_analysis in approved_fixes:
                # Check if this fix was successfully applied
                location = fix_analysis.get('location', '')
                file_path = location.split(':')[0] if ':' in location else location
                
                was_applied = any(
                    r['success'] and file_path in r.get('file', '')
                    for r in applied_results
                )
                
                if not was_applied:
                    continue
                
                # Generate tests for this fix
                test_result = self._generate_test_for_fix(fix_analysis)
                
                if test_result['success']:
                    generated_tests.append(test_result)
            
            # Generate test suite file
            suite_result = self._generate_test_suite(generated_tests)
            
            return {
                'success': True,
                'tests_generated': len(generated_tests),
                'test_files': [t['test_file'] for t in generated_tests],
                'test_suite': suite_result.get('suite_file'),
                'framework': self.test_framework,
                'test_directory': str(self.test_directory)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'tests_generated': 0
            }
    
    def _detect_test_framework(self) -> str:
        """Auto-detect testing framework from project files"""
        
        # Check for JavaScript/TypeScript frameworks
        package_json = self.codebase_path / "package.json"
        if package_json.exists():
            content = package_json.read_text()
            if 'jest' in content.lower():
                return 'jest'
            elif 'mocha' in content.lower():
                return 'mocha'
        
        # Check for Python frameworks
        requirements_files = [
            self.codebase_path / "requirements.txt",
            self.codebase_path / "requirements-dev.txt",
            self.codebase_path / "setup.py"
        ]
        
        for req_file in requirements_files:
            if req_file.exists():
                content = req_file.read_text()
                if 'pytest' in content.lower():
                    return 'pytest'
                elif 'unittest' in content.lower():
                    return 'unittest'
        
        # Check for Java frameworks
        pom_xml = self.codebase_path / "pom.xml"
        if pom_xml.exists():
            content = pom_xml.read_text()
            if 'junit' in content.lower():
                return 'junit'
        
        # Default based on file types
        js_files = list(self.codebase_path.glob("**/*.js")) + list(self.codebase_path.glob("**/*.ts"))
        py_files = list(self.codebase_path.glob("**/*.py"))
        java_files = list(self.codebase_path.glob("**/*.java"))
        
        if js_files:
            return 'jest'
        elif py_files:
            return 'pytest'
        elif java_files:
            return 'junit'
        
        return 'jest'  # Default
    
    def _generate_test_for_fix(self, fix_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test file for a specific fix"""
        
        try:
            vuln_type = fix_analysis.get('vulnerability_type', 'Unknown')
            location = fix_analysis.get('location', 'unknown')
            severity = fix_analysis.get('severity', 'medium')
            
            # Extract file and function info
            file_path = location.split(':')[0] if ':' in location else location
            function_name = self._extract_function_name(fix_analysis)
            
            # Generate test content based on framework
            if self.test_framework in ['jest', 'mocha']:
                test_content = self._generate_javascript_test(fix_analysis)
                test_file_name = f"security.{self._sanitize_filename(function_name)}.test.js"
            elif self.test_framework in ['pytest', 'unittest']:
                test_content = self._generate_python_test(fix_analysis)
                test_file_name = f"test_security_{self._sanitize_filename(function_name)}.py"
            elif self.test_framework == 'junit':
                test_content = self._generate_java_test(fix_analysis)
                test_file_name = f"Security{self._capitalize(function_name)}Test.java"
            else:
                test_content = self._generate_generic_test(fix_analysis)
                test_file_name = f"security_{self._sanitize_filename(function_name)}.test"
            
            # Write test file
            test_file_path = self.test_directory / test_file_name
            test_file_path.write_text(test_content, encoding='utf-8')
            
            return {
                'success': True,
                'test_file': str(test_file_path),
                'vulnerability_type': vuln_type,
                'location': location,
                'test_count': self._count_test_cases(test_content)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'location': fix_analysis.get('location', 'unknown')
            }
    
    def _generate_javascript_test(self, fix_analysis: Dict[str, Any]) -> str:
        """Generate Jest/Mocha test for JavaScript"""
        
        vuln_type = fix_analysis.get('vulnerability_type', 'Unknown')
        location = fix_analysis.get('location', 'unknown')
        function_name = self._extract_function_name(fix_analysis)
        analysis = fix_analysis.get('analysis', {})
        fix = fix_analysis.get('fix', {})
        
        # Extract route information if available
        route_path = self._extract_route_path(fix_analysis)
        http_method = self._extract_http_method(fix_analysis)
        
        test_content = f"""/**
 * Security Test: {vuln_type}
 * Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
 * Location: {location}
 * 
 * This test verifies that the security fix for {vuln_type} is working correctly.
 */

const request = require('supertest');
const app = require('../app'); // Adjust path as needed

describe('Security Test: {function_name} - {vuln_type}', () => {{
    let authToken;
    let testUser;
    let otherUser;
    
    beforeAll(async () => {{
        // Setup: Create test users
        testUser = await createTestUser({{
            email: 'test@example.com',
            password: 'Test123!'
        }});
        
        otherUser = await createTestUser({{
            email: 'other@example.com',
            password: 'Other123!'
        }});
        
        // Get auth token for testUser
        authToken = await getAuthToken(testUser);
    }});
    
    afterAll(async () => {{
        // Cleanup: Remove test users
        await deleteTestUser(testUser);
        await deleteTestUser(otherUser);
    }});
    
    describe('Positive Tests (Authorized Access)', () => {{
        test('should allow user to access their own resource', async () => {{
            const response = await request(app)
                .{http_method.lower()}('{route_path}/{{testUser.resourceId}}')
                .set('Authorization', `Bearer ${{authToken}}`)
                .expect(200);
            
            expect(response.body).toBeDefined();
            expect(response.body.userId).toBe(testUser.id);
        }});
        
        test('should return correct data for authorized user', async () => {{
            const response = await request(app)
                .{http_method.lower()}('{route_path}/{{testUser.resourceId}}')
                .set('Authorization', `Bearer ${{authToken}}`)
                .expect(200);
            
            expect(response.body).toHaveProperty('id');
            expect(response.body).toHaveProperty('userId');
            expect(response.body.userId).toBe(testUser.id);
        }});
    }});
    
    describe('Negative Tests (Unauthorized Access)', () => {{
        test('should deny access to another user\\'s resource', async () => {{
            const response = await request(app)
                .{http_method.lower()}('{route_path}/{{otherUser.resourceId}}')
                .set('Authorization', `Bearer ${{authToken}}`)
                .expect(403);
            
            expect(response.body).toHaveProperty('error');
            expect(response.body.error).toMatch(/permission|forbidden|access denied/i);
        }});
        
        test('should deny access without authentication', async () => {{
            const response = await request(app)
                .{http_method.lower()}('{route_path}/{{testUser.resourceId}}')
                .expect(401);
            
            expect(response.body).toHaveProperty('error');
            expect(response.body.error).toMatch(/unauthorized|authentication/i);
        }});
        
        test('should deny access with invalid token', async () => {{
            const response = await request(app)
                .{http_method.lower()}('{route_path}/{{testUser.resourceId}}')
                .set('Authorization', 'Bearer invalid-token')
                .expect(401);
            
            expect(response.body).toHaveProperty('error');
        }});
    }});
    
    describe('Edge Cases', () => {{
        test('should return 404 for non-existent resource', async () => {{
            const response = await request(app)
                .{http_method.lower()}('{route_path}/99999')
                .set('Authorization', `Bearer ${{authToken}}`)
                .expect(404);
            
            expect(response.body).toHaveProperty('error');
            expect(response.body.error).toMatch(/not found/i);
        }});
        
        test('should handle malformed resource ID', async () => {{
            const response = await request(app)
                .{http_method.lower()}('{route_path}/invalid-id')
                .set('Authorization', `Bearer ${{authToken}}`)
                .expect(400);
            
            expect(response.body).toHaveProperty('error');
        }});
        
        test('should prevent SQL injection attempts', async () => {{
            const response = await request(app)
                .{http_method.lower()}('{route_path}/1\\'OR\\'1\\'=\\'1')
                .set('Authorization', `Bearer ${{authToken}}`)
                .expect(400);
        }});
    }});
    
    describe('Security Logging', () => {{
        test('should log unauthorized access attempts', async () => {{
            // Clear logs
            clearSecurityLogs();
            
            // Attempt unauthorized access
            await request(app)
                .{http_method.lower()}('{route_path}/{{otherUser.resourceId}}')
                .set('Authorization', `Bearer ${{authToken}}`)
                .expect(403);
            
            // Check logs
            const logs = getSecurityLogs();
            expect(logs).toContainEqual(
                expect.objectContaining({{
                    event: 'unauthorized_access_attempt',
                    userId: testUser.id,
                    resourceId: otherUser.resourceId
                }})
            );
        }});
    }});
}});

// Helper functions (implement these based on your app)
async function createTestUser(userData) {{
    // TODO: Implement user creation
    throw new Error('createTestUser not implemented');
}}

async function deleteTestUser(user) {{
    // TODO: Implement user deletion
    throw new Error('deleteTestUser not implemented');
}}

async function getAuthToken(user) {{
    // TODO: Implement token generation
    throw new Error('getAuthToken not implemented');
}}

function clearSecurityLogs() {{
    // TODO: Implement log clearing
    throw new Error('clearSecurityLogs not implemented');
}}

function getSecurityLogs() {{
    // TODO: Implement log retrieval
    throw new Error('getSecurityLogs not implemented');
}}
"""
        
        return test_content
    
    def _generate_python_test(self, fix_analysis: Dict[str, Any]) -> str:
        """Generate PyTest test for Python"""
        
        vuln_type = fix_analysis.get('vulnerability_type', 'Unknown')
        location = fix_analysis.get('location', 'unknown')
        function_name = self._extract_function_name(fix_analysis)
        
        test_content = f"""\"\"\"
Security Test: {vuln_type}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Location: {location}

This test verifies that the security fix for {vuln_type} is working correctly.
\"\"\"

import pytest
from fastapi.testclient import TestClient
from app import app  # Adjust import as needed

client = TestClient(app)


@pytest.fixture
def test_user():
    \"\"\"Create a test user\"\"\"
    user = create_test_user(email="test@example.com", password="Test123!")
    yield user
    delete_test_user(user)


@pytest.fixture
def other_user():
    \"\"\"Create another test user\"\"\"
    user = create_test_user(email="other@example.com", password="Other123!")
    yield user
    delete_test_user(user)


@pytest.fixture
def auth_token(test_user):
    \"\"\"Get auth token for test user\"\"\"
    return get_auth_token(test_user)


class TestSecurity{self._capitalize(function_name)}:
    \"\"\"Security tests for {function_name}\"\"\"
    
    def test_authorized_access(self, test_user, auth_token):
        \"\"\"Test that user can access their own resource\"\"\"
        response = client.get(
            f"/api/resource/{{test_user.resource_id}}",
            headers={{"Authorization": f"Bearer {{auth_token}}"}}
        )
        
        assert response.status_code == 200
        assert response.json()["user_id"] == test_user.id
    
    def test_unauthorized_access_other_user(self, test_user, other_user, auth_token):
        \"\"\"Test that user cannot access another user's resource\"\"\"
        response = client.get(
            f"/api/resource/{{other_user.resource_id}}",
            headers={{"Authorization": f"Bearer {{auth_token}}"}}
        )
        
        assert response.status_code == 403
        assert "error" in response.json()
        assert "permission" in response.json()["error"].lower()
    
    def test_unauthorized_access_no_auth(self, test_user):
        \"\"\"Test that unauthenticated requests are denied\"\"\"
        response = client.get(f"/api/resource/{{test_user.resource_id}}")
        
        assert response.status_code == 401
        assert "error" in response.json()
    
    def test_unauthorized_access_invalid_token(self, test_user):
        \"\"\"Test that invalid tokens are rejected\"\"\"
        response = client.get(
            f"/api/resource/{{test_user.resource_id}}",
            headers={{"Authorization": "Bearer invalid-token"}}
        )
        
        assert response.status_code == 401
        assert "error" in response.json()
    
    def test_nonexistent_resource(self, auth_token):
        \"\"\"Test handling of non-existent resource\"\"\"
        response = client.get(
            "/api/resource/99999",
            headers={{"Authorization": f"Bearer {{auth_token}}"}}
        )
        
        assert response.status_code == 404
        assert "error" in response.json()
    
    def test_malformed_resource_id(self, auth_token):
        \"\"\"Test handling of malformed resource ID\"\"\"
        response = client.get(
            "/api/resource/invalid-id",
            headers={{"Authorization": f"Bearer {{auth_token}}"}}
        )
        
        assert response.status_code == 400
        assert "error" in response.json()
    
    def test_sql_injection_prevention(self, auth_token):
        \"\"\"Test SQL injection prevention\"\"\"
        response = client.get(
            "/api/resource/1'OR'1'='1",
            headers={{"Authorization": f"Bearer {{auth_token}}"}}
        )
        
        assert response.status_code in [400, 404]
    
    def test_security_logging(self, test_user, other_user, auth_token):
        \"\"\"Test that unauthorized access attempts are logged\"\"\"
        clear_security_logs()
        
        # Attempt unauthorized access
        client.get(
            f"/api/resource/{{other_user.resource_id}}",
            headers={{"Authorization": f"Bearer {{auth_token}}"}}
        )
        
        # Check logs
        logs = get_security_logs()
        assert any(
            log["event"] == "unauthorized_access_attempt" and
            log["user_id"] == test_user.id and
            log["resource_id"] == other_user.resource_id
            for log in logs
        )


# Helper functions (implement these based on your app)
def create_test_user(email, password):
    \"\"\"Create a test user\"\"\"
    raise NotImplementedError("create_test_user not implemented")


def delete_test_user(user):
    \"\"\"Delete a test user\"\"\"
    raise NotImplementedError("delete_test_user not implemented")


def get_auth_token(user):
    \"\"\"Get auth token for user\"\"\"
    raise NotImplementedError("get_auth_token not implemented")


def clear_security_logs():
    \"\"\"Clear security logs\"\"\"
    raise NotImplementedError("clear_security_logs not implemented")


def get_security_logs():
    \"\"\"Get security logs\"\"\"
    raise NotImplementedError("get_security_logs not implemented")
"""
        
        return test_content
    
    def _generate_java_test(self, fix_analysis: Dict[str, Any]) -> str:
        """Generate JUnit test for Java"""
        
        vuln_type = fix_analysis.get('vulnerability_type', 'Unknown')
        location = fix_analysis.get('location', 'unknown')
        function_name = self._extract_function_name(fix_analysis)
        class_name = self._capitalize(function_name)
        
        test_content = f"""/**
 * Security Test: {vuln_type}
 * Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
 * Location: {location}
 * 
 * This test verifies that the security fix for {vuln_type} is working correctly.
 */

package com.example.security;

import org.junit.jupiter.api.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
import static org.hamcrest.Matchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
public class Security{class_name}Test {{
    
    @Autowired
    private MockMvc mockMvc;
    
    private static String testUserToken;
    private static String otherUserToken;
    private static Long testUserId;
    private static Long otherUserId;
    
    @BeforeAll
    public static void setup() {{
        // Create test users
        testUserId = createTestUser("test@example.com", "Test123!");
        otherUserId = createTestUser("other@example.com", "Other123!");
        
        // Get auth tokens
        testUserToken = getAuthToken(testUserId);
        otherUserToken = getAuthToken(otherUserId);
    }}
    
    @AfterAll
    public static void cleanup() {{
        // Delete test users
        deleteTestUser(testUserId);
        deleteTestUser(otherUserId);
    }}
    
    @Test
    @Order(1)
    @DisplayName("Should allow user to access their own resource")
    public void testAuthorizedAccess() throws Exception {{
        mockMvc.perform(get("/api/resource/" + testUserId)
                .header("Authorization", "Bearer " + testUserToken)
                .contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.userId").value(testUserId));
    }}
    
    @Test
    @Order(2)
    @DisplayName("Should deny access to another user's resource")
    public void testUnauthorizedAccessOtherUser() throws Exception {{
        mockMvc.perform(get("/api/resource/" + otherUserId)
                .header("Authorization", "Bearer " + testUserToken)
                .contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().isForbidden())
                .andExpect(jsonPath("$.error", containsStringIgnoringCase("permission")));
    }}
    
    @Test
    @Order(3)
    @DisplayName("Should deny access without authentication")
    public void testUnauthorizedAccessNoAuth() throws Exception {{
        mockMvc.perform(get("/api/resource/" + testUserId)
                .contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.error").exists());
    }}
    
    @Test
    @Order(4)
    @DisplayName("Should deny access with invalid token")
    public void testUnauthorizedAccessInvalidToken() throws Exception {{
        mockMvc.perform(get("/api/resource/" + testUserId)
                .header("Authorization", "Bearer invalid-token")
                .contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().isUnauthorized());
    }}
    
    @Test
    @Order(5)
    @DisplayName("Should return 404 for non-existent resource")
    public void testNonexistentResource() throws Exception {{
        mockMvc.perform(get("/api/resource/99999")
                .header("Authorization", "Bearer " + testUserToken)
                .contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().isNotFound());
    }}
    
    @Test
    @Order(6)
    @DisplayName("Should handle malformed resource ID")
    public void testMalformedResourceId() throws Exception {{
        mockMvc.perform(get("/api/resource/invalid-id")
                .header("Authorization", "Bearer " + testUserToken)
                .contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().isBadRequest());
    }}
    
    @Test
    @Order(7)
    @DisplayName("Should prevent SQL injection")
    public void testSqlInjectionPrevention() throws Exception {{
        mockMvc.perform(get("/api/resource/1'OR'1'='1")
                .header("Authorization", "Bearer " + testUserToken)
                .contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().is4xxClientError());
    }}
    
    @Test
    @Order(8)
    @DisplayName("Should log unauthorized access attempts")
    public void testSecurityLogging() throws Exception {{
        clearSecurityLogs();
        
        // Attempt unauthorized access
        mockMvc.perform(get("/api/resource/" + otherUserId)
                .header("Authorization", "Bearer " + testUserToken)
                .contentType(MediaType.APPLICATION_JSON));
        
        // Verify log entry
        List<SecurityLog> logs = getSecurityLogs();
        assertTrue(logs.stream().anyMatch(log ->
            log.getEvent().equals("unauthorized_access_attempt") &&
            log.getUserId().equals(testUserId) &&
            log.getResourceId().equals(otherUserId)
        ));
    }}
    
    // Helper methods (implement these based on your app)
    private static Long createTestUser(String email, String password) {{
        throw new UnsupportedOperationException("createTestUser not implemented");
    }}
    
    private static void deleteTestUser(Long userId) {{
        throw new UnsupportedOperationException("deleteTestUser not implemented");
    }}
    
    private static String getAuthToken(Long userId) {{
        throw new UnsupportedOperationException("getAuthToken not implemented");
    }}
    
    private static void clearSecurityLogs() {{
        throw new UnsupportedOperationException("clearSecurityLogs not implemented");
    }}
    
    private static List<SecurityLog> getSecurityLogs() {{
        throw new UnsupportedOperationException("getSecurityLogs not implemented");
    }}
}}
"""
        
        return test_content
    
    def _generate_generic_test(self, fix_analysis: Dict[str, Any]) -> str:
        """Generate generic test template"""
        
        vuln_type = fix_analysis.get('vulnerability_type', 'Unknown')
        location = fix_analysis.get('location', 'unknown')
        
        return f"""# Security Test: {vuln_type}
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Location: {location}

Test Cases:

1. Positive Test: Authorized Access
   - User should be able to access their own resource
   - Response should be 200 OK
   - Data should belong to the authenticated user

2. Negative Test: Unauthorized Access (Other User)
   - User should NOT be able to access another user's resource
   - Response should be 403 Forbidden
   - Error message should indicate permission denied

3. Negative Test: No Authentication
   - Unauthenticated requests should be denied
   - Response should be 401 Unauthorized

4. Negative Test: Invalid Token
   - Invalid authentication tokens should be rejected
   - Response should be 401 Unauthorized

5. Edge Case: Non-existent Resource
   - Should return 404 Not Found
   - Should not leak information about other resources

6. Edge Case: Malformed Input
   - Should handle invalid resource IDs gracefully
   - Should return 400 Bad Request

7. Security: SQL Injection Prevention
   - Should reject SQL injection attempts
   - Should not execute malicious queries

8. Security: Logging
   - Should log unauthorized access attempts
   - Logs should include user ID and resource ID
"""
    
    def _generate_test_suite(self, generated_tests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate test suite file that runs all tests"""
        
        if not generated_tests:
            return {'success': False, 'error': 'No tests generated'}
        
        try:
            if self.test_framework in ['jest', 'mocha']:
                suite_content = self._generate_javascript_suite(generated_tests)
                suite_file = self.test_directory / "security.suite.test.js"
            elif self.test_framework in ['pytest', 'unittest']:
                suite_content = self._generate_python_suite(generated_tests)
                suite_file = self.test_directory / "test_security_suite.py"
            elif self.test_framework == 'junit':
                suite_content = self._generate_java_suite(generated_tests)
                suite_file = self.test_directory / "SecurityTestSuite.java"
            else:
                suite_content = self._generate_generic_suite(generated_tests)
                suite_file = self.test_directory / "security_suite.txt"
            
            suite_file.write_text(suite_content, encoding='utf-8')
            
            return {
                'success': True,
                'suite_file': str(suite_file)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_javascript_suite(self, generated_tests: List[Dict[str, Any]]) -> str:
        """Generate JavaScript test suite"""
        
        test_imports = '\n'.join([
            f"require('./{Path(t['test_file']).name}');"
            for t in generated_tests
        ])
        
        return f"""/**
 * Security Test Suite
 * Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
 * 
 * This suite runs all generated security tests.
 */

{test_imports}

describe('Security Test Suite', () => {{
    test('All security tests should be loaded', () => {{
        expect(true).toBe(true);
    }});
}});
"""
    
    def _generate_python_suite(self, generated_tests: List[Dict[str, Any]]) -> str:
        """Generate Python test suite"""
        
        return f"""\"\"\"
Security Test Suite
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This suite runs all generated security tests.
\"\"\"

import pytest

# All test files are automatically discovered by pytest
# Run with: pytest {self.test_directory}

def test_suite_loaded():
    \"\"\"Verify test suite is loaded\"\"\"
    assert True
"""
    
    def _generate_java_suite(self, generated_tests: List[Dict[str, Any]]) -> str:
        """Generate Java test suite"""
        
        test_classes = ',\n        '.join([
            f"{Path(t['test_file']).stem}.class"
            for t in generated_tests
        ])
        
        return f"""/**
 * Security Test Suite
 * Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
 */

package com.example.security;

import org.junit.platform.suite.api.SelectClasses;
import org.junit.platform.suite.api.Suite;

@Suite
@SelectClasses({{
        {test_classes}
}})
public class SecurityTestSuite {{
    // Test suite configuration
}}
"""
    
    def _generate_generic_suite(self, generated_tests: List[Dict[str, Any]]) -> str:
        """Generate generic test suite"""
        
        test_list = '\n'.join([
            f"- {t['test_file']}"
            for t in generated_tests
        ])
        
        return f"""Security Test Suite
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Generated Tests:
{test_list}

Run all tests with your testing framework.
"""
    
    def _extract_function_name(self, fix_analysis: Dict[str, Any]) -> str:
        """Extract function name from fix analysis"""
        
        # Try to get from evidence
        evidence = fix_analysis.get('evidence', {})
        if 'function_name' in evidence:
            return evidence['function_name']
        
        # Try to get from location
        location = fix_analysis.get('location', '')
        if 'function_name' in fix_analysis:
            return fix_analysis['function_name']
        
        # Try to extract from fixed code
        fixed_code = fix_analysis.get('fix', {}).get('fixed_code', '')
        match = re.search(r'function\s+(\w+)|const\s+(\w+)\s*=|def\s+(\w+)', fixed_code)
        if match:
            return match.group(1) or match.group(2) or match.group(3)
        
        return 'unknown_function'
    
    def _extract_route_path(self, fix_analysis: Dict[str, Any]) -> str:
        """Extract route path from fix analysis"""
        
        evidence = fix_analysis.get('evidence', {})
        if 'route_path' in evidence:
            return evidence['route_path']
        
        # Default
        return '/api/resource'
    
    def _extract_http_method(self, fix_analysis: Dict[str, Any]) -> str:
        """Extract HTTP method from fix analysis"""
        
        evidence = fix_analysis.get('evidence', {})
        if 'http_method' in evidence:
            return evidence['http_method']
        
        # Default
        return 'GET'
    
    def _sanitize_filename(self, name: str) -> str:
        """Sanitize string for use in filename"""
        return re.sub(r'[^a-zA-Z0-9_]', '_', name).lower()
    
    def _capitalize(self, name: str) -> str:
        """Capitalize string for class names"""
        return ''.join(word.capitalize() for word in name.split('_'))
    
    def _count_test_cases(self, test_content: str) -> int:
        """Count number of test cases in test content"""
        
        # Count test functions/methods
        patterns = [
            r'test\s*\(',  # Jest/Mocha: test(
            r'it\s*\(',    # Jest/Mocha: it(
            r'def\s+test_',  # PyTest: def test_
            r'@Test',      # JUnit: @Test
        ]
        
        count = 0
        for pattern in patterns:
            count += len(re.findall(pattern, test_content))
        
        return max(count, 1)  # At least 1


def generate_tests_from_results(
    codebase_path: str,
    llm_results: Dict[str, Any],
    applied_results: List[Dict[str, Any]],
    test_framework: str = "auto",
    test_directory: str = "tests/security"
) -> Dict[str, Any]:
    """
    Convenience function to generate tests from scan results
    
    Args:
        codebase_path: Path to codebase
        llm_results: Results from LLM analysis
        applied_results: Results from fix application
        test_framework: Testing framework (auto, jest, pytest, etc.)
        test_directory: Directory for generated tests
        
    Returns:
        Dictionary with test generation results
    """
    generator = TestGenerator(codebase_path, test_framework, test_directory)
    return generator.generate_tests(llm_results, applied_results)
