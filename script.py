import os
import subprocess
from collections import defaultdict
import argparse

# Read the repository path from the config file
config_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.txt")
repo_dir = None

with open(config_file_path, 'r') as config_file:
    for line in config_file:
        line = line.strip()
        if line and not line.startswith('#'):
            repo_dir = line
            break

if not repo_dir:
    raise ValueError("Repository path not found in config.txt")

# Extract the repository name from the directory path
repo_name = os.path.basename(repo_dir)

# Change to the repository directory
os.chdir(repo_dir)

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Generate git statistics.')
parser.add_argument('--extended', action='store_true', help='Include content of changed lines')
args = parser.parse_args()

# Command to get the git log with author and file changes
git_log_cmd = [
    "git", "log", "--pretty=format:'%h,%an'", "--numstat"
]

# Run the git log command
result = subprocess.run(git_log_cmd, capture_output=True, text=True)
log_output = result.stdout.strip()

# Parse the output
user_file_stats = defaultdict(lambda: defaultdict(int))
file_changes = defaultdict(lambda: defaultdict(list))
current_user = None

for line in log_output.split('\n'):
    if line.startswith("'"):
        parts = line.strip("'").split(',')
        if len(parts) == 2:
            current_user = parts[1]
    elif current_user:
        parts = line.split('\t')
        if len(parts) == 3:
            added, deleted, filename = parts
            if added.isdigit():
                user_file_stats[current_user][filename] += int(added)
                if args.extended:
                    # Get the diff for each commit
                    commit_hash = log_output.split('\n')[log_output.split('\n').index(line)-1].split(',')[0].strip("'")
                    diff_cmd = ["git", "show", commit_hash]
                    diff_result = subprocess.run(diff_cmd, capture_output=True, text=True)
                    diff_output = diff_result.stdout.strip()
                    added_lines = []
                    deleted_lines = []
                    for diff_line in diff_output.split('\n'):
                        if diff_line.startswith('+') and not diff_line.startswith('+++'):
                            added_lines.append(diff_line[1:])
                        elif diff_line.startswith('-') and not diff_line.startswith('---'):
                            deleted_lines.append(diff_line[1:])
                    file_changes[filename]['added'] = added_lines
                    file_changes[filename]['deleted'] = deleted_lines

# Function to categorize lines by file type
def categorize_by_file_type(file_stats):
    lines_by_type = defaultdict(int)
    for filename, lines in file_stats.items():
        # Extract file type and sanitize it
        file_type = filename.split('.')[-1].strip('} ')
        lines_by_type[file_type] += lines
    
    sorted_lines_by_type = dict(sorted(lines_by_type.items()))
    return sorted_lines_by_type

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Create the "Results" directory if it doesn't exist
results_dir = os.path.join(script_dir, "Results")
os.makedirs(results_dir, exist_ok=True)

# Construct the output file path
output_file = os.path.join(results_dir, f"analysis_{repo_name}.txt")

# Collect overall file type statistics
overall_file_stats = defaultdict(int)
for files in user_file_stats.values():
    categorized_stats = categorize_by_file_type(files)
    for file_type, total_lines in categorized_stats.items():
        overall_file_stats[file_type] += total_lines

# Sort overall file type statistics
sorted_overall_file_stats = dict(sorted(overall_file_stats.items()))

file_types = {}
all_totals = 0
# Write results to the output file
with open(output_file, 'w') as f:
    f.write("################################################################################################################################\n")
    f.write("Overall lines added by file type:\n")
    f.write("################################################################################################################################\n\n")
    for file_type, total_lines in sorted_overall_file_stats.items():
        f.write(f'{file_type}: {total_lines} lines added\n')
        file_types[file_type] = total_lines
        all_totals += total_lines
    f.write("\n")
    f.write(f'Total lines: {all_totals}\n')
    f.write("\n")
    f.write("################################################################################################################################\n")
    f.write("################################################################################################################################\n")
    f.write("################################################################################################################################\n\n")
    f.write("\n")

    user_totals = 0
    for user, files in user_file_stats.items():
        f.write(f"########################### {user} ###########################\n")
        f.write("Lines added by file type:\n")
        categorized_stats = categorize_by_file_type(files)
        for file_type, total_lines in categorized_stats.items():
            percentage = round((100 / file_types[file_type]) * total_lines, 2)
            f.write(f"  {file_type}: {total_lines} lines added. Thats {percentage}%\n")
            user_totals += total_lines
        f.write("\n")
        percentage = round((100/all_totals)*user_totals)
        f.write(f'  Total lines: {user_totals}. Thats {percentage}%\n')
        f.write("\n")
        
        f.write("Files changed:\n")
        for filename, lines in files.items():
            f.write(f"  {filename}: {lines} lines added\n")
            if args.extended and filename in file_changes:
                f.write(f"    + Added lines:\n")
                for added_line in file_changes[filename]['added']:
                    f.write(f"      + {added_line}\n")
                f.write(f"    - Deleted lines:\n")
                for deleted_line in file_changes[filename]['deleted']:
                    f.write(f"      - {deleted_line}\n")
        f.write("\n")
        f.write("################################################################################################################################\n")
        f.write("################################################################################################################################\n")
        f.write("################################################################################################################################\n\n")

print(f"Results written to {output_file}")
