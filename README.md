# Anki AI

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/IamGianluca/anki-addon)

An Anki add-on that uses LLMs to keep your deck healthy: it refactors
individual notes and curates whole clusters of related notes, with a
human reviewing every change before it touches the collection.

## 🌟 Features

- **Format a note with AI** — rewrite a single note to be clearer and
  more atomic, keeping the original meaning and content intact
- **Curate a cluster with an AI agent** — select any note in the
  editor and an agent explores its cluster of related notes (search,
  read, propose edits, splits, new notes, deletions), validates
  atomicity, and presents a single change set for review
- **Human-in-the-loop by construction** — the agent has no write
  access to your collection; everything it proposes is reviewed and
  approved in one batch before being applied
- **Bulk review** — flag notes for review, then step through them one
  by one in a dedicated editor, saving or skipping changes
- **Compatible with OpenAI-compatible inference servers** (self-hosted
  llama.cpp, vLLM, ...) **and OpenCode Go** (hosted open coding
  models)
- **Session traces** — every curation session is recorded with its
  outcome, so you can audit what the AI did and mine rejections for
  recurring failure modes (see the trace viewer)

## 📋 Prerequisites

- Anki 26.x (embeds Python 3.13)
- [uv](https://github.com/astral-sh/uv) (used to bundle dependencies)
- An LLM endpoint: either an OpenAI API compatible inference server,
  or an OpenCode Go subscription

## 🚀 Installation

Clone this repository into your Anki add-ons folder and build the dependencies:

```bash
git clone https://github.com/iamgianluca/anki-addon.git [your-anki-addons-path]/addons21/anki-addon
cd [your-anki-addons-path]/addons21/anki-addon
./bundle_dependencies.sh  # installs Python 3.13 via uv and vendors pydantic, qdrant-client, and their dependencies
```

## ⚙️ Configuration

1. Start Anki and go to `Tools > Add-ons`
2. Select "anki-addon" and click `Config`
3. Fill in the required settings for your LLM provider.

   **Self-hosted OpenAI-compatible server (default):**
   ```json
   {
     "llm_provider": "openai",
     "openai_host": "your_host_url",
     "openai_port": "your_host_port",
     "openai_model": "your_llm_model"
   }
   ```

   **OpenCode Go subscription** (hosted open coding models, e.g. GLM, Kimi,
   DeepSeek — get an API key from the OpenCode Zen console):
   ```json
   {
     "llm_provider": "opencode_go",
     "opencode_go_api_key": "your_api_key",
     "opencode_go_model": "glm-5.2"
   }
   ```
   Only models served via the `chat/completions` endpoint are supported
   (GLM, Kimi, DeepSeek, MiMo, Grok, Hy3); optional sampling overrides are
   `opencode_go_temperature` and `opencode_go_max_tokens`.
4. Name the notetypes the add-on creates notes with (they use the
   standard "Front"/"Back" and "Text"/"Back Extra" fields):
   ```json
   {
     "basic_notetype_name": "Basic",
     "cloze_notetype_name": "Cloze"
   }
   ```
5. Optional settings (add only if needed for your model):
   ```json
   {
     "openai_mode": "v1/chat/completions",
     "openai_temperature": 0.0,
     "openai_max_tokens": 200,
     "openai_top_p": 0.9,
     "openai_top_k": 40,
     "openai_min_p": 0.05,
     "openai_reasoning": false,
     "openai_preserve_thinking": false
   }
   ```
   (these apply only to the self-hosted `openai` provider. `openai_reasoning`
   enables the model's thinking mode; `openai_preserve_thinking` keeps
   reasoning tokens in the output — useful with Qwen3-style models served
   via llama.cpp)
6. Click `Save`

## 🔍 Usage

### Curate a note's cluster with AI

1. Open a note in the Anki editor
2. Click the "Curate cluster" toolbar button or press `Ctrl+Alt+K`
3. The agent explores related notes and proposes a change set (edits,
   splits, new notes, deletions) — this can take a few minutes
4. Review each proposal in the batch dialog and choose which ones to
   apply; nothing is written to your collection until you approve

### Bulk review flagged notes

1. Flag notes with the orange flag for review
2. Go to `Tools > Improve note using AI` (or press `r`)
3. Step through each note, saving or skipping changes

### Count notes flagged for review

Go to `Tools > Count notes marked for review` (or press `c`) to see how many notes in the current deck are flagged for review.

## 🧪 Development

- `make test` / `make test_slow` — unit tests, or the full suite
  (unit + integration + e2e)
- `make eval` — LLM-in-the-loop capability and regression evals for
  the curation agent (opt-in; see `tests/evals/README.md`)
- `make trace_viewer` — review production curation traces and build a
  failure-mode taxonomy from rejected sessions

For setup, conventions, and architecture, see [CONTRIBUTING.md](CONTRIBUTING.md).

## 🤝 Contributing

Contributions are welcome! Please check the [CONTRIBUTING.md](CONTRIBUTING.md) file and feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

- Anki for their amazing flashcard platform
- The Anki community for their support and feedback