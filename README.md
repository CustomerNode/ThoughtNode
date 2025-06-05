# ThoughtNode

**Personalized AI-Synthesized Insights, Delivered Straight to Your Inbox**

ThoughtNode is a lightweight, open-source Python package that delivers curated, AI-generated insight streams—called *ThoughtNodes*—based on real-time web data. It’s built for Django-based systems but can also run standalone, helping users stay informed without needing to constantly monitor sources themselves, or subscribe to general news digests.

## 👥 Attribution

This project was developed as part of an official internship at **CustomerNode LLC**.

- **Lead Developer**: Colin Calvetti
- **Mentor**: Michael Michael ([michaelcantow@customernode.com](mailto:michaelcantow@customernode.com))
- **Sponsor**: [CustomerNode LLC](https://customernode.com)
- **License**: MIT (see [`LICENSE`](LICENSE))

## ✨ Features

- Modular “ThoughtNodes” for tracking custom topics or themes
- Real-time web data ingestion via lightweight scrapers
- GPT-powered summarization using OpenAI’s API
- Scheduled email delivery via SendGrid (HTML + Markdown fallback)
- Django-native backend with support for async processing
- Minimal, headless-first architecture (UI optional)
- Open-source and extensible for internal or public use

## 📦 Installation (COMING SOON)

Install from PyPI:

```
pip install thoughtnode
```

Or install from source:

```
git clone https://github.com/CustomerNode/thoughtnode.git
cd thoughtnode
pip install -r requirements.txt
```

Set environment variables:

```
OPENAI_API_KEY=your_openai_key
SENDGRID_API_KEY=your_sendgrid_key
DEFAULT_FROM_EMAIL=your_email@example.com
```

Run the application:

```
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## 🧠 System Overview

```
User-defined Node ➝ Source Ingestion ➝ AI Summarization ➝ Email Delivery
```

- **Ingestion**: Sources like RSS feeds, macroeconomic data, and earnings releases via `requests`
- **Synthesis**: Structured prompts passed to OpenAI's GPT API with contextual injection
- **Delivery**: Scheduled emails sent via SendGrid using responsive HTML templates with Markdown fallback
- **Backend**: Django models for ThoughtNodes, delivery logs, and user profiles
- **Scheduling**: Pluggable Celery tasks or Django management commands for periodic execution


## 📄 Documentation

- `docs/setup.md` — Step-by-step setup instructions
- `docs/examples.md` — Sample ThoughtNode configurations and use cases
- `docs/integration.md` — Guidelines for integrating with internal systems
- `docs/contributing.md` — Contribution process, code style, and PR checklist

## 🤝 Contributing

Contributions are welcome! Priority areas include:

- Additional ingestion modules (e.g., new data sources, finance feeds)
- Smarter prompt generation and intent-based logic
- CLI utilities for headless operation
- Improved testing, stability, and error handling

To contribute:

1. Fork the repo
2. Create a feature branch
3. Submit a pull request with a clear description

All contributions will be reviewed and attributed. Thank you for helping improve ThoughtNode!


---

ThoughtNode is both a practical tool and a learning platform—designed to deliver real value while helping engineers build end-to-end systems that span data, AI, and product. Built with clarity and extensibility in mind, it’s ready to deploy, adapt, and grow.

Made with focus and curiosity at CustomerNode.

