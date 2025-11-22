import json
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from github import Github

app = Flask(__name__)
CORS(app) # Allows Flutter/Postman to connect easily

# Env Vars
GITHUB_PAT = os.environ.get('GITHUB_PAT')
REPO_NAME = os.environ.get('REPO_NAME') 

def parse_date(date_str):
    """Safely parses date, defaults to TODAY if invalid."""
    if not date_str:
        return datetime.now()
    try:
        # Try standard format YYYY-MM-DD
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        try:
            # Try DD-MM-YYYY just in case
            return datetime.strptime(date_str, '%d-%m-%Y')
        except ValueError:
            print(f"Warning: Invalid date format '{date_str}'. Using today's date.")
            return datetime.now()

@app.route('/add_summary', methods=['POST'])
def add_summary():
    try:
        # 1. Robust JSON Retrieval
        # force=True ignores missing Content-Type header
        # silent=True returns None instead of crashing on bad JSON
        req = request.get_json(force=True, silent=True)
        
        if req is None:
            return jsonify({"success": False, "error": "Invalid JSON. Please check quotes and commas."}), 400

        # 2. Connect to GitHub
        if not GITHUB_PAT or not REPO_NAME:
            return jsonify({"success": False, "error": "Server Config Error: Missing GitHub Keys"}), 500

        g = Github(GITHUB_PAT)
        repo = g.get_repo(REPO_NAME)
        file = repo.get_contents("study.json")
        
        # 3. Smart Date Handling
        dt = parse_date(req.get('date'))
        
        # 4. Prepare New Entry
        new_entry = {
            "date": dt.strftime('%Y-%m-%d'),       # Standard ISO format
            "date_display": dt.strftime('%B %d, %Y'), # Pretty format (e.g. November 20, 2025)
            "speaker": req.get('speaker', 'Unknown Speaker').strip(),
            "portion": req.get('portion', 'Unknown Portion').strip(),
            "title": req.get('title', 'Untitled').strip(),
            "summary": req.get('summary', '').strip(),
            "members": req.get('members', 'N/A').strip()
        }

        # 5. Append & Save
        current_data = json.loads(file.decoded_content.decode())
        current_data.append(new_entry)
        
        repo.update_file(
            path=file.path,
            message=f"Add summary {new_entry['date']}",
            content=json.dumps(current_data, indent=4),
            sha=file.sha,
            branch="main"
        )
        
        return jsonify({"success": True, "message": "Saved to GitHub"}), 200

    except Exception as e:
        print(f"SERVER ERROR: {e}") # Prints exact error to Render logs
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/', methods=['GET'])
def health_check():
    return "MACE EU Backend Active", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))