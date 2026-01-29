# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['fast_parse_time',
 'fast_parse_time.core',
 'fast_parse_time.explicit.bp',
 'fast_parse_time.explicit.dmo',
 'fast_parse_time.explicit.dto',
 'fast_parse_time.explicit.svc',
 'fast_parse_time.implicit.dmo',
 'fast_parse_time.implicit.dto',
 'fast_parse_time.implicit.svc']

package_data = \
{'': ['*']}

install_requires = \
['dateparser', 'word2number']

setup_kwargs = {
    'name': 'fast-parse-time',
    'version': '1.2.0',
    'description': 'Natural Language (NLP) Extraction of Date and Time',
    'long_description': '# fast-parse-time\n\n[![PyPI version](https://img.shields.io/pypi/v/fast-parse-time.svg)](https://pypi.org/project/fast-parse-time/)\n[![Python Version](https://img.shields.io/pypi/pyversions/fast-parse-time.svg)](https://pypi.org/project/fast-parse-time/)\n[![Downloads](https://pepy.tech/badge/fast-parse-time/month)](https://pepy.tech/project/fast-parse-time)\n[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)\n\nExtract dates and times from text. Fast, deterministic, zero cost.\n\n## Why?\n\nLLMs can parse dates, but they\'re slow, expensive, and non-deterministic. This library gives you:\n\n- **Sub-millisecond performance** - Process thousands of documents per second\n- **Zero API costs** - No per-request charges\n- **Deterministic results** - Same input always produces same output\n- **Simple API** - One function call, everything extracted\n\n## Install\n\n```bash\npip install fast-parse-time\n```\n\n## Usage\n\n```python\nfrom fast_parse_time import parse_dates\n\ntext = "Meeting on 04/08/2024 to discuss issues from 5 days ago"\nresult = parse_dates(text)\n\n# Explicit dates found in text\nprint(result.explicit_dates)\n# [ExplicitDate(text=\'04/08/2024\', date_type=\'FULL_EXPLICIT_DATE\')]\n\n# Relative time expressions\nprint(result.relative_times)\n# [RelativeTime(cardinality=5, frame=\'day\', tense=\'past\')]\n\n# Convert to Python datetime\nfor time_ref in result.relative_times:\n    print(time_ref.to_datetime())\n    # datetime.datetime(2025, 11, 14, ...)\n```\n\n## What It Extracts\n\n**Explicit dates:**\n```python\n"Event on 04/08/2024"          → 04/08/2024 (full date)\n"Meeting scheduled for 3/24"   → 3/24 (month/day)\n"Copyright 2024"               → 2024 (year only)\n"Ambiguous: 4/8"               → 4/8 (flagged as ambiguous)\n```\n\n**Relative times:**\n```python\n"5 days ago"                   → 5 days (past)\n"last couple of weeks"         → 2 weeks (past)\n"30 minutes ago"               → 30 minutes (past)\n```\n\n## Examples\n\n### Parse everything at once\n\n```python\nresult = parse_dates("Report from 04/08/2024 covering issues from last week")\n\nresult.explicit_dates  # [\'04/08/2024\']\nresult.relative_times  # [RelativeTime(cardinality=1, frame=\'week\', tense=\'past\')]\n```\n\n### Just get dates\n\n```python\nfrom fast_parse_time import extract_explicit_dates\n\ndates = extract_explicit_dates("Event on 04/08/2024 or maybe 3/24")\n# {\'04/08/2024\': \'FULL_EXPLICIT_DATE\', \'3/24\': \'MONTH_DAY\'}\n```\n\n### Convert to datetime objects\n\n```python\nfrom fast_parse_time import resolve_to_datetime\n\ndatetimes = resolve_to_datetime("Show me data from 5 days ago")\n# [datetime.datetime(2025, 11, 14, ...)]\n```\n\n## Features\n\n- Multiple date formats: `04/08/2024`, `3/24`, `2024-06-05`\n- Multiple delimiters: `/`, `-`, `.`\n- Relative time expressions: "5 days ago", "last week", "couple of months ago"\n- Ambiguity detection: Flags dates like `4/8` that could be April 8 or August 4\n- Time frame support: seconds, minutes, hours, days, weeks, months, years\n\n## Documentation\n\n- [Complete API Reference](docs/API.md)\n- [System Boundaries](BOUNDARIES.md) - Design decisions and limitations\n- [Examples](docs/API.md#examples)\n\n## Performance\n\nTypical extraction takes < 1ms per document. No network calls, no model inference, pure Python.\n\n## License\n\nMIT - See [LICENSE](LICENSE) for details.\n\n## Author\n\n**Craig Trim** - [craigtrim@gmail.com](mailto:craigtrim@gmail.com)\n\n---\n\n[Report Issues](https://github.com/craigtrim/fast-parse-time/issues) | [API Docs](docs/API.md) | [PyPI](https://pypi.org/project/fast-parse-time/)\n',
    'author': 'Craig Trim',
    'author_email': 'craigtrim@gmail.com',
    'maintainer': 'Craig Trim',
    'maintainer_email': 'craigtrim@gmail.com',
    'url': 'https://github.com/craigtrim/fast-parse-time',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.11.5,<4.0.0',
}


setup(**setup_kwargs)
