import os
import sqlite3
from datetime import date, timedelta

from flask import Flask, flash, g, jsonify, redirect, render_template, request, url_for

LOAN_DAYS = 7


def create_app(db_path=None):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
    app.config["DB_PATH"] = db_path or os.environ.get("DB_PATH", "library.db")
    app.config["APP_VERSION"] = os.environ.get("APP_VERSION", "v1")

    # ---------- database helpers ----------
    def get_db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DB_PATH"])
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(exc):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    def init_db():
        db = sqlite3.connect(app.config["DB_PATH"])
        db.execute(
            """CREATE TABLE IF NOT EXISTS books (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   title TEXT NOT NULL,
                   author TEXT NOT NULL,
                   issued_to TEXT,
                   issue_date TEXT,
                   due_date TEXT
               )"""
        )
        db.commit()
        db.close()

    init_db()

    @app.context_processor
    def inject_globals():
        return {"version": app.config["APP_VERSION"], "today": date.today().isoformat()}

    # ---------- routes ----------
    @app.route("/")
    def index():
        q = request.args.get("q", "").strip()
        db = get_db()
        if q:
            like = f"%{q}%"
            books = db.execute(
                "SELECT * FROM books WHERE title LIKE ? OR author LIKE ? ORDER BY id DESC",
                (like, like),
            ).fetchall()
        else:
            books = db.execute("SELECT * FROM books ORDER BY id DESC").fetchall()
        return render_template("index.html", books=books, q=q)

    @app.route("/books", methods=["POST"])
    def add_book():
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        if not title or not author:
            flash("Title and author are required.", "error")
            return redirect(url_for("index"))
        db = get_db()
        db.execute("INSERT INTO books (title, author) VALUES (?, ?)", (title, author))
        db.commit()
        flash(f"Added '{title}'.", "success")
        return redirect(url_for("index"))

    @app.route("/books/<int:book_id>/issue", methods=["POST"])
    def issue_book(book_id):
        borrower = request.form.get("borrower", "").strip()
        if not borrower:
            flash("Borrower name is required.", "error")
            return redirect(url_for("index"))
        db = get_db()
        book = db.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
        if book is None:
            flash("Book not found.", "error")
        elif book["issued_to"]:
            flash("Book is already issued.", "error")
        else:
            today = date.today()
            db.execute(
                "UPDATE books SET issued_to = ?, issue_date = ?, due_date = ? WHERE id = ?",
                (borrower, today.isoformat(), (today + timedelta(days=LOAN_DAYS)).isoformat(), book_id),
            )
            db.commit()
            flash(f"Issued '{book['title']}' to {borrower}.", "success")
        return redirect(url_for("index"))

    @app.route("/books/<int:book_id>/return", methods=["POST"])
    def return_book(book_id):
        db = get_db()
        db.execute(
            "UPDATE books SET issued_to = NULL, issue_date = NULL, due_date = NULL WHERE id = ?",
            (book_id,),
        )
        db.commit()
        flash("Book returned.", "success")
        return redirect(url_for("index"))

    @app.route("/books/<int:book_id>/delete", methods=["POST"])
    def delete_book(book_id):
        db = get_db()
        db.execute("DELETE FROM books WHERE id = ?", (book_id,))
        db.commit()
        flash("Book deleted.", "success")
        return redirect(url_for("index"))

    @app.route("/overdue")
    def overdue():
        db = get_db()
        books = db.execute(
            "SELECT * FROM books WHERE issued_to IS NOT NULL AND due_date < ? ORDER BY due_date",
            (date.today().isoformat(),),
        ).fetchall()
        return render_template("overdue.html", books=books)

    @app.route("/health")
    def health():
        return jsonify(status="ok", version=app.config["APP_VERSION"])

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
