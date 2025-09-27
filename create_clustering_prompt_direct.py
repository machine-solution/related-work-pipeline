#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Создание промпта для кластеризации статей напрямую из processed_papers.csv
"""

import pandas as pd
import os
import argparse

def create_clustering_prompt(papers_df):
    """Creates a prompt for clustering papers"""
    
    prompt_parts = []
    
    # Title
    prompt_parts.append("# Clustering of Manipulation and Machine Learning Papers")
    prompt_parts.append("")
    prompt_parts.append(f"Analyze the following {len(papers_df)} papers on manipulation and machine learning. Identify the main tasks and methods, and group them into clusters based on similar tasks and approaches.")
    prompt_parts.append("")
    
    # Instructions
    prompt_parts.append("## Instructions:")
    prompt_parts.append("1. Identify the main tasks addressed in the papers. Consider these key task categories:")
    prompt_parts.append("   - **Planning**: Path planning, motion planning, task planning")
    prompt_parts.append("   - **Control**: Executing planned motions on real robots, trajectory control")
    prompt_parts.append("   - **Grasping**: Object grasping, manipulation of grasped objects")
    prompt_parts.append("   - **Single vs Multi-arm**: Single manipulator vs multiple manipulators coordination")
    prompt_parts.append("   - **Static vs Mobile**: Fixed manipulators vs mobile manipulators")
    prompt_parts.append("2. Identify the key methods and approaches used.")
    prompt_parts.append("3. Group the papers into clusters based on similar tasks and methods. You need to independently define the groups based on the content of the papers.")
    prompt_parts.append("4. Ensure the following constraints are met:")
    prompt_parts.append("   - Every paper must be assigned to exactly one cluster.")
    prompt_parts.append("   - The total number of clusters should be between 10 and 15.")
    prompt_parts.append("   - Each cluster must contain at least 10 papers.")
    prompt_parts.append("5. For each group, provide:")
    prompt_parts.append("   - Group Name (e.g., 'Tactile Manipulation with Reinforcement Learning')")
    prompt_parts.append("   - Description of tasks and methods covered by the group.")
    prompt_parts.append("   - Complete list of ALL papers in the group with their numbers and titles.")
    prompt_parts.append("")
    
    # Papers
    prompt_parts.append("## Papers for Analysis:")
    prompt_parts.append("")
    
    for index, row in papers_df.iterrows():
        paper_id = row['index'] if 'index' in row else index
        title = row['title']
        abstract = row.get('abstract', '')
        
        prompt_parts.append(f"### Paper #{paper_id}")
        prompt_parts.append(f"**Title:** {title}")
        if abstract and pd.notna(abstract) and str(abstract).strip():
            prompt_parts.append(f"**Abstract:** {abstract}")
        else:
            prompt_parts.append(f"**Abstract:** [No abstract available]")
        
        prompt_parts.append("")
    
    # Expected Output
    prompt_parts.append("## Expected Output Format:")
    prompt_parts.append("Provide the clustering results in the following structured format:")
    prompt_parts.append("")
    prompt_parts.append("#### Cluster 1: <Group Name>")
    prompt_parts.append("- Summary: <Description of tasks and methods>")
    prompt_parts.append("- Papers:")
    prompt_parts.append("  - [Paper Index 1] <Paper Title 1>")
    prompt_parts.append("  - [Paper Index 2] <Paper Title 2>")
    prompt_parts.append("  - ...")
    prompt_parts.append("")
    prompt_parts.append("#### Cluster 2: <Group Name>")
    prompt_parts.append("- Summary: <Description of tasks and methods>")
    prompt_parts.append("- Papers:")
    prompt_parts.append("  - [Paper Index 1] <Paper Title 1>")
    prompt_parts.append("  - ...")
    prompt_parts.append("")
    prompt_parts.append("... (continue for all clusters)")
    prompt_parts.append("")
    
    return "\n".join(prompt_parts)

def main():
    parser = argparse.ArgumentParser(description='Create clustering prompt from processed papers')
    parser.add_argument('--input', default='output/filtered/processed_papers.csv', 
                       help='Input CSV file with processed papers')
    parser.add_argument('--output', default='related_work_prompt_raw.txt',
                       help='Output prompt file')
    
    args = parser.parse_args()
    
    # Load processed papers
    if not os.path.exists(args.input):
        print(f"Error: Input file {args.input} not found")
        return
    
    print(f"Loading papers from {args.input}...")
    papers_df = pd.read_csv(args.input)
    print(f"Loaded {len(papers_df)} papers")
    
    # Create prompt
    print("Creating clustering prompt...")
    prompt = create_clustering_prompt(papers_df)
    
    # Save prompt
    os.makedirs(os.path.dirname(args.output) if os.path.dirname(args.output) else '.', exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(prompt)
    
    print(f"Prompt saved to {args.output}")
    print(f"Prompt contains {len(prompt.split())} words and {len(prompt.splitlines())} lines")

if __name__ == "__main__":
    main()
