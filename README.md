# Anki AI

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/IamGianluca/anki-addon)

A powerful Anki add-on that leverages Large Language Models (LLMs) to help you refactor and improve your notes with AI assistance.

## 🌟 Features

- Automatically refactor and improve your Anki notes
- Enhance readability and clarity of your study materials
- Maintain the original meaning while improving structure
- Compatible with OpenAI API and other compatible inference servers
- Seamlessly integrates with Anki's interface

## 📋 Prerequisites

- Anki 24.11 or later
- [uv](https://github.com/astral-sh/uv) (used to bundle dependencies)
- Access to an OpenAI API compatible inference server

## 🚀 Installation

Clone this repository into your Anki add-ons folder and build the dependencies:

```bash
git clone https://github.com/iamgianluca/anki-addon.git [your-anki-addons-path]/addons21/anki-addon
cd [your-anki-addons-path]/addons21/anki-addon
./bundle_dependencies.sh  # installs Python 3.9 via uv and vendors pydantic, qdrant-client, and their dependencies
```

## ⚙️ Configuration

1. Start Anki and go to `Tools > Add-ons`
2. Select "anki-addon" and click `Config`
3. Fill in the required settings:
   ```json
   {
     "openai_host": "your_host_url",
     "openai_port": "your_host_port",
     "openai_model": "your_llm_model"
   }
   ```
4. Optional settings (add only if needed for your model):
   ```json
   {
     "openai_mode": "v1/chat/completions",
     "openai_temperature": 0.0,
     "openai_max_tokens": 200,
     "openai_top_p": 0.9,
     "openai_top_k": 40,
     "openai_min_p": 0.05
   }
   ```
5. Click `Save`

## 🔍 Usage

### Format a note with AI

1. Open a note in the Anki editor
2. Click the AI toolbar button or press `Ctrl+Alt+M`
3. Review the suggested changes in the dialog
4. Click `Apply changes` to accept or dismiss to cancel

### Bulk review flagged notes

1. Flag notes with the orange flag for review
2. Go to `Tools > Improve note using AI` (or press `r`)
3. Step through each note, saving or skipping changes

### Count notes flagged for review

Go to `Tools > Count notes marked for review` (or press `c`) to see how many notes in the current deck are flagged for review.

## 🤝 Contributing

Contributions are welcome! Please check the [CONTRIBUTING.md](CONTRIBUTING.md) file and feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

- Anki for their amazing flashcard platform
- The Anki community for their support and feedback
