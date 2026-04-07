# pretix-guestlist

A [pretix](https://pretix.eu) plugin that handles DJ and artist guest lists. DJs get personal links they can share with their guests. Guests sign up themselves, and pretix issues the tickets. No manual order creation.

## The problem

If you run a festival, you probably deal with this: every DJ gets a handful of free or discounted tickets for friends. Someone has to track who gets how many, collect names, create orders by hand, and chase people who haven't registered. It gets messy fast.

This plugin moves the whole process into pretix. You add your DJs, set their quotas, and send them an email. They forward links to their guests, guests register themselves, pretix handles the rest.

## What organizers get

- Add DJs one by one or bulk-import via CSV
- Set per-DJ quotas for half-price and free tickets (full price is unlimited)
- Send invitation emails to all DJs at once
- Track guest status: invited, registered, checked in
- Export the full guest list as CSV
- Automatic reminder emails 7 and 2 days before the event

## What DJs get

- An email with up to 3 shareable links (one per ticket type: full price, half price, free)
- A personal dashboard to see their guests and resend invitations
- No pretix account needed -- token-based links, no login

## What guests see

- They open the link the DJ shared and enter their email
- They get a registration link by email, fill in their name
- Free tickets (0 EUR) arrive instantly as PDF; paid tickets go through normal pretix checkout with a one-time voucher

## Requirements

- Pretix >= 2024.1.0
- Python >= 3.9

## Installation

The plugin needs to be installed in the same Python environment where pretix runs. That depends on your setup:

**If pretix runs in Docker (most common):**

```bash
# Open a shell inside your pretix container
docker exec -it <your-pretix-container> bash

# Install the plugin
pip install git+https://github.com/philiponboard/pretix-guestlist.git

# Run database migrations
python -m pretix migrate

# Then restart the container so pretix picks up the new plugin
```

You need to do this for every container that runs pretix code -- typically the web server and the Celery worker. If you use docker-compose, that usually means the `pretix` and `celery` services.

Note: the plugin will be lost when you rebuild the container image. To make it permanent, add the `pip install` line to your Dockerfile.

**If pretix runs directly on a server (without Docker):**

```bash
# Activate the same virtualenv pretix uses, then:
pip install git+https://github.com/philiponboard/pretix-guestlist.git
python -m pretix migrate

# Restart pretix (e.g. systemctl restart pretix-web pretix-worker)
```

**After installation**, go to your event in the pretix admin panel: **Settings > Plugins** and enable "Guest List".

## Setup

1. Create 3 products in your event for the guest list (e.g. "GL Full Price", "GL Half Price", "GL Free"). Set the price for free tickets to 0 EUR.
2. In **Guest List > Settings**, assign each product to its ticket type.
3. Enable "Hide products from shop" so these products only show up through guest list links, not in your public shop.
4. Add DJs manually or use the CSV bulk import (there's a template you can download).
5. Hit "Send all invitations" and you're set.

## How the flow works

1. You add DJs and set their quotas
2. Each DJ gets an email with up to 3 links (one per ticket type) plus a dashboard link
3. The DJ forwards the appropriate link to each guest
4. The guest opens the link, enters their email, and gets a personal registration link
5. The guest fills in their name:
   - Free ticket? Order is created on the spot, ticket PDF sent by email
   - Paid ticket? Guest is redirected to the pretix checkout with a one-time voucher that unlocks the hidden product
6. You can track everything in the pretix admin and export it as CSV

## Development

The repo includes a Docker-based dev setup:

```bash
cd docker-dev-setup
make up              # start containers
make restart         # restart after code changes
make makemigrations  # create new migrations
make migrate         # apply migrations
make shell           # bash inside the container
```

Tests:

```bash
docker compose exec pretix python -m pytest /plugin/pretix_guestlist/tests/ -v
```

## License

Apache 2.0 -- see [LICENSE](LICENSE).
