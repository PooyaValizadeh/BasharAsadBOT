# BasharAsadBOT

A Telegram-style game bot built with **Balethon**. The project keeps its bot source, runtime data, and setup documentation in separate locations.

## Repository layout

```text
BasharAsadBOT/
├── src/
│   └── basharasad_bot.py   # Main bot application
├── data/                   # Runtime database and JSON inventories
├── .gitignore
├── requirements.txt
├── LICENSE
└── README.md
```

## Requirements

- Python
- Balethon

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Configuration

Before running the bot, open `src/basharasad_bot.py` and replace the `TOKEN` placeholder in `Client("TOKEN")` with your bot token.

If payment features are used, configure `PROVIDER_TOKEN` as required by your payment provider. Do not commit real bot or provider tokens to GitHub.

## Run

Run the command from the repository root so the project uses the expected `data/` directory:

```bash
python src/basharasad_bot.py
```

## Runtime data

The bot creates and stores its SQLite database and JSON inventory files in `data/`:

- `bashar.db`
- `miner_inventory.json`
- `missile_inventory.json`
- `defense_inventory.json`

These are runtime files and are intentionally excluded from Git. Back them up separately if you need to preserve bot progress.

## License

See [LICENSE](LICENSE).
