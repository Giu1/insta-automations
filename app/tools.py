"""Command-line helpers for people who maintain the config files.

    python -m app.tools check                 validate config files and tokens
    python -m app.tools whoami                show the Instagram account behind each token
    python -m app.tools try "texto aqui"      preview which reply a comment/message would get
    python -m app.tools posts                 list scheduled posts and what already went out
    python -m app.tools publish-now <post-id> publish one post immediately (for testing)
    python -m app.tools subscribe             (re)subscribe webhooks for every brand
"""

from __future__ import annotations

import sys
from datetime import timezone

from app.config import ConfigError, load_brands, load_posts, load_replies
from app.db import PublishedPost, SessionLocal, init_db
from app.instagram import InstagramError
from app.replies import decide_comment, decide_message
from app.tokens import client_for, token_for

OK, BAD = "  OK ", "  !! "


def cmd_check() -> int:
    problems = 0
    try:
        brands = load_brands()
        print(OK, f"brands.yaml: {', '.join(brands)}")
    except ConfigError as exc:
        print(BAD, exc)
        return 1
    for brand in brands.values():
        try:
            r = load_replies(brand.slug)
            print(OK, f"replies.yaml [{brand.slug}]: {len(r.comments)} comment rules, {len(r.messages)} message rules")
        except ConfigError as exc:
            problems += 1
            print(BAD, exc)
        if not token_for(brand):
            problems += 1
            print(BAD, f"[{brand.slug}] no token. Put it in .env as {brand.token_env}=...")
        else:
            try:
                me = client_for(brand).me()
                print(OK, f"[{brand.slug}] token works -> @{me.get('username')} (id {me.get('user_id')})")
            except InstagramError as exc:
                problems += 1
                print(BAD, f"[{brand.slug}] token rejected by Instagram: {exc}")
    try:
        posts = load_posts()
        print(OK, f"posts.yaml: {len(posts)} posts")
    except ConfigError as exc:
        problems += 1
        print(BAD, exc)
    print("\nAll good." if not problems else f"\n{problems} problem(s) to fix.")
    return 1 if problems else 0


def cmd_whoami() -> int:
    for brand in load_brands().values():
        try:
            me = client_for(brand).me()
            print(f"{brand.slug}: @{me.get('username')}  instagram_id={me.get('user_id')}  instagram_app_user_id={me.get('id')}")
        except InstagramError as exc:
            print(f"{brand.slug}: {exc}")
    return 0


def cmd_try(text: str) -> int:
    for brand in load_brands().values():
        print(f"[{brand.slug}]")
        for kind, fn in (("comment", decide_comment), ("message", decide_message)):
            d = fn(brand, text)
            print(f"  as {kind}: " + (f"rule '{d.rule}' [{d.language}] -> {d.text}" if d else "no reply"))
    return 0


def cmd_posts() -> int:
    init_db()
    with SessionLocal() as session:
        for p in load_posts():
            done = session.get(PublishedPost, p.id)
            brand = load_brands()[p.brand]
            when = p.publish_at.astimezone(brand.tz).strftime("%Y-%m-%d %H:%M")
            state = "waiting" if not done else (f"published {done.media_id}" if done.status == "published" else f"FAILED: {done.error}")
            print(f"{when}  {p.brand:<16} {p.type:<6} {p.id:<28} {state}")
    return 0


def cmd_publish_now(post_id: str) -> int:
    from app.db import record_post
    from app.publisher import publish_post

    init_db()
    post = next((p for p in load_posts() if p.id == post_id), None)
    if not post:
        print(f"No post with id '{post_id}' in posts.yaml")
        return 1
    status, media_id, error = publish_post(post)
    with SessionLocal() as session:
        record_post(session, post.id, post.brand, status, media_id, error)
    print(status, media_id or error)
    return 0 if status == "published" else 1


def cmd_subscribe() -> int:
    for brand in load_brands().values():
        try:
            print(brand.slug, client_for(brand).subscribe_webhooks())
        except InstagramError as exc:
            print(brand.slug, "failed:", exc)
    return 0


def main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # accents print correctly in the Windows console
    init_db()
    cmd = argv[0] if argv else "help"
    try:
        if cmd == "check":
            return cmd_check()
        if cmd == "whoami":
            return cmd_whoami()
        if cmd == "try" and len(argv) > 1:
            return cmd_try(" ".join(argv[1:]))
        if cmd == "posts":
            return cmd_posts()
        if cmd == "publish-now" and len(argv) > 1:
            return cmd_publish_now(argv[1])
        if cmd == "subscribe":
            return cmd_subscribe()
    except ConfigError as exc:
        print(BAD, exc)
        return 1
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
