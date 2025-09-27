# Papers Search and Analysis Pipeline

This repository contains a comprehensive pipeline for searching, processing, and analyzing academic papers related to manipulation and machine learning in robotics.

## Overview

The pipeline automates the process of:
1. **Searching** for papers from multiple academic sources (arXiv, IEEE, ACM, etc.)
2. **Processing** and filtering papers based on ML keywords
3. **Downloading** PDF files of relevant papers
4. **Generating** clustering prompts for AI analysis

## Features

- **Multi-source search**: Supports arXiv, IEEE Xplore, ACM Digital Library, and other academic databases
- **Intelligent filtering**: Uses ML keywords to identify relevant papers
- **PDF download**: Automatically downloads papers with duplicate detection
- **Abstract extraction**: Retrieves full abstracts for comprehensive analysis
- **Clustering prompts**: Generates structured prompts for AI-powered paper clustering

## Project Structure

```
papers_search/
├── search.py                    # Main search script
├── process_papers.py           # Paper processing and filtering
├── download_final_papers.py    # PDF download functionality
├── create_clustering_prompt_direct.py  # Prompt generation
├── config.py                   # Configuration settings
├── output/                     # Output directory
│   ├── papers/                 # Downloaded PDF files
│   ├── filtered/               # Processed paper data
│   └── found/                  # Search results
└── related_work_prompt_raw.txt # Generated clustering prompt
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd papers_search
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### 1. Search for Papers
```bash
python search.py
```
This will search for papers from various academic sources and save results to `output/`.

### 2. Process and Filter Papers
```bash
python process_papers.py
```
Filters papers based on ML keywords and creates processed datasets.

### 3. Download PDF Files
```bash
python download_final_papers.py --input output/found/final_papers_table.csv
```
Downloads PDF files for all papers with valid links.

### 4. Generate Clustering Prompt
```bash
python create_clustering_prompt_direct.py
```
Creates a structured prompt for AI-powered paper clustering analysis.

## Configuration

Edit `config.py` to customize:
- Search keywords and queries
- ML-related keywords for filtering
- Output directories
- Download settings

## Output Files

- `final_papers_table.csv`: Complete table of processed papers with metadata
- `related_work_prompt_raw.txt`: Structured prompt for AI clustering
- `output/papers/`: Downloaded PDF files organized by source

## Requirements

- Python 3.7+
- requests
- beautifulsoup4
- pandas
- tqdm
- selenium (for dynamic content)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

This pipeline was developed for academic research in robotics and machine learning. It integrates with multiple academic databases and provides a streamlined workflow for literature review and analysis.
