import os
import sys
import json
import shutil
from datetime import datetime

ICVCS_DIR = '.icvcs'
COMMITS_DIR = os.path.join(ICVCS_DIR, 'commits')
LATEST_DIR = os.path.join(COMMITS_DIR, 'latest')
VERSIONS_DIR = os.path.join(ICVCS_DIR, 'versions')


def load_repo_data():
    icvcs_path = os.path.join(ICVCS_DIR, 'repo_data.json')
    if not os.path.exists(icvcs_path):
        print("No repository found. Please run 'icvcs init <repo_name>' first.")
        sys.exit(1)
    with open(icvcs_path, 'r') as f:
        return json.load(f)


def save_repo_data(repo_data):
    icvcs_path = os.path.join(ICVCS_DIR, 'repo_data.json')
    with open(icvcs_path, 'w') as f:
        json.dump(repo_data, f, indent=4)
    print("Repository data updated successfully.")


def init(repo_name):
    if os.path.exists(ICVCS_DIR):
        print(f"Repository '{repo_name}' already initialized.")
        return

    os.makedirs(ICVCS_DIR)
    os.makedirs(VERSIONS_DIR)
    os.makedirs(COMMITS_DIR)
    os.makedirs(LATEST_DIR)

    repo_data = {
        "repo_name": repo_name,
        "files": [],
        "directories": {},
        "versions": []
    }

    save_repo_data(repo_data)

    commit_history_path = os.path.join(ICVCS_DIR, "commit_history.json")
    with open(commit_history_path, 'w') as history_file:
        json.dump([], history_file)

    print(f"Repository '{repo_name}' initialized successfully.")


def add(path, with_files=False):
    repo_data = load_repo_data()

    if os.path.isfile(path):
        if path not in repo_data["files"]:
            repo_data["files"].append(path)
            print(f"File '{path}' added to the repository.")
        else:
            print(f"File '{path}' is already tracked.")
    elif os.path.isdir(path):
        if path not in repo_data["directories"]:
            repo_data["directories"][path] = []
            print(f"Directory '{path}' added to the repository.")

        if with_files:
            for root, _, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if file_path not in repo_data["directories"][path]:
                        repo_data["directories"][path].append(file_path)
            print(f"Directory '{path}' and its contents added to the repository.")
    else:
        print(f"Path '{path}' does not exist.")

    save_repo_data(repo_data)


def remove(path):
    repo_data = load_repo_data()

    if os.path.isfile(path):
        if path in repo_data["files"]:
            repo_data["files"].remove(path)
            print(f"File '{path}' removed from the repository.")
        else:
            print(f"File '{path}' is not tracked.")
    elif os.path.isdir(path):
        if path in repo_data["directories"]:
            del repo_data["directories"][path]
            print(f"Directory '{path}' removed from the repository.")
        else:
            print(f"Directory '{path}' is not tracked.")
    else:
        print(f"Path '{path}' does not exist in the repository.")

    save_repo_data(repo_data)


def version(command, version_name=None, force=False):
    repo_data = load_repo_data()

    if command == 'create':
        if not version_name:
            print("Version name is required for 'create'.")
            return

        version_path = os.path.join(VERSIONS_DIR, version_name)
        version_metadata_path = os.path.join(version_path, "metadata.json")

        if os.path.exists(version_path):
            if not force:
                print(f"Version '{version_name}' already exists.")
                return
            else:
                print(f"Version '{version_name}' exists but will be overwritten due to --force.")
                shutil.rmtree(version_path) 
        
        save_repo_data(repo_data)

        os.makedirs(version_path)
        for file in repo_data["files"]:
            if os.path.exists(file):
                shutil.copy(file, version_path)

        for directory, _ in repo_data["directories"].items():
            if os.path.exists(directory):
                shutil.copytree(directory, os.path.join(version_path, os.path.basename(directory)))

        metadata = {
            "version_name": version_name,
            "created_at": datetime.now().isoformat(),
            "author": input("Enter version author: ") or "Unknown",
            "description": input("Enter version description: ") or "No description provided",
        }

        # Save metadata to metadata.json in the version directory
        with open(version_metadata_path, 'w') as metadata_file:
            json.dump(metadata, metadata_file, indent=4)

        repo_data["versions"].append(version_name)
        save_repo_data(repo_data)
        print(f"Version '{version_name}' created successfully.")

    elif command == 'delete':
        if not version_name:
            print("Version name is required for 'delete'.")
            return

        version_path = os.path.join(VERSIONS_DIR, version_name)
        if os.path.exists(version_path):
            shutil.rmtree(version_path)
            repo_data["versions"].remove(version_name)
            save_repo_data(repo_data)
            print(f"Version '{version_name}' deleted successfully.")
        else:
            print(f"Version '{version_name}' does not exist.")
    else:
        print(f"Unknown version command: {command}")
        print("Use 'create' or 'delete'.")


