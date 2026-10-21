#!/usr/bin/env python3
"""Convert a Sticky Password text export into a CSV for KeePass / KeePassXC.

Usage:
    python3 stickypass2csv.py export.txt [-o passwords.csv]
    python3 stickypass2csv.py            # converts every .txt next to this script

Output columns: Group, Title, Username, Password, URL, Notes
Accounts with several logins become one entry per login.
"""

import argparse
import csv
import sys
from pathlib import Path

HEADER = ["Group", "Title", "Username", "Password", "URL", "Notes"]


def read_text(path, encoding):
    data = Path(path).read_bytes()
    if encoding:
        return data.decode(encoding)
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16")
    return data.decode("utf-8-sig")


def value(line, key):
    """Return the text after 'key:', dropping only the single separating space."""
    rest = line[len(key) + 1:]
    return rest[1:] if rest.startswith(" ") else rest


def parse(text):
    """Yield one dict per account, with a list of logins and the comment text."""
    account = None
    pending_desc = None
    in_comments = False

    for raw in text.splitlines():
        line = raw.rstrip("\r")

        if line.startswith("Account name:"):
            if account:
                yield account
            account = {
                "title": value(line, "Account name").strip(),
                "url": "",
                "logins": [],
                "comments": [],
                "extra": [],
            }
            pending_desc = None
            in_comments = False
            continue

        if account is None:
            continue

        if in_comments:
            account["comments"].append(line)
            continue

        if line.startswith("Link:"):
            account["url"] = value(line, "Link").strip()
        elif line.startswith("Description:"):
            # A description belongs to the login that follows it
            pending_desc = value(line, "Description").strip()
        elif line.startswith("Logins:"):
            pass
        elif line.startswith("Login:"):
            account["logins"].append(
                {"username": value(line, "Login"), "password": "", "desc": pending_desc}
            )
            pending_desc = None
        elif line.startswith("Password:"):
            if not account["logins"]:
                account["logins"].append({"username": "", "password": "", "desc": pending_desc})
                pending_desc = None
            account["logins"][-1]["password"] = value(line, "Password")
        elif line.startswith("Comments:"):
            in_comments = True
            first = value(line, "Comments")
            if first.strip():
                account["comments"].append(first)
        elif line.strip():
            print(f"warning: unknown line in '{account['title']}': {line!r}", file=sys.stderr)
            account["extra"].append(line)

    if account:
        if pending_desc and not account["logins"]:
            account["extra"].append(pending_desc)
        yield account


def to_rows(accounts, group):
    for acc in accounts:
        comments = "\n".join(acc["comments"]).strip("\n")
        logins = acc["logins"] or [{"username": "", "password": "", "desc": None}]
        for login in logins:
            notes = [n for n in (login["desc"], *acc["extra"], comments) if n]
            yield [group, acc["title"], login["username"], login["password"], acc["url"], "\n\n".join(notes)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", nargs="?", help="Sticky Password .txt export (default: every .txt next to this script)")
    ap.add_argument("-o", "--output", help="output CSV (default: input name with .csv)")
    ap.add_argument("-g", "--group", default="Sticky Password", help="group name for all entries")
    ap.add_argument("-e", "--encoding", help="input encoding (default: auto, UTF-8 or UTF-16 by BOM)")
    args = ap.parse_args()

    if args.input:
        inputs = [Path(args.input)]
    else:
        if args.output:
            ap.error("-o/--output needs an input file")
        inputs = sorted(Path(__file__).resolve().parent.glob("*.txt"))
        if not inputs:
            ap.error("no .txt files found next to the script")

    for path in inputs:
        convert(path, Path(args.output) if args.output else path.with_suffix(".csv"), args)


def convert(path, out, args):
    try:
        text = read_text(path, args.encoding)
    except UnicodeDecodeError as e:
        print(f"Skipped {path.name}: cannot decode ({e.reason})", file=sys.stderr)
        return

    rows = list(to_rows(parse(text), args.group))
    if not rows:
        print(f"Skipped {path.name}: no Sticky Password entries found", file=sys.stderr)
        return

    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL)
        w.writerow(HEADER)
        w.writerows(rows)

    print(f"Wrote {len(rows)} entries to {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
