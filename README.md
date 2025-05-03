# High Valyrian Declension Practice

A command-line tool for practicing High Valyrian noun and adjective declensions.

## Features

- Practice noun declensions across different cases and quantities
- Practice adjective declensions with various parameters:
  - Cases (Nominative, Accusative, Genitive, etc.)
  - Quantities (Singular, Plural)
  - Positions (e.g., postpositive)
  - Genders
  - Declension types
- Performance tracking and statistics
- Flexible practice modes (fixed number of questions or endless mode)

# Getting Started
## Practicing Noun Declensions
`python declen_practice.py`
## Practicing Adj Declensions
`python adj_practice.py`

### Prerequisites

- Python 3.10 or higher (requires support for newer type hinting syntax)
Dependencies:
- colorama
- beautifulsoup4 (only needed for database scraping tools)

The program will prompt you with words and ask you to provide their correct declension forms. You can:
- Set a maximum number of practice questions
- Practice endlessly by setting test_max to 0 or a negative value
- Quit at any time using `/q` or `/quit`

## Database Structure

The project uses SQLite to store:
- Word forms and their declensions
- User performance statistics

## Learning Features

- Tracks your performance to focus on areas needing improvement
- Times your responses to help point out weaknesses
- Saves failed attempts for targeted practice
- Supports all declension cases for nouns and adjectives