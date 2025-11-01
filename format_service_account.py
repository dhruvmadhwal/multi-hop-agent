"""
Helper script to format Google service account JSON for Streamlit secrets.

This script takes a service account JSON file and formats it properly
for use in Streamlit Cloud secrets (TOML format).

Usage:
    python format_service_account.py path/to/service-account.json
"""

import json
import sys
from pathlib import Path


def format_json_for_toml(json_file_path):
    """
    Read a service account JSON file and format it for TOML secrets.
    
    Args:
        json_file_path: Path to the service account JSON file
        
    Returns:
        Formatted string ready to paste into Streamlit secrets
    """
    try:
        # Read the JSON file
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        
        # Convert to single-line JSON string (compact format)
        json_string = json.dumps(data, separators=(',', ':'))
        
        # Create the TOML format output
        output = []
        output.append("[google]")
        output.append(f"service_account_json = '{json_string}'")
        output.append(f'project_id = "{data.get("project_id", "your-project-id")}"')
        output.append('location = "us-central1"')
        output.append("")
        output.append("[llm]")
        output.append('model = "gemini-2.5-flash"')
        
        return "\n".join(output)
        
    except FileNotFoundError:
        return f"Error: File '{json_file_path}' not found."
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON file - {e}"
    except Exception as e:
        return f"Error: {e}"


def main():
    """Main function to run the formatter."""
    print("=" * 70)
    print("Google Service Account JSON → Streamlit Secrets Formatter")
    print("=" * 70)
    print()
    
    if len(sys.argv) < 2:
        print("Usage: python format_service_account.py <path-to-service-account.json>")
        print()
        print("Example:")
        print("  python format_service_account.py service-account.json")
        print()
        sys.exit(1)
    
    json_file = sys.argv[1]
    
    if not Path(json_file).exists():
        print(f"❌ Error: File '{json_file}' not found.")
        print()
        print("Make sure the file path is correct and try again.")
        sys.exit(1)
    
    print(f"📄 Reading: {json_file}")
    print()
    
    formatted_output = format_json_for_toml(json_file)
    
    if formatted_output.startswith("Error:"):
        print(f"❌ {formatted_output}")
        sys.exit(1)
    
    print("✅ Successfully formatted!")
    print()
    print("=" * 70)
    print("Copy the following to your Streamlit Cloud secrets:")
    print("=" * 70)
    print()
    print(formatted_output)
    print()
    print("=" * 70)
    print()
    print("Instructions:")
    print("1. Go to your Streamlit Cloud app")
    print("2. Click on 'Settings' → 'Secrets'")
    print("3. Paste the above content into the secrets editor")
    print("4. Click 'Save'")
    print()
    
    # Optionally save to file
    output_file = "streamlit_secrets_formatted.txt"
    try:
        with open(output_file, 'w') as f:
            f.write(formatted_output)
        print(f"💾 Output also saved to: {output_file}")
        print()
    except Exception as e:
        print(f"⚠️  Could not save to file: {e}")
        print()


if __name__ == "__main__":
    main()

