import csv
import json
import re
import tkinter as tk
from dataclasses import dataclass, asdict
from datetime import date, timedelta
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Dict, List, Optional, Union


WindowLike = Union[tk.Tk, tk.Toplevel]

# def center_window(root: tk.Tk, width: int, height: int) -> None:
#     """Set window size and center it on the current screen."""

def center_window(root: WindowLike, width: int, height: int) -> None:
    """Set window size and center it on the current screen (Tk or Toplevel)."""
    root.update_idletasks()
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    x = max((screen_w - width) // 2, 0)
    y = max((screen_h - height) // 2, 0)
    
    y = y-42  # adjust for taskbar

    root.geometry(f"{width}x{height}+{x}+{y}")


# Data layer
@dataclass
class Book:
    book_id: str
    title: str
    author: str
    category: str = "General"
    available: bool = True
    borrower: Optional[str] = None
    due_date: Optional[str] = None  # stored as ISO string
    times_borrowed: int = 0

    @property
    def due_date_obj(self) -> Optional[date]:
        return date.fromisoformat(self.due_date) if self.due_date else None


@dataclass
class Member:
    member_id: str
    name: str
    email: str = ""


@dataclass
class Loan:
    loan_id: str
    book_id: str
    member_id: str
    borrower_name: str
    start_date: str
    due_date: str
    returned_at: Optional[str] = None


class LibraryRepository:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._books: Dict[str, Book] = {}
        self._members: Dict[str, Member] = {}
        self._loans: List[Loan] = []
        self._next_loan_id: int = 1
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            # Migration: old format was just books dict
            if isinstance(data, dict) and "books" not in data:
                for book_id, payload in data.items():
                    self._books[book_id] = Book(**payload)
            else:
                for book_id, payload in data.get("books", {}).items():
                    self._books[book_id] = Book(**payload)
                for member_id, payload in data.get("members", {}).items():
                    self._members[member_id] = Member(**payload)
                for loan_payload in data.get("loans", []):
                    self._loans.append(Loan(**loan_payload))
                self._next_loan_id = data.get("next_loan_id", 1)
        except Exception as exc:  # keep UI alive on malformed data
            messagebox.showerror("Error", f"Failed to load data: {exc}")

    def _persist(self) -> None:
        serialized = {
            "books": {book_id: asdict(book) for book_id, book in self._books.items()},
            "members": {member_id: asdict(member) for member_id, member in self._members.items()},
            "loans": [asdict(loan) for loan in self._loans],
            "next_loan_id": self._next_loan_id,
        }
        self.path.write_text(json.dumps(serialized, indent=2), encoding="utf-8")

    def upsert(self, book: Book) -> None:
        self._books[book.book_id] = book
        self._persist()

    def delete(self, book_id: str) -> None:
        self._books.pop(book_id, None)
        self._persist()

    def get(self, book_id: str) -> Optional[Book]:
        return self._books.get(book_id)

    def list_all(self) -> List[Book]:
        return list(self._books.values())

    def upsert_member(self, member: Member) -> None:
        self._members[member.member_id] = member
        self._persist()

    def get_member(self, member_id: str) -> Optional[Member]:
        return self._members.get(member_id)

    def list_members(self) -> List[Member]:
        return list(self._members.values())

    def delete_member(self, member_id: str) -> None:
        self._members.pop(member_id, None)
        self._persist()

    def add_loan(self, loan: Loan) -> None:
        self._loans.append(loan)
        self._next_loan_id += 1
        self._persist()

    def close_loan(self, book_id: str) -> None:
        for loan in reversed(self._loans):
            if loan.book_id == book_id and loan.returned_at is None:
                loan.returned_at = date.today().isoformat()
                break
        self._persist()

    def list_loans(self) -> List[Loan]:
        return list(self._loans)

    def next_loan_id(self) -> str:
        return str(self._next_loan_id)

    def import_data(self, data: dict) -> None:
        # Merge incoming data with current state; new data wins on conflicts
        for book_id, payload in data.get("books", {}).items():
            self._books[book_id] = Book(**payload)
        for member_id, payload in data.get("members", {}).items():
            self._members[member_id] = Member(**payload)
        for loan_payload in data.get("loans", []):
            self._loans.append(Loan(**loan_payload))
        self._next_loan_id = max(self._next_loan_id, data.get("next_loan_id", self._next_loan_id))
        self._persist()


# Service layer
class LibraryService:
    def __init__(self, repo: LibraryRepository):
        self.repo = repo

    @staticmethod
    def _book_sort_key(book: Book):
        bid = book.book_id.strip()
        if bid.isdigit():
            return (0, int(bid))
        return (1, bid.lower())

    def add_book(self, book_id: str, title: str, author: str, category: str) -> None:
        book_id = book_id.strip()
        title = title.strip()
        author = author.strip()
        category = category.strip() or "General"
        if not book_id or not title or not author:
            raise ValueError("Book ID, title, and author are required")
        if self.repo.get(book_id):
            raise ValueError("A book with this ID already exists")
        self.repo.upsert(Book(book_id=book_id, title=title, author=author, category=category))

    def remove_book(self, book_id: str) -> None:
        if not self.repo.get(book_id):
            raise ValueError("Book not found")
        self.repo.delete(book_id)

    def add_member(self, member_id: str, name: str, email: str = "") -> None:
        member_id = member_id.strip()
        name = name.strip()
        email = email.strip()
        if not member_id or not name:
            raise ValueError("Member ID and name are required")
        self.repo.upsert_member(Member(member_id=member_id, name=name, email=email))

    def remove_member(self, member_id: str) -> None:
        member = self.repo.get_member(member_id)
        if not member:
            raise ValueError("Member not found")
        active_loans = [l for l in self.repo.list_loans() if l.member_id == member_id and l.returned_at is None]
        if active_loans:
            raise ValueError("Member has active loans; return books first")
        self.repo.delete_member(member_id)

    def checkout(self, book_id: str, member_id: str, days: int) -> None:
        book = self.repo.get(book_id)
        if not book:
            raise ValueError("Book not found")
        if not book.available:
            raise ValueError("Book is already checked out")
        member = self.repo.get_member(member_id)
        if not member:
            raise ValueError("Member not found")
        book.available = False
        book.borrower = member.name
        book.due_date = (date.today() + timedelta(days=days)).isoformat()
        book.times_borrowed += 1
        self.repo.upsert(book)
        self.repo.add_loan(Loan(
            loan_id=self.repo.next_loan_id(),
            book_id=book.book_id,
            member_id=member.member_id,
            borrower_name=member.name,
            start_date=date.today().isoformat(),
            due_date=book.due_date,
        ))

    def return_book(self, book_id: str) -> None:
        book = self.repo.get(book_id)
        if not book:
            raise ValueError("Book not found")
        if book.available:
            raise ValueError("Book is already available")
        book.available = True
        book.borrower = None
        book.due_date = None
        self.repo.upsert(book)
        self.repo.close_loan(book_id)

    def list_books(self) -> List[Book]:
        #  sorted by book_id (ascending, case-insensitive) when listed
        return sorted(self.repo.list_all(), key=self._book_sort_key)

    def list_members(self) -> List[Member]:
        return self.repo.list_members()

    def get_member(self, member_id: str) -> Optional[Member]:
        return self.repo.get_member(member_id.strip())

    # Add automatic member ID suggestions:
    def next_member_id(self) -> str:
        pattern = re.compile(r"^member-(\d+)$", re.IGNORECASE)
        used = set()
        for member in self.repo.list_members():
            match = pattern.match(member.member_id.strip())
            if match:
                used.add(int(match.group(1)))
        candidate = 1
        while candidate in used:
            candidate += 1
        return f"member-{candidate}"

    def list_loans(self) -> List[Loan]:
        return self.repo.list_loans()

    def status_of(self, book: Book) -> str:
        if book.available:
            return "Available"
        if book.due_date_obj and book.due_date_obj < date.today():
            return "Overdue"
        return "Checked Out"

    def overdue_books(self) -> List[Book]:
        return [b for b in self.repo.list_all() if self.status_of(b) == "Overdue"]

    def top_borrowed(self, limit: int = 5) -> List[Book]:
        return sorted(self.repo.list_all(), key=lambda b: b.times_borrowed, reverse=True)[:limit]

    def export_books_csv(self, path: Path) -> None:
        rows = self.repo.list_all()
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["book_id", "title", "author", "category", "status", "borrower", "due_date", "times_borrowed"])
            for b in rows:
                writer.writerow([
                    b.book_id,
                    b.title,
                    b.author,
                    b.category,
                    self.status_of(b),
                    b.borrower or "",
                    b.due_date or "",
                    b.times_borrowed,
                ])

    def export_json(self, path: Path) -> None:
        data = {
            "books": {b.book_id: asdict(b) for b in self.repo.list_all()},
            "members": {m.member_id: asdict(m) for m in self.repo.list_members()},
            "loans": [asdict(l) for l in self.repo.list_loans()],
            "next_loan_id": self.repo._next_loan_id,
        }
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def import_json(self, path: Path) -> None:
        data = json.loads(path.read_text(encoding="utf-8"))
        self.repo.import_data(data)


# UI layer
class LibraryManagementGUI(ttk.Frame):
    def __init__(self, root: tk.Tk):
        super().__init__(root, padding=12)
        self.root = root
        self.root.title("Library Management System")
        self.repo = LibraryRepository(Path("library_data.json"))
        self.service = LibraryService(self.repo)
        self.search_var = tk.StringVar()
        self.filter_var = tk.StringVar(value="All")
        self.status_var = tk.StringVar()
        self._configure_style()
        self._build_header()
        self._build_table()
        self._build_actions()
        self._refresh_table()
        self.pack(fill="both", expand=True)

    def _configure_style(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", rowheight=24, font=("Segoe UI", 10))
        style.configure("TButton", padding=6, font=("Segoe UI", 10))
        style.configure("TLabel", font=("Segoe UI", 10))

    def _build_header(self) -> None:
        header = ttk.Frame(self)
        ttk.Label(header, text="Library", font=("Segoe UI", 16, "bold")).pack(side=tk.LEFT)
        ttk.Entry(header, textvariable=self.search_var, width=30).pack(side=tk.LEFT, padx=8)
        ttk.Button(header, text="Search", command=self._refresh_table).pack(side=tk.LEFT)
        ttk.Label(header, text="Filter:").pack(side=tk.LEFT, padx=(12, 4))
        ttk.Combobox(header, values=["All", "Available", "Checked Out", "Overdue"], state="readonly", textvariable=self.filter_var, width=14).pack(side=tk.LEFT)
        ttk.Button(header, text="Refresh", command=self._refresh_table).pack(side=tk.LEFT, padx=(8, 0))
        header.pack(fill="x", pady=(0, 10))

    def _build_table(self) -> None:
        columns = ("id", "title", "author", "category", "status", "borrower", "due")
        self.table = ttk.Treeview(self, columns=columns, show="headings", selectmode="browse")
        widths = {
            "id": 20,
            "title": 220,
            "author": 160,
            "category": 120,
            "status": 100,
            "borrower": 140,
            "due": 100,
        }
        headers = {
            "id": "ID",
            "title": "Title",
            "author": "Author",
            "category": "Category",
            "status": "Status",
            "borrower": "Borrower",
            "due": "Due Date",
        }
        for col in columns:
            self.table.heading(col, text=headers[col])

            # center ONLY selected columns, keep others left-aligned
            """
                "w"         → West  → left-aligned text
                "center"    → center-aligned text
                "e"         → East  → right-aligned text
            """
            anchor = "center" if col in ("status", "borrower", "due") else "w"
            self.table.column(col, width=widths[col], anchor=anchor)
            
        # (optional) center the Status header label too; already centered!
        # self.table.heading("status", anchor="center")

        self.table.tag_configure("available", background="#e8f5e9")
        self.table.tag_configure("overdue", background="#ffebee")
        self.table.pack(fill="both", expand=True)

    def _build_actions(self) -> None:
        actions = ttk.Frame(self)
        ttk.Button(actions, text="Add Book", command=self._open_add_dialog).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(actions, text="Edit Book", command=self._open_edit_dialog).pack(side=tk.LEFT, padx=6)
        ttk.Button(actions, text="Remove Book", command=self._remove_selected).pack(side=tk.LEFT, padx=6)
        ttk.Button(actions, text="Check Out", command=self._open_checkout_dialog).pack(side=tk.LEFT, padx=6)
        ttk.Button(actions, text="Return", command=self._return_selected).pack(side=tk.LEFT, padx=6)
        ttk.Button(actions, text="Members", command=self._open_members_dialog).pack(side=tk.LEFT, padx=6)
        ttk.Button(actions, text="Overdue", command=self._show_overdue_report).pack(side=tk.LEFT, padx=6)
        ttk.Button(actions, text="Analytics", command=self._show_analytics).pack(side=tk.LEFT, padx=6)
        ttk.Button(actions, text="Export CSV", command=self._export_csv).pack(side=tk.LEFT, padx=6)
        ttk.Button(actions, text="Export JSON", command=self._export_json).pack(side=tk.LEFT, padx=6)
        ttk.Button(actions, text="Import JSON", command=self._import_json).pack(side=tk.LEFT, padx=6)
        ttk.Label(actions, textvariable=self.status_var).pack(side=tk.RIGHT)
        actions.pack(fill="x", pady=10)

    def _selected_book_id(self) -> Optional[str]:
        selection = self.table.selection()
        if not selection:
            return None
        return self.table.item(selection[0], "values")[0]

    def _refresh_table(self) -> None:
        search = self.search_var.get().lower().strip()
        status_filter = self.filter_var.get()
        for row in self.table.get_children():
            self.table.delete(row)
        books = self.service.list_books()
        available_count = 0
        overdue_count = 0
        for book in books:
            if search and search not in book.title.lower() and search not in book.author.lower() and search not in book.category.lower() and search not in book.book_id.lower():
                continue
            status = self.service.status_of(book)
            if status_filter != "All" and status != status_filter:
                continue
            tag = "available" if status == "Available" else "overdue" if status == "Overdue" else ""
            if status == "Available":
                available_count += 1
            if status == "Overdue":
                overdue_count += 1
            self.table.insert("", tk.END, values=(
                book.book_id,
                book.title,
                book.author,
                book.category,
                status,
                book.borrower or "-",
                book.due_date or "-",
            ), tags=(tag,))
        self.status_var.set(f"Available: {available_count} | Overdue: {overdue_count} | Total: {len(books)}")

    def _open_add_dialog(self) -> None:
        dialog = tk.Toplevel(self)
        dialog.title("Add Book")
        center_window(dialog, 280, 195)
        dialog.grab_set()
        entries = {}
        for idx, (label, key) in enumerate([("Book ID", "id"), ("Title", "title"), ("Author", "author"), ("Category", "category")]):
            ttk.Label(dialog, text=label).grid(row=idx, column=0, sticky="w", padx=8, pady=6)
            entry = ttk.Entry(dialog, width=30)
            entry.grid(row=idx, column=1, padx=8, pady=6)
            entries[key] = entry
        entries["category"].insert(0, "General")
        ttk.Button(dialog, text="Save", command=lambda: self._save_new_book(dialog, entries)).grid(row=5, column=0, columnspan=2, pady=10)

    def _save_new_book(self, dialog: tk.Toplevel, entries: Dict[str, ttk.Entry]) -> None:
        try:
            self.service.add_book(
                entries["id"].get(),
                entries["title"].get(),
                entries["author"].get(),
                entries["category"].get(),
            )
        except Exception as exc:
            messagebox.showerror("Error", str(exc), parent=self)
            return
        dialog.destroy()
        self._refresh_table()
        messagebox.showinfo("Success", "Book added", parent=self)

    def _open_edit_dialog(self) -> None:
        book_id = self._selected_book_id()
        if not book_id:
            messagebox.showwarning("Select", "Select a book to edit", parent=self)
            return
        book = self.repo.get(book_id)
        if not book:
            messagebox.showerror("Error", "Book not found", parent=self)
            return
        dialog = tk.Toplevel(self)
        dialog.title("Edit Book")
        center_window(dialog, 280, 160)
        dialog.grab_set()
        entries = {}
        for idx, (label, key, value) in enumerate([
            ("Title", "title", book.title),
            ("Author", "author", book.author),
            ("Category", "category", book.category),
        ]):
            ttk.Label(dialog, text=label).grid(row=idx, column=0, sticky="w", padx=8, pady=6)
            entry = ttk.Entry(dialog, width=30)
            entry.insert(0, value)
            entry.grid(row=idx, column=1, padx=8, pady=6)
            entries[key] = entry
        ttk.Button(dialog, text="Save", command=lambda: self._save_edit(book_id, dialog, entries)).grid(row=4, column=0, columnspan=2, pady=10)

    def _save_edit(self, book_id: str, dialog: tk.Toplevel, entries: Dict[str, ttk.Entry]) -> None:
        book = self.repo.get(book_id)
        if not book:
            messagebox.showerror("Error", "Book not found", parent=self)
            return
        book.title = entries["title"].get().strip()
        book.author = entries["author"].get().strip()
        book.category = entries["category"].get().strip() or "General"
        self.repo.upsert(book)
        dialog.destroy()
        self._refresh_table()
        messagebox.showinfo("Success", "Book updated", parent=self)

    def _remove_selected(self) -> None:
        book_id = self._selected_book_id()
        if not book_id:
            messagebox.showwarning("Select", "Select a book to remove", parent=self)
            return
        if not messagebox.askyesno("Confirm", "Remove the selected book?", parent=self):
            return
        try:
            self.service.remove_book(book_id)
        except Exception as exc:
            messagebox.showerror("Error", str(exc), parent=self)
            return
        self._refresh_table()
        messagebox.showinfo("Success", "Book removed", parent=self)

    def _open_checkout_dialog(self) -> None:
        book_id = self._selected_book_id()
        if not book_id:
            messagebox.showwarning("Select", "Select a book to check out", parent=self)
            return
        dialog = tk.Toplevel(self)
        dialog.title("Check Out")
        # center the checkout_dialog window
        center_window(dialog, 350, 250)
        dialog.grab_set()
        ttk.Label(dialog, text="Select Member").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        members = self.service.list_members()
        member_choices = [f"{m.member_id} - {m.name}" for m in members] or ["(none)"]
        member_var = tk.StringVar(value=member_choices[0])
        member_combo = ttk.Combobox(dialog, values=member_choices, textvariable=member_var, state="readonly", width=32)
        member_combo.grid(row=0, column=1, padx=8, pady=6)
        ttk.Label(dialog, text="Or Add Member").grid(row=1, column=0, sticky="w", padx=8, pady=6)
        new_member_id = ttk.Entry(dialog, width=30)
        new_member_id.insert(0, self.service.next_member_id())
        new_member_id.grid(row=1, column=1, padx=8, pady=6)
        ttk.Label(dialog, text="Name").grid(row=2, column=0, sticky="w", padx=8, pady=6)
        new_member_name = ttk.Entry(dialog, width=30)
        new_member_name.grid(row=2, column=1, padx=8, pady=6)
        ttk.Label(dialog, text="Email").grid(row=3, column=0, sticky="w", padx=8, pady=6)
        new_member_email = ttk.Entry(dialog, width=30)
        new_member_email.grid(row=3, column=1, padx=8, pady=6)
        ttk.Label(dialog, text="Days").grid(row=4, column=0, sticky="w", padx=8, pady=6)
        days_entry = ttk.Entry(dialog, width=10)
        days_entry.insert(0, "14")
        days_entry.grid(row=4, column=1, padx=8, pady=6, sticky="w")
        ttk.Button(dialog, text="Confirm", command=lambda: self._checkout(book_id, member_var.get(), new_member_id.get(), new_member_name.get(), new_member_email.get(), days_entry.get(), dialog)).grid(row=5, column=0, columnspan=2, pady=10)

    def _checkout(self, book_id: str, member_choice: str, new_member_id: str, new_member_name: str, new_member_email: str, days_text: str, dialog: tk.Toplevel) -> None:
        try:
            days = int(days_text)
            if days <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Days must be a positive number", parent=self)
            return
        member_id = None
        if new_member_id.strip() and new_member_name.strip():
            if self.service.get_member(new_member_id.strip()):
                messagebox.showerror("Error", "Member ID already exists. Use the existing member or pick another ID.", parent=self)
                return
            try:
                self.service.add_member(new_member_id, new_member_name, new_member_email)
                member_id = new_member_id.strip()
            except Exception as exc:
                messagebox.showerror("Error", str(exc), parent=self)
                return
        else:
            if member_choice and member_choice != "(none)":
                member_id = member_choice.split(" - ", 1)[0]
        if not member_id:
            messagebox.showerror("Error", "Select or add a member", parent=self)
            return
        try:
            self.service.checkout(book_id, member_id, days)
        except Exception as exc:
            messagebox.showerror("Error", str(exc), parent=self)
            return
        dialog.destroy()
        self._refresh_table()
        messagebox.showinfo("Success", "Book checked out", parent=self)

    def _return_selected(self) -> None:
        book_id = self._selected_book_id()
        if not book_id:
            messagebox.showwarning("Select", "Select a book to return", parent=self)
            return
        try:
            self.service.return_book(book_id)
        except Exception as exc:
            messagebox.showerror("Error", str(exc), parent=self)
            return
        self._refresh_table()
        messagebox.showinfo("Success", "Book returned", parent=self)

    def _open_members_dialog(self) -> None:
        dialog = tk.Toplevel(self)
        dialog.title("Members")
        center_window(dialog, 700, 600)
        dialog.grab_set()
        columns = ("id", "name", "email")
        tree = ttk.Treeview(dialog, columns=columns, show="headings")
        for col, text, width in [("id", "ID", 100), ("name", "Name", 180), ("email", "Email", 200)]:
            tree.heading(col, text=text)
            tree.column(col, width=width, anchor="w")
        tree.pack(fill="both", expand=True, padx=8, pady=8)
        for member in self.service.list_members():
            tree.insert("", tk.END, values=(member.member_id, member.name, member.email))
        form = ttk.Frame(dialog)
        form.pack(fill="x", padx=8, pady=8)
        ttk.Label(form, text="ID").grid(row=0, column=0, sticky="w", pady=4)
        mid_entry = ttk.Entry(form, width=18)
        mid_entry.grid(row=0, column=1, sticky="w")
        mid_entry.insert(0, self.service.next_member_id())
        ttk.Label(form, text="Name").grid(row=1, column=0, sticky="w", pady=4)
        mname_entry = ttk.Entry(form, width=24)
        mname_entry.grid(row=1, column=1, sticky="w")
        ttk.Label(form, text="Email").grid(row=2, column=0, sticky="w", pady=4)
        memail_entry = ttk.Entry(form, width=24)
        memail_entry.grid(row=2, column=1, sticky="w")
        def save_member() -> None:
            try:
                self.service.add_member(mid_entry.get(), mname_entry.get(), memail_entry.get())
                existing = None
                for item in tree.get_children():
                    if tree.item(item, "values")[0] == mid_entry.get().strip():
                        existing = item
                        break
                values = (mid_entry.get().strip(), mname_entry.get().strip(), memail_entry.get().strip())
                if existing:
                    tree.item(existing, values=values)
                else:
                    tree.insert("", tk.END, values=values)
                mid_entry.delete(0, tk.END)
                mname_entry.delete(0, tk.END)
                memail_entry.delete(0, tk.END)
                mid_entry.insert(0, self.service.next_member_id())
                self._refresh_table()
            except Exception as exc:
                messagebox.showerror("Error", str(exc), parent=dialog)
        def delete_member() -> None:
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("Select", "Select a member to delete", parent=dialog)
                return
            member_id = tree.item(selection[0], "values")[0]
            if not messagebox.askyesno("Confirm", f"Delete member {member_id}?", parent=dialog):
                return
            try:
                self.service.remove_member(member_id)
                tree.delete(selection[0])
                mid_entry.delete(0, tk.END)
                mname_entry.delete(0, tk.END)
                memail_entry.delete(0, tk.END)
                self._refresh_table()
            except Exception as exc:
                messagebox.showerror("Error", str(exc), parent=dialog)

        def on_select(event: tk.Event) -> None:
            selected = tree.selection()
            if not selected:
                return
            vals = tree.item(selected[0], "values")
            mid_entry.delete(0, tk.END)
            mname_entry.delete(0, tk.END)
            memail_entry.delete(0, tk.END)
            mid_entry.insert(0, vals[0])
            mname_entry.insert(0, vals[1])
            memail_entry.insert(0, vals[2])

        tree.bind("<<TreeviewSelect>>", on_select)
        btn_row = ttk.Frame(form)
        btn_row.grid(row=3, column=0, columnspan=2, pady=8)
        ttk.Button(btn_row, text="Add / Update", command=save_member).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_row, text="Delete", command=delete_member).pack(side=tk.LEFT, padx=4)

    def _show_overdue_report(self) -> None:
        overdue = self.service.overdue_books()
        if not overdue:
            messagebox.showinfo("Overdue", "No overdue books", parent=self)
            return
        lines = [f"{b.book_id} - {b.title} (due {b.due_date})" for b in overdue]
        messagebox.showwarning("Overdue Books", "\n".join(lines), parent=self)

    def _show_analytics(self) -> None:
        top = self.service.top_borrowed()
        loans = self.service.list_loans()
        active_loans = [l for l in loans if l.returned_at is None]
        lines = []
        lines.append("Top borrowed:")
        for book in top:
            lines.append(f"- {book.title} ({book.times_borrowed} times)")
        lines.append("")
        lines.append(f"Active loans: {len(active_loans)}")
        lines.append(f"Total loans: {len(loans)}")
        messagebox.showinfo("Analytics", "\n".join(lines), parent=self)

    def _export_csv(self) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not path:
            return
        try:
            self.service.export_books_csv(Path(path))
            messagebox.showinfo("Export", "Books exported to CSV", parent=self)
        except Exception as exc:
            messagebox.showerror("Error", str(exc), parent=self)

    def _export_json(self) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            self.service.export_json(Path(path))
            messagebox.showinfo("Export", "Data exported to JSON", parent=self)
        except Exception as exc:
            messagebox.showerror("Error", str(exc), parent=self)

    def _import_json(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            self.service.import_json(Path(path))
            self._refresh_table()
            messagebox.showinfo("Import", "Data imported", parent=self)
        except Exception as exc:
            messagebox.showerror("Error", str(exc), parent=self)


if __name__ == "__main__":
    root = tk.Tk()
    center_window(root, 1500, 900)   # window size + centered position
    app = LibraryManagementGUI(root)
    root.mainloop()
