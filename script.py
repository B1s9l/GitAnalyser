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
parser.add_argument('--files', action='store_true', help='Include files changed without line content')
parser.add_argument('--exclude-hash', type=str, help='Exclude this commit hash from user statistics and attribute it separately')
parser.add_argument('--exclude-before-hash', type=str, help='Exclude all commits before this commit hash')
args = parser.parse_args()

# Construct git log command
if args.exclude_before_hash:
    git_range = f"{args.exclude_before_hash}..HEAD"
else:
    git_range = "HEAD"

git_log_cmd = [
    "git", "log", git_range, "--pretty=format:'%h,%an'", "--numstat"
]

# Run the git log command
result = subprocess.run(git_log_cmd, capture_output=True, text=True)
log_output = result.stdout.strip()

# Parse the output
user_file_stats = defaultdict(lambda: defaultdict(int))
file_changes = defaultdict(lambda: defaultdict(list))
initial_commit_lines = defaultdict(int)
initial_commit_user = None

current_user = None
current_commit_hash = None
lines = log_output.split('\n')

for i, line in enumerate(lines):
    if line.startswith("'"):
        parts = line.strip("'").split(',')
        if len(parts) == 2:
            current_commit_hash = parts[0]
            current_user = parts[1]
    elif current_user:
        parts = line.split('\t')
        if len(parts) == 3:
            added, deleted, filename = parts
            if added.isdigit():
                added = int(added)
                if current_commit_hash == args.exclude_hash:
                    initial_commit_lines[filename] += added
                    initial_commit_user = current_user
                else:
                    user_file_stats[current_user][filename] += added
                    if args.extended:
                        commit_line_idx = i - 1
                        commit_hash = lines[commit_line_idx].split(',')[0].strip("'")
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
breakline = "#############################################\n"

# Write results to the output file
with open(output_file, 'w') as f:
    f.write(breakline)
    f.write("Overall lines added by file type:\n")
    f.write(breakline)
    for file_type, total_lines in sorted_overall_file_stats.items():
        f.write(f'{file_type}: {total_lines} lines added\n')
        file_types[file_type] = total_lines
        all_totals += total_lines
    f.write("\n")
    f.write(f'Total lines: {all_totals}\n')
    f.write(breakline)
    f.write("\n\n")

    # Write initialization commit stats
    if args.exclude_hash and initial_commit_user:
        f.write(breakline)
        f.write(f"Initialization done by {initial_commit_user} (excluded from stats):\n")
        f.write(breakline)
        categorized_stats = categorize_by_file_type(initial_commit_lines)
        for file_type, total_lines in categorized_stats.items():
            f.write(f"  {file_type}: {total_lines} lines added\n")
        total_init_lines = sum(initial_commit_lines.values())
        f.write(f"\n  Total lines: {total_init_lines}\n")
        f.write(breakline)
        f.write("\n\n")

    for user, files in user_file_stats.items():
        user_totals = 0
        f.write(breakline)
        f.write(f"{user}\n")
        f.write(breakline)
        f.write("Lines added by file type:\n")
        categorized_stats = categorize_by_file_type(files)
        for file_type, total_lines in categorized_stats.items():
            percentage = round((100 / file_types[file_type]) * total_lines, 2) if file_types[file_type] else 0
            f.write(f"  {file_type}: {total_lines} lines added. Thats {percentage}%\n")
            user_totals += total_lines
        f.write("\n")
        percentage = round((100 / all_totals) * user_totals, 2) if all_totals else 0
        f.write(f'  Total lines: {user_totals}. Thats {percentage}%\n')

        if args.files or args.extended:
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
        f.write(breakline)
        f.write("\n\n")

print(f"Results written to {output_file}")
