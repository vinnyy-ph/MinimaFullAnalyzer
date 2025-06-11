#!/usr/bin/env python3
import sys
import os

def count_metrics(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            lines = content.split('\n')
            
            char_count = len(content)
            line_count = len(lines)
            non_empty_lines = sum(1 for line in lines if line.strip())
            
            return {
                'characters': char_count,
                'lines': line_count,
                'non_empty_lines': non_empty_lines
            }
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print("Usage: python length_code.py <filename>")
        sys.exit(1)
    
    # Handle the filename with or without the leading dash
    filename = sys.argv[1]
    if filename.startswith('-'):
        filename = filename[1:]
    
    metrics = count_metrics(filename)
    
    print(f"File: {filename}")
    print(f"Total characters: {metrics['characters']}")
    print(f"Total lines: {metrics['lines']}")
    print(f"Non-empty lines: {metrics['non_empty_lines']}")

if __name__ == "__main__":
    main() 