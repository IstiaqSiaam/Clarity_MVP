#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Base URL
BASE_URL="http://localhost:8000"

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function to print test results
print_test_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ $2${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ $2${NC}"
        ((TESTS_FAILED++))
    fi
}

# Generate random email to avoid conflicts
RANDOM_ID=$RANDOM
TEST_EMAIL="testuser${RANDOM_ID}@example.com"
TEST_NAME="Test User ${RANDOM_ID}"
TEST_PASSWORD="password123"

echo -e "${YELLOW}=== Testing Updated Authentication System ===${NC}\n"

# Test 1: User Signup (no tokens in response)
echo "Test 1: User Signup (should return user info only, no tokens)"
SIGNUP_RESPONSE=$(curl -s -X POST "${BASE_URL}/auth/signup" \
    -H "Content-Type: application/json" \
    -d "{
        \"name\": \"${TEST_NAME}\",
        \"email\": \"${TEST_EMAIL}\",
        \"password\": \"${TEST_PASSWORD}\",
        \"type\": \"individual\"
    }")

USER_ID=$(echo $SIGNUP_RESPONSE | jq -r '.user.id')
USER_NAME=$(echo $SIGNUP_RESPONSE | jq -r '.user.name')
USER_TYPE=$(echo $SIGNUP_RESPONSE | jq -r '.user.type')
SIGNUP_MESSAGE=$(echo $SIGNUP_RESPONSE | jq -r '.message')
SIGNUP_HAS_TOKENS=$(echo $SIGNUP_RESPONSE | jq 'has("access_token")')

if [ "$USER_ID" != "null" ] && [ "$USER_ID" != "" ] && [ "$SIGNUP_HAS_TOKENS" == "false" ]; then
    print_test_result 0 "Signup successful - ID: $USER_ID, Name: $USER_NAME, Type: $USER_TYPE"
    echo "   Message: $SIGNUP_MESSAGE"
else
    print_test_result 1 "Signup failed or incorrectly returned tokens"
    echo "   Response: $SIGNUP_RESPONSE"
fi
echo ""

# Test 2: User Login (should return tokens)
echo "Test 2: User Login (should return access and refresh tokens)"
LOGIN_RESPONSE=$(curl -s -X POST "${BASE_URL}/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"${TEST_EMAIL}\", \"password\": \"${TEST_PASSWORD}\"}")

ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
REFRESH_TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.refresh_token')

if [ "$ACCESS_TOKEN" != "null" ] && [ "$ACCESS_TOKEN" != "" ]; then
    print_test_result 0 "Login successful - Got access and refresh tokens"
else
    print_test_result 1 "Login failed"
    echo "   Response: $LOGIN_RESPONSE"
fi
echo ""

# Test 3: Get Current User with valid token
echo "Test 3: Get Current User (/auth/me)"
ME_RESPONSE=$(curl -s -X GET "${BASE_URL}/auth/me" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}")

ME_EMAIL=$(echo $ME_RESPONSE | jq -r '.email')
ME_NAME=$(echo $ME_RESPONSE | jq -r '.name')
ME_TYPE=$(echo $ME_RESPONSE | jq -r '.type')

if [ "$ME_EMAIL" == "$TEST_EMAIL" ] && [ "$ME_NAME" == "$TEST_NAME" ] && [ "$ME_TYPE" == "individual" ]; then
    print_test_result 0 "Get current user successful - Name: $ME_NAME, Type: $ME_TYPE"
else
    print_test_result 1 "Get current user failed"
    echo "   Response: $ME_RESPONSE"
fi
echo ""

# Test 4: Token Refresh
echo "Test 4: Token Refresh"
REFRESH_RESPONSE=$(curl -s -X POST "${BASE_URL}/auth/refresh" \
    -H "Content-Type: application/json" \
    -d "{\"refresh_token\": \"${REFRESH_TOKEN}\"}")

NEW_ACCESS_TOKEN=$(echo $REFRESH_RESPONSE | jq -r '.access_token')

if [ "$NEW_ACCESS_TOKEN" != "null" ] && [ "$NEW_ACCESS_TOKEN" != "" ]; then
    print_test_result 0 "Token refresh successful - Got new access token"
    ACCESS_TOKEN=$NEW_ACCESS_TOKEN  # Update token for subsequent tests
else
    print_test_result 1 "Token refresh failed"
    echo "   Response: $REFRESH_RESPONSE"
