# NameSwiper

A web app for parents to collaboratively pick a baby name. Couples (or small groups) independently swipe through name candidates, then fine-tune the results together through scoring — ending up with a ranked list of names everyone agreed on.

---

## Core Flow

### 1. Swiping (independent)
Each group member independently swipes through name groups one at a time, Tinder-style:
- **Like** — add to your liked names
- **Dislike** — remove from consideration
- **Skip** — defer the name to revisit later

### 2. Scoring (collaborative)
Once swiping is done, names that **every group member liked** move to the scoring phase. Each member:
- Rates the name group **1–5 stars**
- **Checkmarks their preferred spelling variants** within the group (e.g. prefer "Michael" over "Mikael")
- Optionally leaves a **comment** for the group

### 3. Results
A ranked list of all mutually liked names, ordered by average score across the group.

All three views (swiping, scoring, results) include a **filter by sex**.

---

## Name Data Model

A "name" in NameSwiper is not a single string — it is a **name group**: a set of spelling variants that are considered equivalent.

- Michael and Mikael → same group (male)
- Ruben and Reuben → same group (male)
- Michael and Michaela → **different groups** (different sex)

Sex is an attribute of the name group, not of individual variants. During swiping, all variants in the group are displayed together. Matching between group members is **all-or-nothing at the group level** — if two people liked the same group via different variants, it still counts as a match.

---

## Groups

- Any registered user can create a group.
- The creator becomes the **group owner**.
- Other users join via a **unique invite link**. A logged-in user who opens the link sees a confirmation form showing which group they are joining before they accept.
- The group owner can **remove members**. Ownership is non-transferable.
- No hard cap on group size; UI is optimized for ≤ 4 members.

---

## User Features

- **Retroactive editing**: users can go back and change any of their swipes or scores at any time.
- **Sex filter**: available on all main views to narrow names down to a specific sex (useful once the parents know).

---

## Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Backend | Django (Python) | Batteries-included auth, ORM, admin; familiar stack |
| Database | SQLite | Zero-install; sufficient for small local user base |
| Frontend | Django templates + vanilla JS | No build step, no Node.js required |
| Swipe UI | CDN-loaded JS library (e.g. Hammer.js) | Touch/drag gestures without a frontend framework |
| Layout | Responsive CSS | Must work on mobile screens; swiping is a primary mobile interaction |

### Development Setup

A `venv` virtual environment lives in the `venv/` directory at the project root. Always activate it before running any Python commands:

```bash
# Windows (PowerShell)
venv\Scripts\Activate.ps1

# Windows (bash/Git Bash)
source venv/Scripts/activate

# macOS / Linux
source venv/bin/activate
```

All dependencies are tracked in `requirements.txt`. After installing or upgrading any package, update it:

```bash
pip freeze > requirements.txt
```

To install dependencies in a fresh environment:

```bash
pip install -r requirements.txt
```

### Running the dev server

```bash
source venv/Scripts/activate   # Windows bash / Git Bash
python manage.py runserver 0.0.0.0:8000
```

Open `http://localhost:8000` in a browser. Other devices on the local network can connect via `http://<your-ip>:8000`.

First-time setup:

```bash
python manage.py migrate
python manage.py loaddata dummy_names   # loads the 23 dummy name groups
python manage.py createsuperuser        # optional – for Django admin access
```

### Current phase constraints
- Maximum ~2 users on a local network
- No scalability or parallel-processing optimizations needed yet
- Name dataset is a small dummy set; full dataset generation is a later workstream

---

## Project Status

- [x] Project setup (Django app, SQLite, basic auth)
- [x] Data model (name groups, variants, sex, swipes, scores, groups, memberships)
- [x] Dummy name dataset (23 name groups across male / female / neutral)
- [x] Group creation & invite link flow
- [x] Swiping UI (swipe gesture + buttons + keyboard shortcuts)
- [x] Scoring UI (stars, variant checkmarks, comments)
- [x] Results view (ranked by average score)
- [x] Retroactive swipe/score editing
- [x] Sex filter across all views
- [ ] Full name dataset (later workstream)
