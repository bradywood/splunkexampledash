#!/bin/bash

# ==============================================================================
# Rally Ticket Fetcher
#
# Description:
# This script fetches all User Stories and Defects associated with a specific
# Rally Feature ID. It requires the Rally API Key, Epic ID (for context),
# Feature ID, and Workspace OID to be passed as arguments.
#
# Prerequisites:
# - curl: A command-line tool for transferring data with URLs.
# - jq: A lightweight and flexible command-line JSON processor.
#   (Install on macOS: brew install jq)
#   (Install on Debian/Ubuntu: sudo apt-get install jq)
#
# Usage:
# ./rally_fetcher.sh "<RALLY_API_KEY>" "<EPIC_ID>" "<FEATURE_ID>" "<WORKSPACE_OID>"
#
# Example:
# ./rally_fetcher.sh "_abc123..." "E123" "F456" "9876543210"
#
# ==============================================================================

# --- Configuration ---
# Assign command-line arguments to variables for clarity.
if [ "$#" -ne 4 ]; then
    echo "Usage: $0 \"<RALLY_API_KEY>\" \"<EPIC_ID>\" \"<FEATURE_ID>\" \"<WORKSPACE_OID>\""
    exit 1
fi

RALLY_API_KEY="$1"
EPIC_ID="$2"
FEATURE_ID="$3"
WORKSPACE_OID="$4"

# Your Rally instance URL.
RALLY_URL="https://rally1.rallydev.com"

# --- Helper Functions ---

# Function to perform the curl request with common settings.
# Arguments: $1: API endpoint path, $2: Rally query string
function rally_curl() {
    local endpoint="$1"
    local query="$2"

    curl -s -G "${RALLY_URL}/slm/webservice/v2.0/${endpoint}" \
    --header "Authorization: Bearer ${RALLY_API_KEY}" \
    --header "Content-Type: application/json" \
    --data-urlencode "query=${query}" \
    --data-urlencode "workspace=${RALLY_URL}/slm/webservice/v2.0/workspace/${WORKSPACE_OID}" \
    --data-urlencode "fetch=FormattedID,Name,State,Owner" \
    --data-urlencode "pagesize=200"
}

# Function to fetch User Stories for a given Feature ID.
function get_stories_for_feature() {
    local feature_id="$1"
    echo "------------------------------------------------------------"
    echo "🔎 Fetching User Stories for Feature: ${feature_id}"
    echo "------------------------------------------------------------"

    # Query for User Stories (HierarchicalRequirement) whose parent PortfolioItem is the specified Feature.
    local query_string="(PortfolioItem.FormattedID = \"${feature_id}\")"
    local response=$(rally_curl "hierarchicalrequirement" "${query_string}")

    # Check if the query was successful and print results using jq.
    if [[ $(echo "$response" | jq -r '.QueryResult.TotalResultCount') -gt 0 ]]; then
        echo "$response" | jq -r '.QueryResult.Results[] | "  - \(.FormattedID): \(.Name) (\(.State.Name // "No State"))"'
    else
        echo "  - No User Stories found for this Feature."
        # Optional: Print the full error response for debugging.
        # echo "$response" | jq
    fi
    echo "" # Newline for spacing
}

# Function to fetch Defects for a given Feature ID.
function get_defects_for_feature() {
    local feature_id="$1"
    echo "------------------------------------------------------------"
    echo "🐞 Fetching Defects for Feature: ${feature_id}"
    echo "------------------------------------------------------------"

    # Query for Defects whose parent PortfolioItem is the specified Feature.
    local query_string="(PortfolioItem.FormattedID = \"${feature_id}\")"
    local response=$(rally_curl "defect" "${query_string}")

    # Check if the query was successful and print results using jq.
    if [[ $(echo "$response" | jq -r '.QueryResult.TotalResultCount') -gt 0 ]]; then
        echo "$response" | jq -r '.QueryResult.Results[] | "  - \(.FormattedID): \(.Name) (\(.State // "No State"))"'
    else
        echo "  - No Defects found for this Feature."
    fi
    echo "" # Newline for spacing
}


# --- Main Execution ---

echo "============================================================"
echo "Rally Ticket Fetcher"
echo "============================================================"
echo "Epic Context: ${EPIC_ID}"
echo ""

# Fetch all tickets associated with the specified Feature.
get_stories_for_feature "${FEATURE_ID}"
get_defects_for_feature "${FEATURE_ID}"

echo "✅ Done."