def commit():
    repo_data = load_repo_data()

    commit_id = datetime.now().strftime('%Y%m%d%H%M%S')
    commit_dir = os.path.join(COMMITS_DIR, commit_id)
    os.makedirs(commit_dir)

    for file in repo_data["files"]:
        if os.path.exists(file):
            shutil.copy(file, commit_dir)
        else:
            print(f"Warning: Tracked file '{file}' does not exist.")

    for directory, _ in repo_data["directories"].items():
        if os.path.exists(directory):
            dest_dir = os.path.join(commit_dir, os.path.basename(directory))
            shutil.copytree(directory, dest_dir)
        else:
            print(f"Warning: Tracked directory '{directory}' does not exist.")

    metadata = {
        "commit_id": commit_id,
        "timestamp": datetime.now().isoformat(),
        "message": input("Enter commit message: ") or "No message",
        "author": input("Enter commit's author: ") or "Unknown"
    }
    metadata_path = os.path.join(commit_dir, "metadata.json")
    with open(metadata_path, 'w') as metadata_file:
        json.dump(metadata, metadata_file, indent=4)

    commit_history_path = os.path.join(ICVCS_DIR, "commit_history.json")
    with open(commit_history_path, 'r') as history_file:
        commit_history = json.load(history_file)

    commit_history.append(metadata)

    with open(commit_history_path, 'w') as history_file:
        json.dump(commit_history, history_file, indent=4)

    print(f"Commit '{commit_id}' created successfully.")


def remove_commit(commit_id):
    commit_dir = os.path.join(COMMITS_DIR, commit_id)
    if os.path.exists(commit_dir):
        shutil.rmtree(commit_dir)
        print(f"Commit '{commit_id}' removed successfully.")
    else:
        print(f"Commit '{commit_id}' does not exist.")


def push(commit_id=None):
    if not os.listdir(COMMITS_DIR):
        print("No commits to push.")
        return

    if commit_id:
        commit_dir = os.path.join(COMMITS_DIR, commit_id)
        if not os.path.exists(commit_dir):
            print(f"Commit '{commit_id}' does not exist.")
            return
    else:
        commits = sorted(os.listdir(COMMITS_DIR))
        if 'latest' in commits:
            commits.remove('latest')
        if not commits:
            print("No commits to push.")
            return
        commit_id = commits[-1]
        commit_dir = os.path.join(COMMITS_DIR, commit_id)

    if os.path.exists(LATEST_DIR):
        shutil.rmtree(LATEST_DIR)
    os.makedirs(LATEST_DIR)

    for item in os.listdir(commit_dir):
        src_path = os.path.join(commit_dir, item)
        dest_path = os.path.join(LATEST_DIR, item)
        if os.path.isdir(src_path):
            shutil.copytree(src_path, dest_path)
        else:
            shutil.copy(src_path, dest_path)

    print(f"Commit '{commit_id}' pushed to 'latest'.")


def clear_commits():
    for commit_id in os.listdir(COMMITS_DIR):
        if commit_id != 'latest':
            commit_dir = os.path.join(COMMITS_DIR, commit_id)
            if os.path.exists(commit_dir):
                shutil.rmtree(commit_dir)
    print("All commits cleared except the 'latest' commit.")


