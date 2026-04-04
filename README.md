# pretix-guestlist

A [pretix](https://pretix.eu) plugin for managing DJ and artist guest lists. Assign individual quotas, let guests self-register via personal links, and issue real pretix tickets.

## Features

- **3 ticket types**: Full Price, Half Price, and Free — each mapped to a pretix product
- **Per-DJ quotas**: Configurable limits for half-price and free tickets
- **DJ dashboard**: Personal link where DJs invite guests and track their status
- **Guest self-registration**: Guests receive a personal link to complete registration
- **Automatic ticketing**: Free tickets issued instantly; paid tickets redirect to pretix checkout via voucher
- **Hidden products**: Guest list products are automatically hidden from the public shop
- **QR codes**: DJ invitation emails include a QR code for their dashboard
- **Reminder emails**: Automatic reminders 7 days and 2 days before the event
- **CSV export**: Export the full guest list from the pretix admin
- **Translations**: German and English

## Requirements

- Pretix >= 2024.1.0
- Python >= 3.9

## Installation

```bash
pip install git+https://github.com/philiponboard/pretix-guestlist.git
```

Restart pretix after installation. Then enable the plugin under **Settings > Plugins** in your event.

## Configuration

1. **Create 3 products** in your event for the guest list ticket types (e.g. "GL Full Price", "GL Half Price", "GL Free")
2. Go to **Guest List > Settings** and assign the 3 products
3. Enable "Hide products from shop" so they are only accessible via guest list links
4. Go to **Guest List** and add your DJs with name, email, and quota settings
5. Click "Send invitation" to email each DJ their personal dashboard link

## How it works

1. Admin creates products and adds DJs with individual quotas
2. DJ receives an invitation email with a link to their personal dashboard
3. DJ invites guests by entering email addresses and selecting a ticket type
4. Guest receives an email with a personal registration link
5. Guest fills in their name and email:
   - **Free ticket** (0 EUR): Order created immediately, ticket sent by email
   - **Paid ticket**: Redirected to pretix checkout with a pre-configured voucher
6. Admin can track all guests and export the list as CSV

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
