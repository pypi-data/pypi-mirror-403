# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['fast_sentence_segment',
 'fast_sentence_segment.bp',
 'fast_sentence_segment.core',
 'fast_sentence_segment.dmo',
 'fast_sentence_segment.svc']

package_data = \
{'': ['*']}

install_requires = \
['spacy>=3.8.0,<4.0.0']

entry_points = \
{'console_scripts': ['segment = fast_sentence_segment.cli:main',
                     'segment-file = fast_sentence_segment.cli:file_main']}

setup_kwargs = {
    'name': 'fast-sentence-segment',
    'version': '1.3.0',
    'description': 'Fast and Efficient Sentence Segmentation',
    'long_description': '# Fast Sentence Segmentation\n\n[![PyPI version](https://img.shields.io/pypi/v/fast-sentence-segment.svg)](https://pypi.org/project/fast-sentence-segment/)\n[![Python versions](https://img.shields.io/pypi/pyversions/fast-sentence-segment.svg)](https://pypi.org/project/fast-sentence-segment/)\n[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)\n[![spaCy](https://img.shields.io/badge/spaCy-3.8-blue.svg)](https://spacy.io/)\n[![Downloads](https://static.pepy.tech/badge/fast-sentence-segment)](https://pepy.tech/project/fast-sentence-segment)\n[![Downloads/Month](https://static.pepy.tech/badge/fast-sentence-segment/month)](https://pepy.tech/project/fast-sentence-segment)\n\nFast and efficient sentence segmentation using spaCy with surgical post-processing fixes. Handles complex edge cases like abbreviations (Dr., Mr., etc.), ellipses, quoted text, and multi-paragraph documents.\n\n## Why This Library?\n\n1. **Keep it local**: LLM API calls cost money and send your data to third parties. Run sentence segmentation entirely on your machine.\n2. **spaCy perfected**: spaCy is a great local model, but it makes mistakes. This library fixes most of spaCy\'s shortcomings.\n\n## Features\n\n- **Paragraph-aware segmentation**: Returns sentences grouped by paragraph\n- **Abbreviation handling**: Correctly handles "Dr.", "Mr.", "etc.", "p.m.", "a.m." without false splits\n- **Ellipsis preservation**: Keeps `...` intact while detecting sentence boundaries\n- **Question/exclamation splitting**: Properly splits on `?` and `!` followed by capital letters\n- **Cached processing**: LRU cache for repeated text processing\n- **Flexible output**: Nested lists (by paragraph) or flattened list of sentences\n- **Bullet point & numbered list normalization**: Cleans common list formats\n- **CLI tool**: Command-line interface for quick segmentation\n\n## Installation\n\n```bash\npip install fast-sentence-segment\n```\n\nAfter installation, download the spaCy model:\n\n```bash\npython -m spacy download en_core_web_sm\n```\n\n## Quick Start\n\n```python\nfrom fast_sentence_segment import segment_text\n\ntext = "Do you like Dr. Who? I prefer Dr. Strange! Mr. T is also cool."\n\nresults = segment_text(text, flatten=True)\n```\n\n```json\n[\n  "Do you like Dr. Who?",\n  "I prefer Dr. Strange!",\n  "Mr. T is also cool."\n]\n```\n\nNotice how "Dr. Who?" stays together as a single sentence—the library correctly recognizes that a title followed by a single-word name ending in `?` or `!` is a name reference, not a sentence boundary.\n\n## Usage\n\n### Basic Segmentation\n\nThe `segment_text` function returns a list of lists, where each inner list represents a paragraph containing its sentences:\n\n```python\nfrom fast_sentence_segment import segment_text\n\ntext = """Gandalf spoke softly. "All we have to decide is what to do with the time given us."\n\nFrodo nodded. The weight of the Ring pressed against his chest."""\n\nresults = segment_text(text)\n```\n\n```json\n[\n  [\n    "Gandalf spoke softly.",\n    "\\"All we have to decide is what to do with the time given us.\\"."\n  ],\n  [\n    "Frodo nodded.",\n    "The weight of the Ring pressed against his chest."\n  ]\n]\n```\n\n### Flattened Output\n\nIf you don\'t need paragraph boundaries, use the `flatten` parameter:\n\n```python\ntext = "At 9 a.m. the hobbits set out. By 3 p.m. they reached Rivendell. Mr. Frodo was exhausted."\n\nresults = segment_text(text, flatten=True)\n```\n\n```json\n[\n  "At 9 a.m. the hobbits set out.",\n  "By 3 p.m. they reached Rivendell.",\n  "Mr. Frodo was exhausted."\n]\n```\n\n### Direct Segmenter Access\n\nFor more control, use the `Segmenter` class directly:\n\n```python\nfrom fast_sentence_segment import Segmenter\n\nsegmenter = Segmenter()\nresults = segmenter.input_text("Your text here.")\n```\n\n### Command Line Interface\n\n```bash\n# Inline text\nsegment "Gandalf paused... You shall not pass! The Balrog roared."\n\n# Pipe from stdin\necho "Have you seen Dr. Who? It\'s brilliant!" | segment\n\n# Numbered output\nsegment -n -f silmarillion.txt\n\n# File-to-file (one sentence per line)\nsegment-file --input-file book.txt --output-file sentences.txt\n\n# Unwrap hard-wrapped e-texts (Project Gutenberg, etc.)\nsegment-file --input-file book.txt --output-file sentences.txt --unwrap\n```\n\n## API Reference\n\n| Function | Parameters | Returns | Description |\n|----------|------------|---------|-------------|\n| `segment_text()` | `input_text: str`, `flatten: bool = False`, `unwrap: bool = False` | `list` | Main entry point for segmentation |\n| `Segmenter.input_text()` | `input_text: str` | `list[list[str]]` | Cached paragraph-aware segmentation |\n\n### CLI Commands\n\n| Command | Description |\n|---------|-------------|\n| `segment [text]` | Segment text from argument, `-f FILE`, or stdin. Use `-n` for numbered output. |\n| `segment-file --input-file IN --output-file OUT [--unwrap]` | Segment a file and write one sentence per line. Use `--unwrap` for hard-wrapped e-texts. |\n\n## Why Nested Lists?\n\nThe segmentation process preserves document structure by segmenting into both paragraphs and sentences. Each outer list represents a paragraph, and each inner list contains that paragraph\'s sentences. This is useful for:\n\n- Document structure analysis\n- Paragraph-level processing\n- Maintaining original text organization\n\nUse `flatten=True` when you only need sentences without paragraph context.\n\n## Requirements\n\n- Python 3.9+\n- spaCy 3.8+\n- en_core_web_sm spaCy model\n\n## How It Works\n\nThis library uses spaCy for initial sentence segmentation, then applies surgical post-processing fixes for cases where spaCy\'s default behavior is incorrect:\n\n1. **Pre-processing**: Normalize numbered lists, preserve ellipses with placeholders\n2. **spaCy segmentation**: Use spaCy\'s sentence boundary detection\n3. **Post-processing**: Split on abbreviation boundaries, handle `?`/`!` + capital patterns\n4. **Denormalization**: Restore placeholders to original text\n\n## License\n\nMIT License - see [LICENSE](LICENSE) for details.\n\n## Contributing\n\nContributions are welcome! Please feel free to submit a Pull Request.\n\n1. Fork the repository\n2. Create your feature branch (`git checkout -b feature/amazing-feature`)\n3. Run tests (`make test`)\n4. Commit your changes\n5. Push to the branch\n6. Open a Pull Request\n',
    'author': 'Craig Trim',
    'author_email': 'craigtrim@gmail.com',
    'maintainer': 'Craig Trim',
    'maintainer_email': 'craigtrim@gmail.com',
    'url': 'https://github.com/craigtrim/fast-sentence-segment',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.9,<4.0',
}


setup(**setup_kwargs)
