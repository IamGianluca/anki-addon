# Anki AI

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
git clone https://github.com/iamgianluca/anki-addon.git [your-anki-addons-path]/anki-addon
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

## 🧑‍💻 Development

### Project Structure

This project adopts Domain-Driven Design principles with a clear separation between domain, application, and infrastructure layers:

```
addon/
├── domain/            # Core domain models, entities, value objects
│   ├── models/
│   └── services/
├── application/       # Application services, use cases
│   └── services/
└── infrastructure/    # External systems adapters, repositories
    ├── adapters/
    └── repositories/
```

### Testing

To run the test suite:

1. Set up the necessary environment variables:
   ```bash
   export OPENAI_HOST=your_host_url
   export OPENAI_PORT=your_host_port
   export OPENAI_MODEL=your_llm_model
   ```

2. Run the tests:
   ```bash
   make test        # run unit tests
   make test_slow   # run unit, integration, and end-to-end tests
   ```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

- Anki for their amazing flashcard platform
- The Anki community for their support and feedback