def help_command():
    print("Usage:")
    print("  icvcs init <repo_name>           - Initialize a new version control repository.")
    print("  icvcs add <path>                 - Add a file or directory to the repository.")
    print("  icvcs add <path> -wf             - Add a directory and all its contents recursively.")
    print("  icvcs remove <path>              - Remove a file or directory from the repository.")
    print("  icvcs version create <version>   - Create a new version.")
    print("  icvcs version delete <version>   - Delete an existing version.")
    print("  icvcs version create <version> --force - Overwrite existing version with force.")
    print("  icvcs commit                     - Create a new commit.")
    print("  icvcs commit remove <commit_id>  - Remove a specific commit.")
    print("  icvcs commit clear               - Clear all commits except the 'latest' commit.")
    print("  icvcs push                       - Push the latest commit to 'latest'.")
    print("  icvcs push <commit_id>           - Push a specific commit to 'latest'.")
    print("  icvcs help                       - Display this help message.")

def list_commits():
    if not os.path.exists(COMMITS_DIR):
        print("No commits directory found.")
        return

    commits = sorted(os.listdir(COMMITS_DIR))
    if not commits:
        print("No commits found.")
        return

    print("Commits:")
    for commit_id in commits:
        metadata_path = os.path.join(COMMITS_DIR, commit_id, "metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            print(f"- {commit_id}: {metadata.get('message', 'No message')} (Author: {metadata.get('author', 'Unknown')})")
        else:
            print(f"- {commit_id}: No metadata available.")


def list_versions():
    repo_data = load_repo_data()
    versions = repo_data.get("versions", [])
    if not versions:
        print("No versions found.")
        return

    print("Versions:")
    for version_name in versions:
        version_path = os.path.join(VERSIONS_DIR, version_name)
        metadata_path = os.path.join(version_path, "metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            print(f"- {version_name}: {metadata.get('description', 'No description')} (Created on: {metadata.get('created_at', 'Unknown')} by {metadata.get('author', 'Unknown')})")
        else:
            print(f"- {version_name}: No metadata available.")


def list_commit_history():
    commit_history_path = os.path.join(ICVCS_DIR, "commit_history.json")

    if not os.path.exists(commit_history_path):
        print("No commit history found.")
        return

    with open(commit_history_path, 'r') as history_file:
        commit_history = json.load(history_file)

    if not commit_history:
        print("No commits found in the history.")
        return

    print("Commit History:")
    for entry in commit_history:
        print(f"- Commit ID: {entry['commit_id']}")
        print(f"  Author: {entry['author']}")
        print(f"  Timestamp: {entry['timestamp']}")
        print(f"  Message: {entry['message']}")
        print()



def main():
    if len(sys.argv) < 2:
        print("Invalid command. Run 'icvcs help' to see available commands.")
        return

    command = sys.argv[1]

    if command == 'init':
        if len(sys.argv) < 3:
            print("Repository name is required.")
            return
        repo_name = sys.argv[2]
        init(repo_name)
    elif command == 'add':
        if len(sys.argv) < 3:
            print("Path to add is required.")
            return
        path = sys.argv[2]
        with_files = '-wf' in sys.argv
        add(path, with_files)
    elif command == 'remove':
        if len(sys.argv) < 3:
            print("Path to remove is required.")
            return
        path = sys.argv[2]
        remove(path)
    elif command == 'version':
        if sys.argv[2] == 'list':
            list_versions()
        elif len(sys.argv) < 4:
            print("Version command ('create' or 'delete') and version name are required.")
            return
        else:
            version(sys.argv[2], sys.argv[3], '--force' in sys.argv)
    elif command == 'commit':
        if len(sys.argv) > 2:
            if sys.argv[2] == 'remove':
                if len(sys.argv) < 4:
                    print("Commit ID is required for 'remove'.")
                    return
                remove_commit(sys.argv[3])
            elif sys.argv[2] == 'clear':
                clear_commits()
            elif sys.argv[2] == 'list':
                list_commits()
            elif sys.argv[2] == 'history':
                list_commit_history()
            else:
                commit()
        else:
            commit()
    elif command == 'push':
        if len(sys.argv) < 3:
            push()
        else:
            push(sys.argv[2])
    elif command == 'help':
        help_command()
    else:
        print(f"Unknown command: {command}")
        print("Run 'icvcs help' to see available commands.")


if __name__ == '__main__':
    main()

