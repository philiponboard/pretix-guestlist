# pretix-guestlist

A [pretix](https://pretix.eu) plugin for managing DJ and artist guest lists at festivals and events. Assign individual quotas, let guests self-register via personal links, and issue real pretix tickets — all without manual order creation.

## What it does

Managing guest lists for DJs and artists is tedious: tracking who gets how many free or discounted tickets, collecting names, creating orders manually, and chasing people who haven't registered. This plugin automates the entire process inside pretix.

**For event organizers:**
- Create and manage DJ/artist accounts with individual ticket quotas
- Bulk-import DJs via CSV upload instead of adding them one by one
- Send invitation emails to all DJs at once
- Track guest registration status (invited / registered / checked in)
- Export the complete guest list as CSV
- Automatic reminder emails to unregistered guests (7 days and 2 days before the event)

**For DJs and artists:**
- Receive shareable links per ticket type (Full Price, Half Price, Free) to forward to guests
- Personal dashboard to view guest status and resend invitations
- No pretix account needed — everything works via token-based links

**For guests:**
- Simple self-registration: enter email via the link the DJ shared, then complete registration via a personal link
- Free tickets (0 EUR) are issued instantly with a ticket PDF by email
- Paid tickets redirect to the standard pretix checkout via a one-time voucher

## Features

- **3 ticket types**: Full Price, Half Price, and Free — each mapped to a pretix product
- **Per-DJ quotas**: Configurable limits for half-price and free tickets (full price is unlimited)
- **Shareable guest links**: DJs get up to 3 links (one per ticket type) to share with their guests
- **Guest self-sign-up**: Guests enter their email via the shared link and receive a registration email
- **DJ dashboard**: Personal page where DJs see their guest list and can resend invitations
- **Guest self-registration**: Guests complete registration (name, email) via their personal link
- **Automatic ticketing**: Free tickets issued instantly; paid tickets redirect to pretix checkout via one-time voucher
- **Hidden products**: Guest list products are automatically hidden from the public shop
- **CSV bulk import**: Upload a CSV file to import multiple DJs at once (with template download)
- **CSV export**: Export the full guest list from the pretix admin
- **Duplicate protection**: Same email cannot sign up twice per DJ
- **Reminder emails**: Automatic reminders 7 days and 2 days before the event
- **Translations**: German and English

## Requirements

- Pretix >= 2024.1.0
- Python >= 3.9

## Installation

```bash
pip install git+https://github.com/philiponboard/pretix-guestlist.git
```

After installation, restart pretix and run migrations:

```bash
python -m pretix migrate
```

Then enable the plugin in your event under **Settings > Plugins > Guest List**.

## Configuration

1. **Create 3 products** in your event for the guest list ticket types (e.g. "GL Full Price", "GL Half Price", "GL Free"). Set the price to 0 EUR for free tickets.
2. Go to **Guest List > Settings** and assign the 3 products to their ticket types.
3. Enable "Hide products from shop" so they are only accessible via guest list links.
4. Add DJs manually or use **CSV bulk import** (download the template first).
5. Click **Send all invitations** to email every DJ their personal links.

## How it works

1. **Admin** creates products, configures the plugin, and adds DJs with individual quotas
2. **DJ** receives an invitation email containing:
   - Up to 3 shareable links (one per configured ticket type) to forward to guests
   - A personal dashboard link to manage their guest list
3. **Guest** opens the link the DJ shared, enters their email, and receives a registration email
4. **Guest** opens the registration link and fills in their name:
   - **Free ticket** (0 EUR): Order created immediately, ticket sent by email
   - **Paid ticket**: Redirected to pretix checkout with a one-time voucher
5. **Admin** tracks all guests via the pretix control panel and can export the list as CSV

## Development

Clone the repository and use the Docker dev setup:

```bash
cd docker-dev-setup
make up              # Start containers
make restart         # Restart after code changes
make makemigrations  # Create new migrations
make migrate         # Apply migrations
make shell           # Bash in container
```

Run tests:

```bash
docker compose exec pretix python -m pytest /plugin/pretix_guestlist/tests/ -v
```

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.
