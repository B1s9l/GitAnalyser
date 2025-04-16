# GitAnalyser
A script to analyse git repositories locally.

## Usage
1. Go to the location where you saved this tool `cd /path/to/tool/GitAnalyser`
2. Open the `config.txt` file and enter the local path name to the repository you want to analyse
3. Run the tool using `python script.py` to see an overview of added lines by user by **file type**.
4. The results will be stored in `/path/to/tool/GitAnalyser/Results`

### Optional flags
- Use `python script.py --files` to see an overview of added lines by user **by file**.
- Use `python script.py --extended` to see an overview of added lines by user **by file** and a breakdown of the **most recent change line-by-line**.
(Using the `--extended` flag might cause longer waiting times depending on the size of the repository)
- Use `python script.py  --exclude-hash [commit hash]` to see an overview of added lines by user by **file type excluding a certain commit**.
- Use `python script.py --exclude-before-hash [commit hash]` to see an overview of added lines by user **by file type after a certain commit**.
Chain flags together:
- Use `python script.py --files --exclude-before-hash [commit hash]` to see an overview of added lines by user **by file after a certain commit**.
