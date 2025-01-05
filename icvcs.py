import os
import sys
import json
import shutil
import difflib
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

def load_config():
    config_path = os.path.join(ICVCS_DIR, 'icvcs_config.json')
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    else:
        return {
            "default_author": "Unknown",
            "default_version_description": "No description provided",
            "default_commit_message": "No commit message provided"
        }

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

    config = {
        "default_author": input("Enter default author: ") or "Unknown",
        "default_version_description": input("Enter a default version description: ") or "No description provided",
        "default_commit_message": input("Enter a default commit message: " or "No commit message provided")
    }

    with open(os.path.join(ICVCS_DIR, 'icvcs_config.json'), 'w') as config_file:
        json.dump(config, config_file, indent=4)

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
    config = load_config()

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
                repo_data["versions"].remove(version_name)

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
            "author": input("Enter version author: ") or config["default_author"],
            "description": input("Enter version description: ") or config["default_version_description"],
            "files": repo_data["files"]
        }

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
    config = load_config()

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
        "message": input("Enter commit message: ") or config["default_commit_message"],
        "author": input("Enter commit's author: ") or config["default_author"]
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
    print("  icvcs init <repo_name>                 - Initialize a new version control repository.")
    print("  icvcs add <path>                       - Add a file or directory to the repository.")
    print("  icvcs add <path> -wf                   - Add a directory and all its contents recursively.")
    print("  icvcs remove <path>                    - Remove a file or directory from the repository.")
    print("  icvcs version create <version>         - Create a new version.")
    print("  icvcs version create <version> --force - Overwrite existing version with force.")
    print("  icvcs version delete <version>         - Delete an existing version.")
    print("  icvcs version list                     - List all versions.")
    print("  icvcs commit                           - Create a new commit.")
    print("  icvcs commit remove <commit_id>        - Remove a specific commit.")
    print("  icvcs commit clear                     - Clear all commits except the 'latest' commit.")
    print("  icvcs commit list                      - List all commits.")
    print("  icvcs commit history                   - Display the commit history.")
    print("  icvcs push                             - Push the latest commit to 'latest'.")
    print("  icvcs push <commit_id>                 - Push a specific commit to 'latest'.")
    print("  icvcs status                           - Shows the repo's status.")
    print("  icvcs config show                      - Show the current icvcs config.")
    print("  icvcs config author                    - Change the dafault author.")
    print("  icvcs config version_description       - Change the dafault version description.")
    print("  icvcs config commit_message            - Change the default commit message.")
    print("  icvcs compare <version1> <version2>    - Compare two versions.")
    print("  icvcs help                             - Display this help message.")

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
            print(f"- {commit_id}: {metadata.get('message', 'No message')} (Author: {metadata.get('author', 'Unknown')}) id: {metadata.get('commit_id')}")
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

def status():
    repo_data = load_repo_data()
    tracked_files = set(repo_data.get("files", []))
    working_directory_files = set()

    latest_commit_path = os.path.join(ICVCS_DIR, "commits", "latest")

    for root, _, files in os.walk('.'):
        if ICVCS_DIR in root:
            continue
        for file in files:
            working_directory_files.add(os.path.relpath(os.path.join(root, file)))

    untracked_files = {
        file for file in working_directory_files - tracked_files if not file.startswith(ICVCS_DIR)
    }
    modified_files = []
    deleted_files = []

    for file in tracked_files:
        file_path = os.path.join(latest_commit_path, file)
        if not os.path.exists(file):
            deleted_files.append(file)
        elif not os.path.exists(file_path):
            modified_files.append(file)
        else:
            with open(file, 'rb') as current_file:
                current_content = current_file.read()
            with open(file_path, 'rb') as commit_file:
                commit_content = commit_file.read()
            if current_content != commit_content:
                modified_files.append(file)

    staged_files = tracked_files.intersection(working_directory_files) - set(modified_files) - set(deleted_files)

    print(f"Repository: {repo_data['repo_name']}")
    print(f"Tracked Files: {len(tracked_files)}")
    print(f"Total Versions: {len(repo_data['versions'])}")
    print(f"Last Commit: {get_last_commit_info()}")

    print("\nUntracked Files:")
    if not untracked_files:
        print("No untracked files")
    else:
        for file in untracked_files:
            print(f"  {file}")

    print("\nModified Files:")
    if not modified_files:
        print("No modified files.")
    else:
        for file in modified_files:
            print(f"  {file}")

    print("\nDeleted Files:")
    if not deleted_files:
        print("No deleted files.")
    else:
        for file in deleted_files:
            print(f"  {file}")

    print("\nStaged Files:")
    if not staged_files:
        print("No staged files.")
    else:
        for file in staged_files:
            print(f"  {file}")

