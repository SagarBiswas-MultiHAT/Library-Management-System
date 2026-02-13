# Library Management System (Python + Tkinter)

<div align="right">

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
&nbsp;
[![License](https://img.shields.io/github/license/SagarBiswas-MultiHAT/Library-Management-System)](https://github.com/SagarBiswas-MultiHAT/Library-Management-System/blob/main/LICENSE)
&nbsp;
[![Last commit](https://img.shields.io/github/last-commit/SagarBiswas-MultiHAT/Library-Management-System)](https://github.com/SagarBiswas-MultiHAT/Library-Management-System/commits)
&nbsp;
[![Issues](https://img.shields.io/github/issues/SagarBiswas-MultiHAT/Library-Management-System)](https://github.com/SagarBiswas-MultiHAT/Library-Management-System/issues)

</div>

This is a small “library app” you run on your computer.

Think of it like a digital notebook where you can:

- keep a list of books,
- keep a list of members (people),
- lend books out (check out),
- take books back (return),
- and see what’s overdue (late).

It also has a **login screen** with **two-step sign-in**:

1. password (saved as a SHA‑256 hash)
2. a changing 6‑digit code from an Authenticator app (TOTP)

---

## Pictures (what you will see)

### Sign-In Window

<div align="center">

![](https://imgur.com/SmDFHok.png)

</div>

### Main Window

![](https://imgur.com/AiqL3QJ.png)

### Add Book

![](https://imgur.com/MM0U3p2.png)

### Edit Book

![](https://imgur.com/e8t9nQ6.png)

### Check Out

![](https://imgur.com/Mv3voMC.png)

### Members

![](https://imgur.com/7BuqpGx.png)

### Analytics

![](https://imgur.com/pQmxJhh.png)

---

## What this app can do (features)

### Books

- Add a book (ID, title, author, category)
- Edit a book (title/author/category)
- Remove a book
- See all books in a table
- Search books (by ID, title, author, or category)
- Filter books: All / Available / Checked Out / Overdue

### Borrowing (Loans)

- Check out a book to a member
- Return a book
- Due date is stored and “Overdue” is shown if it’s late
- Tracks how many times a book was borrowed

### Members

- Add / update members (ID, name, email)
- Delete members (but only if they have **no active loans**)
- Suggests member IDs like `member-1`, `member-2`, … so you don’t have to think

### Reports / Extras

- Overdue report (shows late books)
- Analytics (top borrowed books, active loans, total loans)
- Export books list to CSV
- Export everything to JSON
- Import a JSON backup (it merges data)

---

## How it saves your work (important)

When you add books or members, the app saves automatically.

- Your library data is stored in `library_data.json`
- Your login info is stored in `library_credentials.json`

Both files live in the same folder as the Python app.

---

## How to run (Windows, easy)

1. Install **Python 3**.
2. Open this project folder.
3. In the address bar (top of File Explorer), type `powershell` and press Enter.
4. Run this command:

   ```powershell
   python "main.py"
   ```

5. The Sign-In window opens.

Default login (unless you changed it):

- Username: `admin`
- Password: `your-new-password`

You must also enter the **6-digit authenticator code** (see next section).

---

## Two-step sign-in (Authenticator / TOTP) — explained

The app asks for a 6-digit code because it wants to be extra safe.

That 6-digit number comes from an app like **Google Authenticator**.
It changes about every 30 seconds.

### Step 1: Find your secret key

Open `library_credentials.json`.
You will see something like:

- `username`: who you are
- `password_hash`: a long hash (not the real password)
- `totp_secret`: this is the **secret key** for the authenticator app

### Step 2: Add the secret to Google Authenticator (enroll)

Google Authenticator (similar in other apps):

1. Open Google Authenticator
2. Tap `+`
3. Choose **Enter a setup key** (or “Manual entry”)
4. Fill in:
   - Account name: `Library (admin)` (or anything you want)
   - Key / Secret: paste your `totp_secret`
   - Type: **Time based**
5. Save

Now the app will show a changing **6-digit code**.

### Step 3: Sign in

In the login window:

1. Type your username
2. Type your password
3. Type the current 6-digit code from your authenticator
4. Press **Continue**

If the code says “expired”, just wait for the next one and try again.

---

## Changing the password (SHA‑256 hashing)

The app does **not** store your password as normal text.
Instead it stores a **SHA‑256 hash** (a one-way “scrambled” version).

That means:

- You can change the password
- But you must store the **hash**, not the real password

### Option A (what you said you do): use the KeyCDN SHA‑256 tool

You said you use:
https://tools.keycdn.com/sha256-online-generator

Steps:

1. Type your new password into the website
2. Copy the SHA‑256 output
3. Open `library_credentials.json`
4. Replace the value of `password_hash` with the new hash
5. Save the file and restart the app

### Option B (offline): generate SHA‑256 using Python

In PowerShell, run:

```powershell
python -c "import hashlib; print(hashlib.sha256('your-new-password'.encode('utf-8')).hexdigest())"
```

Copy the printed hash into `password_hash`.

Safety note: putting passwords into websites is not ideal for real security. For learning/projects it’s okay, but for real use, prefer the offline Python method.

---

## How to use the app (quick guide)

- **Add Book**: click `Add Book` → fill fields → `Save`
- **Edit Book**: click a row → `Edit Book` → change fields → `Save`
- **Remove Book**: click a row → `Remove Book`
- **Check Out**: click a book → `Check Out` → pick a member OR add a new one → choose days (default 14) → `Confirm`
- **Return**: click a checked-out book → `Return`
- **Members**: click `Members` to add/update/delete members
- **Overdue**: click `Overdue` to see late books
- **Analytics**: click `Analytics` to see top borrowed + loan counts
- **Export CSV**: saves the book table as a `.csv` file
- **Export JSON**: saves books + members + loans as `.json`
- **Import JSON**: loads a backup `.json` and merges it

---

## Common problems (and easy fixes)

- “Invalid or expired 6-digit code.”

  - Wait for the next code in your authenticator and try again
  - Make sure your computer time is correct

- “Authenticator not set. Ask an admin to add totp_secret.”

  - Make sure your user in `library_credentials.json` has a `totp_secret`

- “Member has active loans; return books first”

  - Return their books, then delete the member

- “Enter username, password, and code.”
  - Make sure you filled in all 3 boxes on the Sign-In screen

---

## Tips: Make a Windows EXE (powershell)

If you want, you can turn this app into a `.exe` file so you can open it like a normal program.

### 1) Install PyInstaller

Run these in PowerShell:

```powershell
py -m pip install --upgrade pip
py -m pip install pyinstaller
```

Verify it installed:

```powershell
py -m PyInstaller --version
```

### 2) Build the one-file EXE (no console window)

Go to the folder that contains your `.py` file:

```powershell
cd "C:\path\to\your\project"
```

Then run:

```powershell
py -m PyInstaller --onefile --windowed --name "Library Management System" "main.py"
```

After it finishes, your EXE will be here:

```text
dist\Library Management System.exe
```

**Then change the password_hash AND totp_secret from dist\library_credentials.json**

---

## Files in this project

- Main app: [main.py](Library%20Management%20System%20using%20Python.py)
- Saves your library data: `library_data.json`
- Stores login + 2FA secret: `library_credentials.json`
- Tiny helper example: `SHA-256 hash.py`

---
