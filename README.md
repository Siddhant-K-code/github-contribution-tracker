# 🚀 GitHub Contribution Tracker

A powerful CLI tool to fetch and beautifully format all your GitHub contributions to any organization!

## ✨ Features

- 📊 Comprehensive contribution tracking
  - Pull Requests (open, closed, merged)
  - Issues
  - Commits
- 📝 Beautiful Markdown export
- 📅 Chronological sorting
- 🔍 Detailed statistics
- 🎯 Organization-specific insights

## 🛠️ Installation

1. Clone this repository:

```bash
git clone https://github.com/Siddhant-K-code/github-contribution-tracker
cd github-contribution-tracker
```

2. Install dependencies:

```bash
pip install requests
```

3. Set up your GitHub token:

```bash
export GITHUB_TOKEN=your_github_personal_access_token
```

## 🎮 Usage

Run the tracker with:

```bash
python main.py USERNAME ORGANIZATION_NAME
```

Example:

```bash
python main.py Siddhant-K-code OpenFGA
```


## 📦 Output
The tool generates a beautifully formatted contributions.md file containing:

### 📊 Summary Section

- Total Pull Requests
- Total Issues
- Total Commits

### 📝 Detailed Sections

- Pull Requests: Title, status, and date
- Issues: Title, status, and date
- Commits: Message and date

## 🔑 GitHub Token Permissions
Your token needs these scopes:

- `repo`
- `read:org`
- `read:user`

## 💡 Example Output

```markdown
# GitHub Contributions for Siddhant-K-code in OpenFGA

## Summary
- Total Pull Requests: 42
- Total Issues: 15
- Total Commits: 123

## Detailed Contributions
[...]
```

## 🛠️ Technical Details

- Uses GitHub's GraphQL API
- Implements pagination for complete data retrieval
- Sorts contributions chronologically
- Handles rate limiting gracefully
