#!/usr/bin/env python3
"""
Markdown to Jupyter Notebook converter.
Splits markdown by --- delimiters and extracts code blocks as code cells.
"""

import re
import sys
import json
import argparse
from pathlib import Path

try:
    import nbformat
    from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell
except ImportError:
    print("Error: nbformat is required. Install with: pip install nbformat", file=sys.stderr)
    sys.exit(1)


# Default languages treated as code cells
DEFAULT_CODE_LANGUAGES = {'python', 'sql'}


def remove_front_matter(content: str) -> str:
    """
    Remove YAML front matter from the beginning of content.
    Front matter is the first ---...--- block at the very start of the file.
    """
    if not content.startswith('---'):
        return content

    lines = content.split('\n')
    in_front_matter = False
    end_index = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == '---':
            if not in_front_matter:
                # Starting front matter
                in_front_matter = True
            else:
                # Ending front matter
                end_index = i + 1
                break

    if end_index > 0:
        return '\n'.join(lines[end_index:])

    return content


def split_by_delimiter(content: str, delimiter: str = '---') -> list:
    """
    Split content by delimiter, but not when inside code blocks.
    Uses a state machine to track code block boundaries.
    """
    lines = content.split('\n')
    sections = []
    current_section = []
    in_code_block = False

    for line in lines:
        stripped = line.strip()

        # Check for code block boundaries
        if stripped.startswith('```'):
            in_code_block = not in_code_block
            current_section.append(line)
            continue

        # Check for delimiter (only when not in code block)
        if not in_code_block and stripped == delimiter:
            # Save current section
            section_content = '\n'.join(current_section).strip()
            if section_content:
                sections.append(section_content)
            current_section = []
        else:
            current_section.append(line)

    # Don't forget the last section
    section_content = '\n'.join(current_section).strip()
    if section_content:
        sections.append(section_content)

    return sections


def extract_cells_from_section(section: str, code_languages: set) -> list:
    """
    Extract markdown and code cells from a section.
    Only code blocks with languages in code_languages become code cells.
    Other code blocks remain part of the markdown content.

    Returns list of dicts with 'type', 'content', and 'language' keys.
    """
    cells = []

    # Pattern to match fenced code blocks with optional language
    # Matches: ```language\n...\n```
    code_block_pattern = re.compile(
        r'^```(\w*)\n(.*?)^```$',
        re.MULTILINE | re.DOTALL
    )

    last_end = 0

    for match in code_block_pattern.finditer(section):
        language = match.group(1).lower()

        # Only extract if language is in code_languages
        if language in code_languages:
            # Add markdown content before this code block
            before_content = section[last_end:match.start()].strip()
            if before_content:
                cells.append({
                    'type': 'markdown',
                    'content': before_content,
                    'language': None
                })

            code_content = match.group(2).rstrip()
            cells.append({
                'type': 'code',
                'content': code_content,
                'language': language
            })

            last_end = match.end()
        # else: don't extract, leave as part of markdown

    # Add remaining markdown content after last extracted code block
    after_content = section[last_end:].strip()
    if after_content:
        cells.append({
            'type': 'markdown',
            'content': after_content,
            'language': None
        })

    return cells


def parse_markdown(content: str, code_languages: set = None) -> list:
    """
    Main parsing function.
    Returns list of cells: {"type": str, "content": str, "language": str}
    """
    if code_languages is None:
        code_languages = DEFAULT_CODE_LANGUAGES

    # 1. Remove front matter
    content = remove_front_matter(content)

    # 2. Split by ---
    sections = split_by_delimiter(content)

    # 3. Extract cells from each section
    cells = []
    for section in sections:
        section_cells = extract_cells_from_section(section, code_languages)
        cells.extend(section_cells)

    # 4. Filter empty cells
    cells = [c for c in cells if c['content'].strip()]

    return cells


def create_notebook(cells: list) -> nbformat.NotebookNode:
    """Create notebook from parsed cells."""
    nb = new_notebook()

    for cell in cells:
        if cell['type'] == 'markdown':
            nb.cells.append(new_markdown_cell(cell['content']))
        elif cell['type'] == 'code':
            code_cell = new_code_cell(cell['content'])
            # Set metadata for non-Python languages
            if cell.get('language') and cell['language'] != 'python':
                code_cell.metadata['language'] = cell['language']
            nb.cells.append(code_cell)

    return nb


def convert(input_path: str, output_path: str, code_languages: set = None) -> dict:
    """
    Convert markdown file to Jupyter notebook.

    Returns dict with conversion stats.
    """
    content = Path(input_path).read_text(encoding='utf-8')

    cells = parse_markdown(content, code_languages)
    nb = create_notebook(cells)

    with open(output_path, 'w', encoding='utf-8') as f:
        nbformat.write(nb, f)

    # Return stats
    markdown_count = sum(1 for c in cells if c['type'] == 'markdown')
    code_count = sum(1 for c in cells if c['type'] == 'code')

    return {
        'status': 'success',
        'input': input_path,
        'output': output_path,
        'total_cells': len(cells),
        'markdown_cells': markdown_count,
        'code_cells': code_count
    }


def main():
    parser = argparse.ArgumentParser(
        description='Convert markdown to Jupyter notebook'
    )
    parser.add_argument('input', help='Input markdown file')
    parser.add_argument('output', help='Output .ipynb file')
    parser.add_argument(
        '--code-languages',
        help='Comma-separated list of languages to treat as code cells',
        default=','.join(DEFAULT_CODE_LANGUAGES)
    )

    args = parser.parse_args()

    code_languages = set(args.code_languages.split(','))

    try:
        result = convert(args.input, args.output, code_languages)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({
            'status': 'error',
            'error': str(e)
        }, indent=2), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
