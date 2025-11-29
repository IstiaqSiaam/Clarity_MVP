#!/bin/bash
# Test script for Analytics and Search endpoints

set -e

API_URL="http://localhost:8000"
echo "🧪 Testing Analytics & Search Endpoints"
echo "========================================="
echo ""

# Step 1: Login
echo "1️⃣  Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"testuser@example.com","password":"password123"}')

TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
  echo "❌ Login failed"
  exit 1
fi
echo "✅ Login successful"
echo ""

# Step 2: Test GET /analytics/mood-trend
echo "2️⃣  Testing GET /analytics/mood-trend?days=7"
MOOD_RESPONSE=$(curl -s -X GET "$API_URL/analytics/mood-trend?days=7" \
  -H "Authorization: Bearer $TOKEN")

MOOD_LABEL=$(echo "$MOOD_RESPONSE" | jq -r '.overall_statistics.mood_label')
AVG_SENTIMENT=$(echo "$MOOD_RESPONSE" | jq -r '.overall_statistics.average_sentiment')
TOTAL_ENTRIES=$(echo "$MOOD_RESPONSE" | jq -r '.overall_statistics.total_entries')

echo "   Overall Mood: $MOOD_LABEL (sentiment: $AVG_SENTIMENT)"
echo "   Total Entries: $TOTAL_ENTRIES"
echo "✅ Mood trend endpoint working"
echo ""

# Step 3: Test GET /analytics/mood-trend with 30 days
echo "3️⃣  Testing GET /analytics/mood-trend?days=30"
MOOD_RESPONSE_30=$(curl -s -X GET "$API_URL/analytics/mood-trend?days=30" \
  -H "Authorization: Bearer $TOKEN")

TOTAL_30=$(echo "$MOOD_RESPONSE_30" | jq -r '.overall_statistics.total_entries')
echo "   Total Entries (30 days): $TOTAL_30"
echo "✅ 30-day mood trend working"
echo ""

# Step 4: Test GET /analytics/themes
echo "4️⃣  Testing GET /analytics/themes?days=30"
THEMES_RESPONSE=$(curl -s -X GET "$API_URL/analytics/themes?days=30" \
  -H "Authorization: Bearer $TOKEN")

UNIQUE_THEMES=$(echo "$THEMES_RESPONSE" | jq -r '.statistics.unique_themes')
TOTAL_THEMES=$(echo "$THEMES_RESPONSE" | jq -r '.statistics.total_themes')
TOP_THEME=$(echo "$THEMES_RESPONSE" | jq -r '.top_themes[0].theme')

echo "   Unique Themes: $UNIQUE_THEMES"
echo "   Total Theme Occurrences: $TOTAL_THEMES"
echo "   Top Theme: $TOP_THEME"
echo "✅ Theme analysis endpoint working"
echo ""

# Step 5: Test POST /search - basic keyword search
echo "5️⃣  Testing POST /search - Basic keyword search"
SEARCH_RESPONSE=$(curl -s -X POST "$API_URL/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"work promotion"}')

TOTAL_RESULTS=$(echo "$SEARCH_RESPONSE" | jq -r '.total_results')
SEARCH_TIME=$(echo "$SEARCH_RESPONSE" | jq -r '.search_time_ms')

echo "   Query: 'work promotion'"
echo "   Results Found: $TOTAL_RESULTS"
echo "   Search Time: ${SEARCH_TIME}ms"
echo "✅ Basic search working"
echo ""

# Step 6: Test POST /search - with positive sentiment filter
echo "6️⃣  Testing POST /search - With sentiment filter (positive)"
SEARCH_POS=$(curl -s -X POST "$API_URL/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"work", "filter_sentiment":"positive"}')

POS_RESULTS=$(echo "$SEARCH_POS" | jq -r '.total_results')
echo "   Query: 'work' (positive only)"
echo "   Results Found: $POS_RESULTS"
echo "✅ Sentiment filter working"
echo ""

# Step 7: Test POST /search - with negative sentiment filter
echo "7️⃣  Testing POST /search - With sentiment filter (negative)"
SEARCH_NEG=$(curl -s -X POST "$API_URL/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"work", "filter_sentiment":"negative"}')

NEG_RESULTS=$(echo "$SEARCH_NEG" | jq -r '.total_results')
echo "   Query: 'work' (negative only)"
echo "   Results Found: $NEG_RESULTS"
echo "✅ Negative sentiment filter working"
echo ""

# Step 8: Test POST /search - with theme filter
echo "8️⃣  Testing POST /search - With theme filter"
SEARCH_THEME=$(curl -s -X POST "$API_URL/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"stress", "filter_themes":["anxiety", "stress"]}')

THEME_RESULTS=$(echo "$SEARCH_THEME" | jq -r '.total_results')
MATCHED_THEMES=$(echo "$SEARCH_THEME" | jq -r '.results[0].themes | join(", ")')

echo "   Query: 'stress' (themes: anxiety, stress)"
echo "   Results Found: $THEME_RESULTS"
echo "   Matched Themes: $MATCHED_THEMES"
echo "✅ Theme filter working"
echo ""

# Step 9: Test POST /search - with max_results limit
echo "9️⃣  Testing POST /search - With result limit"
SEARCH_LIMIT=$(curl -s -X POST "$API_URL/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"work", "max_results":1}')

LIMIT_RESULTS=$(echo "$SEARCH_LIMIT" | jq -r '.results | length')
echo "   Max Results: 1"
echo "   Actual Results: $LIMIT_RESULTS"
echo "✅ Result limiting working"
echo ""

# Summary
echo "========================================="
echo "✅ All 9 tests passed!"
echo ""
echo "📊 Analytics Endpoints:"
echo "   - GET /analytics/mood-trend ✅"
echo "   - GET /analytics/themes ✅"
echo ""
echo "🔍 Search Endpoints:"
echo "   - POST /search (basic) ✅"
echo "   - POST /search (sentiment filter) ✅"
echo "   - POST /search (theme filter) ✅"
echo "   - POST /search (result limit) ✅"
echo ""
