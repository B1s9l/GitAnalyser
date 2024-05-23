# GitAnalyser
A script to analyse git repositories locally.

## Usage
1. Go to the location where you saved this tool `cd /path/to/tool/GitAnalyser`
2. Open the `config.txt` file and enter the local path name to the repository you want to analyse
3. Run the tool using `python script.py`
4. The results will be stored in `/path/to/tool/GitAnalyser/Results`

### Optional flags
- Use `python script.py --files` to see the overview of all files each user has edited.
- Use `python script.py --extended` to see the overview of all files each user has edited and a breakdown of the most recent change line-by-line.
(Using the `--extended` flag might cause longer waiting times depending on the size of the repository)
