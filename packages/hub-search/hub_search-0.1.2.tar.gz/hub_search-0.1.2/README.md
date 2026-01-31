# Hub Search

A powerful Python CLI tool to detect, extract, and verify sensitive information (like API keys) from GitHub.

## Features

- **Search**: Query GitHub Code Search API with enumeration (`a-z0-9`) and pagination support.
- **Clean**: Extract specific patterns (e.g., `sk-xxxxxxxx`) from raw search result files.
- **Verify**: Validate extracted DashScope/OpenAI-compatible API keys by testing them against the live API.

## Installation

```bash
pip install hub-search
```

## Configuration

Set your GitHub Token (required for search rate limits):
```bash
export GITHUB_TOKEN='your_github_token'
```

## Usage

### 1. Search
Search for keys using enumeration mode.
```bash
hub-search search "DASHSCOPE_API_KEY=sk-" --enum --limit 100
```

### 2. Clean
Extract keys from the search results directory.
```bash
hub-search clean 202512271649 keys.txt
```

### 3. Verify
Validate extracted keys.
```bash
hub-search verify keys.txt --output valid.txt --threads 10
```

### 4. Automated Task
Run the entire workflow (Search -> Clean -> Verify) in one go.
```bash
# Automatically creates .hub-search directory and manages results
hub-search task "DASHSCOPE_API_KEY=sk-" --limit 100
```
*Creates a timestamped directory inside `.hub-search/` containing raw results, clean keys, and valid keys.*

## Token Permissions
- **Public Search**: No scopes required (Classic Token).
- **Private Search**: `repo` scope required.