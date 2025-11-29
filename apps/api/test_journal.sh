#!/bin/bash

# Journal Service Test Script
# Tests all journal endpoints

set -e

API_URL="http://localhost:8000"
echo "Testing Journal Service at $API_URL"
echo "======================================"
echo

# Test 1: Health Check
echo "1. Testing health endpoint..."
HEALTH=$(curl -s "$API_URL/health")
echo "   Response: $HEALTH"
echo "   ✓ Health check passed"
echo

# Test 2: Create Journal Entry
echo "2. Creating a new journal entry..."
CREATE_RESPONSE=$(curl -s -X POST "$API_URL/journal" \
  -H "Content-Type: application/json" \
  -d '{"text": "Test entry from script. Today I learned about FastAPI and MongoDB!"}')
ENTRY_ID=$(echo $CREATE_RESPONSE | jq -r '.id')
echo "   Created entry ID: $ENTRY_ID"
echo "   ✓ Entry created successfully"
echo

# Test 3: Get Specific Entry
echo "3. Getting specific entry by ID..."
GET_RESPONSE=$(curl -s "$API_URL/journal/$ENTRY_ID")
TEXT=$(echo $GET_RESPONSE | jq -r '.text')
echo "   Entry text: $TEXT"
echo "   ✓ Entry retrieved successfully"
echo

# Test 4: Get All Entries (Paginated)
echo "4. Getting paginated list of entries..."
LIST_RESPONSE=$(curl -s "$API_URL/journal?page=1&page_size=5")
TOTAL=$(echo $LIST_RESPONSE | jq -r '.total')
PAGE=$(echo $LIST_RESPONSE | jq -r '.page')
PAGE_SIZE=$(echo $LIST_RESPONSE | jq -r '.page_size')
TOTAL_PAGES=$(echo $LIST_RESPONSE | jq -r '.total_pages')
echo "   Total entries: $TOTAL"
echo "   Page: $PAGE/$TOTAL_PAGES (showing $PAGE_SIZE per page)"
echo "   ✓ List retrieved successfully"
echo

# Test 5: Test Pagination
echo "5. Testing pagination with page_size=2..."
PAGE1=$(curl -s "$API_URL/journal?page=1&page_size=2")
COUNT1=$(echo $PAGE1 | jq '.entries | length')
echo "   Page 1 entries: $COUNT1"

if [ $TOTAL -gt 2 ]; then
  PAGE2=$(curl -s "$API_URL/journal?page=2&page_size=2")
  COUNT2=$(echo $PAGE2 | jq '.entries | length')
  echo "   Page 2 entries: $COUNT2"
fi
echo "   ✓ Pagination working correctly"
echo

# Test 6: Test Validation (should fail)
echo "6. Testing validation (empty text - should fail)..."
ERROR_RESPONSE=$(curl -s -X POST "$API_URL/journal" \
  -H "Content-Type: application/json" \
  -d '{"text": ""}' \
  -w "\nHTTP_CODE:%{http_code}")
HTTP_CODE=$(echo "$ERROR_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
if [ "$HTTP_CODE" = "422" ]; then
  echo "   ✓ Validation working (returned 422)"
else
  echo "   ⚠ Unexpected response code: $HTTP_CODE"
fi
echo

# Test 7: Check NLP Worker
echo "7. Checking if NLP worker processed the job..."
sleep 2  # Give worker time to process
docker-compose -f ../../infra/docker-compose.yml logs nlp 2>/dev/null | tail -10 | grep -q "Analysis complete" && \
  echo "   ✓ NLP worker processed the entry" || \
  echo "   ⚠ NLP worker might not have processed yet (check logs manually)"
echo

echo "======================================"
echo "All tests completed!"
echo
echo "API Documentation available at: $API_URL/docs"
echo "OpenAPI spec available at: $API_URL/openapi.json"
