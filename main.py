import json
import os
from flask import Flask, request, jsonify
from datetime import datetime
from github import Github

app = Flask(__name__)

# Env Vars: Set these in Render
GITHUB_PAT = os.environ.get('GITHUB_PAT')
REPO_NAME = os.environ.get('REPO_NAME') 

@app.route('/add_summary', methods=['POST'])
def add_summary():
    try:
        # 1. Get Data from Flutter
        req = request.get_json()
        
        # 2. Connect to GitHub Repo
        g = Github(GITHUB_PAT)
        repo = g.get_repo(REPO_NAME)
        file = repo.get_contents("study.json")
        
        # 3. Get current content & Append new entry
        data = json.loads(file.decoded_content.decode())
        
        new_entry = {
            "date": req.get('date', datetime.now().strftime('%Y-%m-%d')),
            "date_display": datetime.now().strftime('%B %d, %Y'), # Or format req['date']
            "speaker": req.get('speaker', ''),
            "portion": req.get('portion', ''),
            "title": req.get('title', ''),
            "summary": req.get('summary', ''),
            "members": req.get('members', 'N/A')
        }
        data.append(new_entry)
        
        # 4. Update file on GitHub (This is the only way to make it permanent on Render)
        repo.update_file(
            path=file.path,
            message=f"Add summary {new_entry['date']}",
            content=json.dumps(data, indent=4),
            sha=file.sha,
            branch="main"
        )
        
        return jsonify({"success": True, "message": "Saved to GitHub"}), 200

    except Exception as e:
        # This prints the ACTUAL error to your terminal window
        print(f"ERROR OCCURRED: {e}") 
        return jsonify({"success": False, "error": str(e)}), 500
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))