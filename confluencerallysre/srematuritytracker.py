import pandas as pd
import requests
import json
import os
import sys
from io import StringIO
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()

# -- Rally Config --
RALLY_API_KEY = os.getenv("RALLY_API_KEY")
RALLY_URL = "https://rally1.rallydev.com/slm/webservice/v2.0"
RALLY_WORKSPACE_OID = os.getenv("RALLY_WORKSPACE_OID")

# -- Confluence Config --
CONFLUENCE_URL = os.getenv("CONFLUENCE_URL")
CONFLUENCE_USER = os.getenv("CONFLUENCE_USER")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")
CONFLUENCE_PAGE_ID = os.getenv("CONFLUENCE_PAGE_ID")

# --- File Paths ---
FLOWS_FILE = 'flows.csv'
CONFLUENCE_EXPORT_FILE = 'confluence_export.csv'

# --- Maturity Model ---
MATURITY_MODEL = {
    "Monitoring": {
        1: "Basic host-level monitoring (CPU, Mem). Manual log checking.",
        2: "Application-level metrics (e.g., request rate, error rate). Centralized logging.",
        3: "SLO-based alerting. Distributed tracing implemented.",
        4: "Proactive alerting on SLO burn rate. Automated anomaly detection.",
        5: "Predictive analytics for potential issues. Self-healing capabilities."
    },
    "Incident Response": {
        1: "Ad-hoc, informal response. No on-call rotation.",
        2: "Defined on-call rotation. Basic incident communication plan.",
        3: "Formal Incident Commander role. Blameless postmortems are standard practice.",
        4: "Automated incident runbooks. ChatOps integration for incident management.",
        5: "Automated incident resolution for common issues."
    },
    "Post-Mortem and Root Cause Analysis": {
        1: "No formal process. Blame is common.",
        2: "Informal postmortems for major incidents.",
        3: "Blameless postmortems for all customer-impacting incidents. Action items are tracked.",
        4: "Postmortem action items are prioritized in backlogs. Trends are analyzed.",
        5: "Automated generation of postmortem timelines and data."
    },
    "Testing and Release Procedures": {
        1: "Manual testing and deployments.",
        2: "Automated unit and integration tests in CI.",
        3: "Automated deployments (e.g., Blue/Green, Canary).",
        4: "Automated rollback procedures based on health checks.",
        5: "Chaos engineering practices are part of the release cycle."
    },
    "Capacity Planning": {
        1: "Reactive scaling based on outages.",
        2: "Manual capacity planning based on historical trends.",
        3: "Automated load testing as part of the release cycle.",
        4: "Proactive capacity forecasting based on business projections.",
        5: "Automated, predictive scaling of resources."
    },
    "Development and Product": {
        1: "SRE is an afterthought; involved only during outages.",
        2: "SRE provides operational requirements to development teams.",
        3: "SRE consults on design and architecture for new features.",
        4: "Reliability is a key feature; SREs and Devs collaborate on SLOs.",
        5: "SRE principles are embedded in the entire product development lifecycle."
    }
}


def fetch_confluence_table_api():
    """Fetches the first table from a Confluence page using the REST API."""
    print(f"Fetching table via API from Confluence page ID: {CONFLUENCE_PAGE_ID}...")
    url = f"{CONFLUENCE_URL}/rest/api/content/{CONFLUENCE_PAGE_ID}?expand=body.storage"
    auth = (CONFLUENCE_USER, CONFLUENCE_API_TOKEN)
    try:
        response = requests.get(url, auth=auth)
        response.raise_for_status()
        page_html = response.json()['body']['storage']['value']
        tables = pd.read_html(StringIO(page_html))
        if tables:
            print("Successfully fetched and parsed Confluence table via API.")
            return tables[0]
        else:
            print("Warning: No tables found on the Confluence page.")
            return pd.DataFrame()
    except Exception as e:
        print(f"Error fetching/parsing Confluence page via API: {e}")
        return None

