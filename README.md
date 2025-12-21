# Library Management System (Tkinter)

This is a simple desktop app to manage a small library. It works with buttons and tables, so a 10-year-old can use it.

### Main Window

![](https://imgur.com/L69lVpz.png)

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

## What you can do

- Add books (ID, title, author, category).
- Edit books or remove them.
- See all books in a table, sorted by Book ID.
- Check out a book to a member (choose a member or add a new one on the spot).
- Return a book.
- Members page: add, update, delete members (cannot delete if they still have a book).
- Automatic member ID suggestions like member-1, member-2, member-3...
- Overdue alert: see which books are late.
- Analytics: top borrowed books, active and total loans.
- Export books to CSV, export everything to JSON, and import JSON backups.
- Data is saved automatically to `library_data.json` (created next to the app file).

## How to run

1. Make sure you have Python 3 installed.
2. Open a terminal in this folder.
3. Run:
   ```bash
   python "Library Management System using Python.py"
   ```
4. The window opens centered on your screen.

## How to use

- **Add Book**: Click Add Book, fill the fields, Save.
- **Edit Book**: Select a row, click Edit Book, change fields, Save.
- **Remove Book**: Select a row, click Remove Book.
- **Check Out**: Select a book, click Check Out. Pick an existing member or type a new ID/name/email and click Confirm. Days defaults to 14.
- **Return**: Select a book, click Return.
- **Members**: Click Members. You can add/update with the form, delete selected (only if no active loans). IDs auto-suggest in the form.
- **Overdue**: Shows all late books.
- **Analytics**: Shows most borrowed books and loan counts.
- **Export CSV**: Saves books table to a CSV file.
- **Export JSON**: Saves books, members, and loans to JSON.
- **Import JSON**: Load a JSON backup (merges data).

## Tips

- Book ID must be unique.
- Member ID must be unique. Use the suggested ID if unsure.
- Sorting: Book table is always sorted by Book ID (numbers first in order).
- If you cannot delete a member, return their books first.
- Keep `library_data.json` safe; it holds your data.

## File map

- Main app: [Library Management System using Python.py](Library%20Management%20System%20using%20Python.py)
- Data file (auto-created): `library_data.json`

Enjoy managing your library!