def get_last_commit_info():
    commit_history_path = os.path.join(ICVCS_DIR, "commit_history.json")
    if not os.path.exists(commit_history_path):
        return "No commits yet."
    with open(commit_history_path, 'r') as history_file:
        commit_history = json.load(history_file)
    if not commit_history:
        return "No commits yet."
    last_commit = commit_history[-1]
    return f"ID: {last_commit['commit_id']}, Author: {last_commit['author']}, Message: {last_commit['message']}, Timestamp: {last_commit['timestamp']}"

def update_icvcs_config(config_key, new_value):
    config_file = 'icvcs_config.json'
    
    if not os.path.exists(config_file):
        print("Config file does not exist.")
        return
    
    with open(config_file, 'r') as file:
        config_data = json.load(file)
    
    config_data[config_key] = new_value
    
    with open(config_file, 'w') as file:
        json.dump(config_data, file, indent=4)
    
    print(f"{config_key} updated successfully.")

def change_author():
    new_author = input("Enter the new default author: ")
    update_icvcs_config('author', new_author)

def change_commit_message():
    new_commit_message = input("Enter the new default commit message: ")
    update_icvcs_config('commit_message', new_commit_message)

def change_version_description():
    new_version_description = input("Enter the new default version description: ")
    update_icvcs_config('version_description', new_version_description)


def load_version_files(version_id):
    version_path = f".icvcs/versions/{version_id}/metadata.json"
    try:
        with open(version_path, "r") as f:
            version_data = json.load(f)
        
        if isinstance(version_data, list):
            return [entry["files"] for entry in version_data]
        
        return version_data["files"]
    except FileNotFoundError:
        print(f"Version {version_id} does not exist.")
        return None
    except KeyError:
        print(f"Invalid format in version file: {version_path}")
        return None

def load_file_content(version_id, file_path):
    file_version_path = f".icvcs/versions/{version_id}/{file_path}"
    try:
        with open(file_version_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return None

def compare_versions(version1, version2):
    files1 = load_version_files(version1)
    files2 = load_version_files(version2)
    print(files1, files2)
    
    if files1 is None or files2 is None:
        return
    
    print(f"Comparing versions {version1} and {version2}...\n")
    
    all_files = set(files1).union(files2)
    for file in sorted(all_files):

        content1 = load_file_content(version1, file) or ""
        content2 = load_file_content(version2, file) or ""

        if content1 != content2:
            print(f"Changes in file: {file}")
            show_diff(content1, content2)
            print("-" * 40)
        else:
            print(f"No changes in file: {file}")

def show_diff(content1, content2):
    diff = difflib.unified_diff(
        content1.splitlines(), content2.splitlines(),
        lineterm='', fromfile="Version 1", tofile="Version 2"
    )
    for line in diff:
        print(line)



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
    elif command == 'status':
        status()
    elif command == 'config':
        if len(sys.argv) < 3:
            print("Provide a setting to change (author, version_description, commit_message) or 'show' to show the current config")
        else:
            arg = sys.argv[2]
            if arg == 'author':
                change_author()
            elif arg == "version_description":
                change_version_description()
            elif arg == "commit_message":
                change_commit_message()
            elif arg == "show":
                config = load_config()
                for key, value in config.items():
                    print(f"{key.replace('_', ' ').capitalize()}: {value}")
            else:
                print("Invalid default setting.")
    elif command == 'compare':
        compare_versions(sys.argv[2], sys.argv[3])
    else:
        print(f"Unknown command: {command}")
        print("Run 'icvcs help' to see available commands.")


if __name__ == '__main__':
    main()