fi
echo ""

# Test 5: Create Authenticated Journal Entry
echo "Test 5: Create Authenticated Journal Entry"
JOURNAL_RESPONSE=$(curl -s -X POST "${BASE_URL}/journal" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -d '{"text": "This is an authenticated journal entry from the updated test script!"}')

ENTRY_ID=$(echo $JOURNAL_RESPONSE | jq -r '.id')
ENTRY_USER_ID=$(echo $JOURNAL_RESPONSE | jq -r '.user_id')

if [ "$ENTRY_ID" != "null" ] && [ "$ENTRY_ID" != "" ]; then
    print_test_result 0 "Authenticated journal entry created - ID: $ENTRY_ID, User: $ENTRY_USER_ID"
else
    print_test_result 1 "Failed to create journal entry"
    echo "   Response: $JOURNAL_RESPONSE"
fi
echo ""

# Test 6: Get Journal Entries (Authenticated)
echo "Test 6: Get Journal Entries (Authenticated)"
JOURNAL_LIST=$(curl -s "${BASE_URL}/journal" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}")

TOTAL=$(echo $JOURNAL_LIST | jq -r '.total')

if [ "$TOTAL" != "null" ] && [ "$TOTAL" != "" ]; then
    print_test_result 0 "Journal list retrieved - Total entries: $TOTAL"
else
    print_test_result 1 "Failed to get journal list"
fi
echo ""

# Test 7: Unauthorized Access
echo "Test 7: Unauthorized Access (should fail with 403)"
UNAUTH_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" "${BASE_URL}/journal")
UNAUTH_CODE=$(echo "$UNAUTH_RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)

if [ "$UNAUTH_CODE" == "403" ]; then
    print_test_result 0 "Unauthorized access correctly rejected (HTTP 403)"
else
    print_test_result 1 "Unauthorized access test failed - Expected 403, got $UNAUTH_CODE"
fi
echo ""

# Test 8: Wrong Password
echo "Test 8: Wrong Password (should fail with 401)"
WRONG_PW_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "${BASE_URL}/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"${TEST_EMAIL}\", \"password\": \"wrongpassword\"}")

WRONG_PW_CODE=$(echo "$WRONG_PW_RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)

if [ "$WRONG_PW_CODE" == "401" ]; then
    print_test_result 0 "Wrong password correctly rejected (HTTP 401)"
else
    print_test_result 1 "Wrong password test failed - Expected 401, got $WRONG_PW_CODE"
fi
echo ""

# Test 9: Duplicate Email
echo "Test 9: Duplicate Email Signup (should fail with 400)"
DUP_EMAIL_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "${BASE_URL}/auth/signup" \
    -H "Content-Type: application/json" \
    -d "{
        \"name\": \"Another User\",
        \"email\": \"${TEST_EMAIL}\",
        \"password\": \"${TEST_PASSWORD}\",
        \"type\": \"therapist\"
    }")

DUP_EMAIL_CODE=$(echo "$DUP_EMAIL_RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)

if [ "$DUP_EMAIL_CODE" == "400" ]; then
    print_test_result 0 "Duplicate email correctly rejected (HTTP 400)"
else
    print_test_result 1 "Duplicate email test failed - Expected 400, got $DUP_EMAIL_CODE"
fi
echo ""

# Test 10: Signup with different user types
echo "Test 10: Test different user types (therapist)"
THERAPIST_EMAIL="therapist${RANDOM_ID}@example.com"
THERAPIST_RESPONSE=$(curl -s -X POST "${BASE_URL}/auth/signup" \
    -H "Content-Type: application/json" \
    -d "{
        \"name\": \"Dr. Therapist\",
        \"email\": \"${THERAPIST_EMAIL}\",
        \"password\": \"${TEST_PASSWORD}\",
        \"type\": \"therapist\"
    }")

THERAPIST_TYPE=$(echo $THERAPIST_RESPONSE | jq -r '.user.type')

if [ "$THERAPIST_TYPE" == "therapist" ]; then
    print_test_result 0 "Therapist account created successfully with type: $THERAPIST_TYPE"
else
    print_test_result 1 "Failed to create therapist account"
    echo "   Response: $THERAPIST_RESPONSE"
fi
echo ""

# Summary
echo -e "${YELLOW}=== Test Summary ===${NC}"
echo -e "${GREEN}Tests Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Tests Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed.${NC}"
    exit 1
fi
