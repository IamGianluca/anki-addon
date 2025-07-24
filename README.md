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

- Anki 2.1.x or later
- Access to an OpenAI API compatible inference server

## 🚀 Installation

Clone this repository into your Anki add-ons folder:

```bash
git clone https://github.com/iamgianluca/anki-addon.git [your-anki-addons-path]/addons21/anki-addon
```

## ⚙️ Configuration

1. Start Anki and go to `Tools > Add-ons`
2. Select "anki-addon" and click `Config`
3. Fill in the following required settings:
   ```json
   {
     "openai_host": "your_host_url",
     "openai_port": "your_host_port",
     "openai_model": "your_llm_model",
   }
   ```
4. Click `Save`

## 🔍 Usage

1. Select a note or multiple notes in Anki
2. Right-click and select "Refactor with LLM" from the context menu
3. Choose your refactoring options from the dialog
4. Review and approve the suggested changes

## 🤝 Contributing

Contributions are welcome! Please check the CONTRIBUTING.md file and feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

- Anki for their amazing flashcard platform
- The Anki community for their support and feedback