def update_confluence_page_api(df_to_sync):
    """Updates the table on a Confluence page via the REST API."""
    print("Preparing to update Confluence page via API...")
    url = f"{CONFLUENCE_URL}/rest/api/content/{CONFLUENCE_PAGE_ID}?expand=body.storage,version"
    auth = (CONFLUENCE_USER, CONFLUENCE_API_TOKEN)

    try:
        # 1. Get current page content and version
        get_response = requests.get(url, auth=auth)
        get_response.raise_for_status()
        page_data = get_response.json()
        page_html = page_data['body']['storage']['value']
        current_version = page_data['version']['number']
        
        # 2. Convert DataFrame to HTML table
        # Create a copy to avoid modifying the original DataFrame
        df_for_html = df_to_sync.copy()
        # Create clickable links for Rally cards
        df_for_html['Rally Card'] = df_for_html['Rally Card'].apply(
            lambda x: f'<a href="https://rally1.rallydev.com/#/detail/userstory/{x}">{x}</a>' if pd.notna(x) and str(x).strip() != '' else ''
        )
        new_table_html = df_for_html.to_html(index=False, escape=False, border=1)

        # 3. Replace old table with new table in the page HTML
        soup = BeautifulSoup(page_html, 'lxml')
        table_tag = soup.find('table')
        if not table_tag:
            print("Error: No table found on the Confluence page to replace.")
            return
        
        table_tag.replace_with(BeautifulSoup(new_table_html, 'lxml'))
        updated_html_content = str(soup)

        # 4. Prepare the payload for the PUT request
        payload = {
            "version": {"number": current_version + 1},
            "title": page_data['title'],
            "type": "page",
            "body": {
                "storage": {
                    "value": updated_html_content,
                    "representation": "storage"
                }
            }
        }

        # 5. Send the PUT request
        update_url = f"{CONFLUENCE_URL}/rest/api/content/{CONFLUENCE_PAGE_ID}"
        put_response = requests.put(update_url, auth=auth, json=payload)
        put_response.raise_for_status()
        print("✅ Successfully updated the Confluence page via API!")

    except requests.exceptions.RequestException as e:
        print(f"Error updating Confluence page: {e}")
        if e.response:
            print(f"Response body: {e.response.text}")
    except Exception as e:
        print(f"An unexpected error occurred during Confluence update: {e}")


def load_data(use_api=True):
    """Loads data from Confluence (API or CSV) and Rally."""
    print("--- Loading Data ---")
    if use_api:
        confluence_df = fetch_confluence_table_api()
        if confluence_df is None or confluence_df.empty:
            print("Could not load data from Confluence API. Aborting.")
            return None
    else:
        try:
            confluence_df = pd.read_csv(CONFLUENCE_FILE)
            print("Loaded data from local confluence_export.csv")
        except FileNotFoundError:
            print(f"Error: {CONFLUENCE_FILE} not found. Please run the setup or provide the file.")
            return None
    
    # Standardize column names for consistency
    confluence_df.columns = [col.replace(' ', '_').lower() for col in confluence_df.columns]
    
    return confluence_df

