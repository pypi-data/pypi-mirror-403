# Contributing to jeomaechu (점메추) 🍱

[한국어 버전](CONTRIBUTING_ko.md)

Thank you for your interest in contributing to `jeomaechu`! This project aims to provide **high-quality, curated lunch data** for those struggling with indecision. Your contributions make this engine more powerful, accurate, and realistic.

---

## 🎯 Contribution Philosophy

1.  **Hyper-Realism**: We focus on "realistic" menus that people actually encounter in daily life, rather than just generic food names. (e.g., "Empty-the-fridge Bibimbap," "Spam with warm white rice").
2.  **Authenticity**: For global cuisines, we prioritize authentic pronunciations or widely accepted accurate names over lazy translations.
3.  **Data Quality**: Curating "persuasive" items that make users say "That's it!" is more important than simply increasing the total count.

---

## 📂 Data Addition Rules (`jeomaechu/data.py`)

When adding or modifying menu data, please strictly follow these regulations:

### 1. Category Classification (`MENU_DATA`)
- Add items to the list under the category that best matches the cuisine's culture or nature.
- **No Duplicates**: Always check if the menu item already exists before adding.

### 2. Naming Conventions
- **Korean Cuisine**: Use common names but be specific about key ingredients (e.g., "Beef Brisket Kimchi Stew" instead of just "Stew").
- **Global Cuisine**: Prioritize original pronunciations. You may add brief explanations in parentheses if necessary (e.g., "Pasta Aglio e Olio").
- **Emoji Usage**: Avoid excessive emojis in menu names, except for essential indicators like the spicy emoji (`🌶️`) used for tagging logic.

### 3. Tagging System (`TAGS`)
- All items are automatically tagged based on keywords.
- After adding a new menu, verify if the core keywords of the item are included in the **keyword list** within the `TAGS` dictionary (e.g., Spicy, Meat, Seafood).
- If necessary, add new keywords to the respective tag's list to improve detection accuracy.

---

## 💻 CLI & Feature Contribution (`jeomaechu/cli.py`)

Rules for adding new features or commands for user convenience:

### 1. Shorthand Commands
- Use the `Typer` decorator when adding new Korean shorthand commands.
- Always include a `help` argument to explain the purpose of the command.
- Call the internal helper function `_perform_pick()` instead of re-implementing logic to maintain a consistent output style.

### 2. Aliases
- Register commonly used synonyms as alias commands with `hidden=True` to improve usability (e.g., `매운거` as an alias for `매워`).

---

## 🚀 Contribution Workflow

1.  **Fork & Clone**: Fork the repository and clone it to your local machine.
2.  **Branch Creation**: Create a new branch for your feature or data addition (`git checkout -b feature/new-menu`).
3.  **Implementation**: Write your code while adhering to the guidelines.
4.  **Verification**: Test your changes in the terminal using `python3 -m jeomaechu.cli [command]`.
5.  **Pull Request**: Commit your changes and submit a PR.
    - Use clear commit message prefixes like `feat:`, `fix:`, `docs:`, or `data:`.

---

## 🎨 Style Guide

- **Python**: Follow PEP 8 guidelines. Use type hints for functions and variables wherever possible.
- **Markdown**: Use consistent header hierarchies and table formats to ensure readability.
- **Bilingual Support**: Try to update both English and Korean versions (README, CONTRIBUTING) to maintain global accessibility.
- **Install Methods**: When adding dependencies or changing entry points, ensure it doesn't break Docker or Curl installation methods.

Your contribution, no matter how small, helps someone enjoy a better lunch today. Happy coding and happy eating! 🍱
