# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['tfidf_zones']

package_data = \
{'': ['*']}

install_requires = \
['rich>=13.0,<14.0', 'scikit-learn>=1.5,<2.0', 'wordnet-lookup>=1.2']

entry_points = \
{'console_scripts': ['tfidf-zones = tfidf_zones.cli:main']}

setup_kwargs = {
    'name': 'tfidf-zones',
    'version': '1.2.1',
    'description': 'TF-IDF zone analysis CLI — classify terms into too-common, goldilocks, and too-rare zones',
    'long_description': '# tfidf-zones\n\n[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)\n[![Poetry](https://img.shields.io/badge/packaging-poetry-cyan.svg)](https://python-poetry.org/)\n[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.5-orange.svg)](https://scikit-learn.org/)\n[![License](https://img.shields.io/badge/license-MIT-green.svg)]()\n[![Downloads](https://img.shields.io/pepy/dt/tfidf-zones)](https://pepy.tech/project/tfidf-zones)\n[![Downloads/Month](https://img.shields.io/pepy/dm/tfidf-zones)](https://pepy.tech/project/tfidf-zones)\n\nCLI tool that classifies terms in text documents into three zones based on TF-IDF and document frequency:\n\n- **Too Common** — high document frequency (df > 0.2N)\n- **Goldilocks** — high TF-IDF score within a moderate DF band (3 ≤ df ≤ 0.2N, tfidf ≥ Q95)\n- **Too Rare** — low document frequency (df < 3)\n\nUseful for stylometric analysis, authorship attribution, and understanding term importance.\n\n## Install\n\n```bash\npoetry install\n```\n\n## Usage\n\n```bash\n# Analyze a single file\npoetry run tfidf-zones --file novel.txt --output results.csv\n\n# Use scikit-learn engine with bigrams\npoetry run tfidf-zones --file novel.txt --scikit --ngram 2 --output results.csv\n\n# Analyze a directory of .txt files\npoetry run tfidf-zones --dir ./texts/ --output results.csv\n\n# Show top 25 terms per zone with custom chunk size\npoetry run tfidf-zones --file novel.txt --top-k 25 --chunk-size 500 --output results.csv\n```\n\n## Recipes\n\n**Find content-word bigrams across a corpus:**\n\n```bash\npoetry run tfidf-zones \\\n  --dir ./texts/ --limit 100 --output results.csv \\\n  --no-chunk --wordnet --ngram 2 --no-ngram-stopwords\n```\n\nCombines `--wordnet` (only real English words), `--ngram 2` (bigrams), and `--no-ngram-stopwords` (discard bigrams containing stop/function words like "of_the") to surface meaningful two-word terms.\n\n**Find content phrases (trigrams and above):**\n\n```bash\npoetry run tfidf-zones \\\n  --dir ./texts/ --output results.csv \\\n  --no-chunk --wordnet --ngram 3 --no-ngram-stopwords\n```\n\nIncrease `--ngram` to 3, 4, or 5 to find longer phrases. The stopword filter removes any n-gram where at least one token is a stop word or function word, so only content-rich phrases survive.\n\n**Corpus analysis with post-processing filters:**\n\n```bash\npoetry run tfidf-zones \\\n  --dir ./texts/ --output results.csv \\\n  --no-chunk --wordnet --min-df 2 --min-tf 2\n```\n\nUse `--min-df` and `--min-tf` to remove terms that appear in too few documents or have too few total occurrences, reducing noise from hapax legomena.\n\n## Options\n\n| Flag | Default | Description |\n|------|---------|-------------|\n| `--file` | | Path to a single text file |\n| `--dir` | | Path to a directory of `.txt` files |\n| `--scikit` | off | Use scikit-learn TF-IDF engine (default: pure Python) |\n| `--top-k` | `10` | Number of terms per zone |\n| `--ngram` | `1` | N-gram level (1–5, or 6 for skipgrams) |\n| `--chunk-size` | `2000` | Tokens per chunk (min 100) |\n| `--limit` | all | Randomly select N files from directory (requires `--dir`) |\n| `--no-chunk` | off | Each file = one document, no chunking (requires `--dir`) |\n| `--wordnet` | off | Only recognized English words participate in TF-IDF |\n| `--no-ngram-stopwords` | off | Discard n-grams containing stop/function words (requires `--ngram` ≥ 2) |\n| `--min-df` | | Remove terms with document frequency below this value |\n| `--min-tf` | | Remove terms with term frequency below this value |\n| `--output` | | Output CSV file path (required) |\n\nEither `--file` or `--dir` is required (not both).\n\n## How It Works\n\nText is tokenized, split into chunks, and scored with TF-IDF. Chunking a single document into sub-documents prevents IDF from collapsing to a constant. Terms are then bucketed into zones by their document-frequency percentile.\n\nTwo engines are available: a pure-Python implementation and a scikit-learn backed implementation. Both use smooth IDF (`log((1+N)/(1+DF)) + 1`) and produce comparable results.\n',
    'author': 'Craig Trim',
    'author_email': 'craigtrim@gmail.com',
    'maintainer': 'Craig Trim',
    'maintainer_email': 'craigtrim@gmail.com',
    'url': 'None',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.11,<3.14',
}


setup(**setup_kwargs)
