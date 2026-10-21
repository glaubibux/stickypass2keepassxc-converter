# Sticky Password → KeePass / KeePassXC converter

`stickypass2csv.py` converts a Sticky Password text export (`.txt`) into a CSV file you can import into KeePass 2 or KeePassXC.

## Requirements

Python 3. No extra packages are needed.

## 1. Export from Sticky Password

Export your passwords from Sticky Password as a text file (`.txt`). `example.txt` in this folder shows what that file looks like, with fake data.

## 2. Convert

**Easiest way:** put the export next to `stickypass2csv.py` and run:

```
python3 stickypass2csv.py
```

Every `.txt` file in the script's folder is converted into a `.csv` with the same name, e.g. `export.txt` → `export.csv`. Files that are not Sticky Password exports are skipped.

**Single file:**

```
python3 stickypass2csv.py export.txt
python3 stickypass2csv.py export.txt -o passwords.csv
```

### Options

| Option | Meaning |
|---|---|
| `-o FILE`, `--output FILE` | Name of the CSV to write. Only works when you name an input file. |
| `-g NAME`, `--group NAME` | Group the entries are put into (default: `Sticky Password`). |
| `-e ENC`, `--encoding ENC` | Encoding of the export, e.g. `cp1252`. By default the script reads UTF-8 and also detects UTF-16. |

Existing CSV files with the same name are overwritten without asking.

## 3. Import

**KeePassXC:** *Database → Import → CSV File*. This creates a new database. Tick "First line has field names". The columns are mapped automatically; check the preview before finishing.

**KeePass 2:** *File → Import → Generic CSV Importer*. Assign the columns to Title, User Name, Password, URL and Notes. Set Group to "(Ignore)", or use it if you want the entries in their own group.

## How entries are converted

The CSV has the columns `Group, Title, Username, Password, URL, Notes`.

- **Account name** → Title, **Link** → URL, **Login** → Username, **Password** → Password.
- An account with several logins becomes **one entry per login**, all with the same title and URL.
- A **Description** line goes into the notes of the login that follows it.
- Everything under **Comments** (security questions, recovery keys, …) goes into the notes of every login of that account.
- Passwords are copied exactly, including special characters and spaces.
- If the script finds a line it doesn't recognise, it prints a warning and puts the line into the notes, so nothing is lost.

## Security

The export and the CSV contain **all your passwords in plain text**. Once the import has worked, delete both files, and empty the trash too.