def sync_with_rally(df):
    """Syncs the DataFrame with the latest data from Rally."""
    print("\n--- Syncing with Rally ---")
    rally_tags = df['tags'].dropna().unique().tolist()
    
    print(f"Querying Rally for stories with tags: {rally_tags}")
    
    # For simplicity, we'll fetch all stories with any of the relevant tags
    # A more advanced query could be constructed based on your specific needs
    if not rally_tags:
        print("No tags found in Confluence data to query Rally.")
        return df

    headers = {
        "zsessionid": RALLY_API_KEY,
        "Content-Type": "application/json"
    }
    
    tag_query_parts = [f'(Tags.Name = "{tag}")' for tag in rally_tags]
    query = f'({" OR ".join(tag_query_parts)})'
    
    params = {
        "query": query,
        "workspace": f"/workspace/{RALLY_WORKSPACE_OID}",
        "fetch": "FormattedID,Name,ScheduleState",
        "pagesize": 200
    }

    try:
        response = requests.get(f"{RALLY_URL}/hierarchicalrequirement", headers=headers, params=params)
        response.raise_for_status()
        data = response.json()['QueryResult']['Results']
        
        if not data:
            print("No matching stories found in Rally.")
            return df

        rally_updates = {item['FormattedID']: item['ScheduleState'] for item in data}
        print(f"Found {len(rally_updates)} stories in Rally. Applying updates...")

        # Update status in the main dataframe
        df['status'] = df.apply(
            lambda row: rally_updates.get(row['rally_card'], row['status']),
            axis=1
        )
        print("Sync complete.")
        return df

    except requests.exceptions.RequestException as e:
        print(f"Error fetching Rally data: {e}")
        return df


def generate_reports(df):
    """Generates all output files."""
    print("\n--- Generating Reports ---")
    
    # 1. Rally Import CSV
    rally_import_df = df[df['rally_card'].isnull() | (df['rally_card'] == ' ')]
    if not rally_import_df.empty:
        rally_output = rally_import_df[['task', 'description', 'flow', 'asset_name']].copy()
        rally_output.rename(columns={'task': 'Name', 'description': 'Description'}, inplace=True)
        rally_output['Project'] = "Your Rally Project Name" # IMPORTANT: Set this
        rally_output['Tags'] = rally_import_df.apply(
            lambda row: f"sre, flow_{row['flow'].replace(' ', '_')}, asset_{row['asset_name'].replace(' ', '_')}", 
            axis=1
        )
        rally_output[['Name', 'Description', 'Project', 'Tags']].to_csv('rally_import.csv', index=False)
        print("✅ 'rally_import.csv' created for new stories.")
    else:
        print("ℹ️ No new stories require creation in Rally.")

    # 2. Confluence To-Do List (Wiki Markup)
    with open('confluence_todo_list.txt', 'w') as f:
        f.write("h1. SRE Action & To-Do List\n\n")
        for owner, group in df.groupby('owner'):
            f.write(f"h2. To-Do for: {owner}\n")
            f.write("||Priority||Task||Status||Rally Card||\n")
            for _, row in group.iterrows():
                rally_card_str = str(row['rally_card']).replace('.0', '')
                rally_link = f"[{rally_card_str}|https://rally1.rallydev.com/#/detail/userstory/{rally_card_str}]" if pd.notna(row['rally_card']) and rally_card_str.strip() != '' else " "
                f.write(f"|{row['priority']}|{row['task']}|{row['status']}|{rally_link}|\n")
            f.write("\n")
    print("✅ 'confluence_todo_list.txt' created.")

    # 3. Confluence Upload CSV
    report_df = df.copy()
    report_df['Rally Card Link'] = report_df['rally_card'].apply(
        lambda x: f"https://rally1.rallydev.com/#/detail/userstory/{x}" if pd.notna(x) and str(x).strip() != '' else ''
    )
    report_df.to_csv('confluence_upload.csv', index=False)
    print("✅ 'confluence_upload.csv' created for manual import into Confluence.")


def main():
    """Main application CLI."""
    print("--- SRE Maturity Tracker ---")
    
    df = load_data()
    if df is None:
        print("Failed to load initial data. Exiting.")
        return

    while True:
        print("\n--- Main Menu ---")
        print("1. Sync with Rally (Fetch latest statuses)")
        print("2. Generate Reports (Rally Import, Confluence Uploads)")
        print("3. Sync Statuses to Confluence (API Update)")
        print("4. Exit")
        choice = input("> ")

        if choice == '1':
            df = sync_with_rally(df)
        elif choice == '2':
            generate_reports(df)
        elif choice == '3':
            update_confluence_table(df)
        elif choice == '4':
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()
