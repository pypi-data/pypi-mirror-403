# Renovation-Ad

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)

**Renovation-Ad** is a high-performance Python library designed to clean HTML by removing ad elements based on standard Adblock rules (e.g., EasyList). 

Unlike other libraries that struggle with performance when handling tens of thousands of rules, **Renovation-Ad** utilizes a "Content-Aware Filtering" strategy combined with `lxml` to achieve extreme speeds—capable of processing complex pages with 13,000+ rules in **under 0.2 seconds**.

---

## ✨ Features

- **Extreme Performance**: Optimized with a DOM-content-aware pre-filter (Bloom Filter strategy). 
- **Lightweight**: Pure Python rule engine. No Rust or C++ compiler required for installation.
- **EasyList Support**: Supports standard Adblock Plus / EasyList cosmetic rules (`##selector`).
- **Domain Intelligence**: Correctly handles domain-specific rules (`example.com##.ad`) and exclusions (`~example.com##.ad`).
- **Flexible Input**: Automatically handles rule lists from URLs, local files, or raw strings.
- **Hybrid Parser**: Uses `lxml` for maximum speed with an automatic fallback to `BeautifulSoup4`.

---

## 🚀 Performance Comparison

In real-world testing on highly commercialized news pages (e.g., Yahoo News) with **13,000+ active rules**:

| Method | Time |
| :--- | :--- |
| Standard `BeautifulSoup` + Naive Loop | ~115.0 seconds |
| **Renovation-Ad (LXML + Content-Aware)** | **0.14 seconds** |

*Optimization: By scanning the DOM for existing IDs and Classes first, we reduce the number of CSS queries by over 98%.*

---

## 📦 Installation

```bash
pip install renovation-ad
```

**Note:** `lxml` and `cssselect` are highly recommended for the best performance:
```bash
pip install lxml cssselect
```

---

## 🛠 Usage

### Quick Start (Function Interface)

```python
from renovation_ad import clean_html

rules = [
    "https://easylist-downloads.adblockplus.org/easylist.txt", # Remote URL
    "./my_custom_rules.txt",                                  # Local file
    "##.top-banner-ads"                                       # Raw rule string
]

html_content = "<html><body><div class='top-banner-ads'>Ad</div><p>Content</p></body></html>"
page_url = "https://example.com/article"

cleaned_html = clean_html(html_content, page_url, rules)
```

### Advanced Usage (Class Interface)

Initializing the `Renovator` once is more efficient if you are processing multiple pages with the same rule set.

```python
from renovation_ad import Renovator

# Initialize and load rules (downloads and parses)
renovator = Renovator(
    rules_list=["https://easylist-downloads.adblockplus.org/easylist.txt"],
    dom_parser="lxml" # Default is lxml
)

# Clean multiple contents
html_1 = renovator.clean(raw_html_1, "https://site-a.com")
html_2 = renovator.clean(raw_html_2, "https://site-b.com")
```

---

## 🔍 How it Works

1. **Rule Parsing**: The library parses EasyList files into an internal map of domain-specific and generic cosmetic rules.
2. **Content-Aware Filtering**: Before running CSS selectors, **Renovation-Ad** scans the HTML for all present `id` and `class` attributes.
3. **Selector Pruning**: Rules targeting classes or IDs not present in the current document are skipped entirely.
4. **Batch Execution**: Remaining selectors are bundled into large batches (e.g., 500 per group) and executed via `lxml`'s highly optimized C engine.

---

## 📜 Supported Rule Syntax

| Syntax | Description |
| :--- | :--- |
| `##.ad-class` | Hide all elements with class `ad-class` (Generic) |
| `###ad-id` | Hide element with ID `ad-id` |
| `example.com##.sidebar-ad` | Hide only on `example.com` |
| `~example.com##.global-ad` | Hide everywhere EXCEPT `example.com` |
| `domain1.com,domain2.com##.ad`| Hide on multiple specific domains |

---

## 🛠 Dependencies

- `requests`: For fetching remote rule lists.
- `lxml`: For high-speed DOM manipulation.
- `cssselect`: For translating CSS selectors to XPath.
- `beautifulsoup4`: Provided as a fallback parser.

---

## 📄 License

This project is licensed under the **MIT License**. See the `LICENSE` file for details.

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/yourusername/renovation-ad/issues).