# database.py
import os
import sqlite3
from tkinter import messagebox
import config
from config import load_or_create_config
import time
import gui

DATABASE_FILE = 'default.db'
config = load_or_create_config()

def connect_db():
    """ Stellt eine Verbindung zur SQLite-Datenbank her und gibt diese zurück. """
    db_name = config.get('database', DATABASE_FILE)
    db_path = os.path.dirname(db_name)
        
    if not db_path:
        db_path = os.getcwd()
        
    if db_path and not os.path.exists(db_path):
        os.makedirs(db_path)
            
    try:
        return sqlite3.connect(db_name)
    except sqlite3.Error as e:
        messagebox.showerror("Datenbankfehler", f"Ein Fehler ist aufgetreten: {e}")
        return None

def create_table():
    """ Erstellt die Tabelle in der SQLite-Datenbank, falls sie noch nicht existiert. """
    try:
        with connect_db() as conn:
            if conn is not None:
                cursor = conn.cursor()
                cursor.execute('''CREATE TABLE IF NOT EXISTS dokumente
                                (id INTEGER PRIMARY KEY, beschreibung TEXT, kategorie TEXT, seitenzahl TEXT, erstelldatum TEXT, link TEXT, autor TEXT)''')
                conn.commit()
    except sqlite3.Error as e:
        messagebox.showerror("Datenbankfehler", f"Ein Fehler ist aufgetreten bei der Datenbankoperation: {e}")

def insert_document(beschreibung, kategorie, seitenzahl, erstelldatum, link, autor):
    try:
        with connect_db() as conn:
            if conn is not None:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO dokumente (beschreibung, kategorie, seitenzahl, erstelldatum, link, autor) VALUES (?, ?, ?, ?, ?, ?)",
                               (beschreibung, kategorie, seitenzahl, erstelldatum, link, autor))
                conn.commit()
    except sqlite3.Error as e:
        messagebox.showerror("Datenbankfehler", f"Ein Fehler ist aufgetreten bei der Datenbankoperation: {e}")

def insert_file_if_not_exists(file_path, category):
    """
    Fügt eine Datei in die Datenbank ein, falls sie noch nicht vorhanden ist.
    
    :param file_path: Der Pfad der Datei.
    :param category: Die Kategorie, unter der die Datei gespeichert werden soll.
    """
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM dokumente WHERE link=?", (file_path,))
            if cursor.fetchone() is None:
                # Dateiinformationen extrahieren
                beschreibung = time.strftime('%Y%m%d', time.localtime(os.path.getmtime(file_path))) + "_" + os.path.splitext(os.path.basename(file_path))[0]
                seitenzahl = 1
                erstelldatum = time.strftime('%d.%m.%Y', time.localtime(os.path.getmtime(file_path)))
                autor = "Unbekannt"
                # Neuen Eintrag in die Datenbank einfügen
                print(f"Neue Datei gefunden: {file_path}")
                cursor.execute("INSERT INTO dokumente (beschreibung, kategorie, seitenzahl, erstelldatum, link, autor) VALUES (?, ?, ?, ?, ?, ?)",
                                (beschreibung, category, seitenzahl, erstelldatum, file_path, autor))
                conn.commit()
    except sqlite3.Error as e:
        messagebox.showerror("Datenbankfehler", f"Ein Fehler ist aufgetreten bei der Datenbankoperation: {e}")

def file_is_valid(file_path, extensions):
    return any(file_path.lower().endswith(ext) for ext in extensions)

def insert_document(id, beschreibung, kategorie, seitenzahl, erstelldatum, link, autor):
    """
    Fügt ein neues Dokument in die Datenbank ein oder aktualisiert ein bestehendes Dokument,
    und aktualisiert anschließend die Ansicht.

    :param id: Die ID des Dokuments. Wenn None, wird ein neues Dokument eingefügt.
    :param beschreibung: Die Beschreibung des Dokuments.
    :param kategorie: Die Kategorie des Dokuments.
    :param seitenzahl: Die Anzahl der Seiten des Dokuments.
    :param erstelldatum: Das Erstellungsdatum des Dokuments.
    :param link: Der Link zum Dokument.
    :param autor: Der Autor des Dokuments.
    """
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            
            # Überprüfen, ob bereits ein Eintrag mit demselben Link existiert
            # cursor.execute("SELECT * FROM dokumente WHERE link=?", (link,))
            
            # existing_entry = cursor.fetchone()

            if id is not None:
                existing_data = get_document_by_id(id)
                if existing_data:
                    cursor.execute("UPDATE dokumente SET beschreibung=?, kategorie=?, seitenzahl=?, erstelldatum=?, link=?, autor=? WHERE id=?",
                                    (beschreibung, kategorie, seitenzahl, erstelldatum, link, autor, id))
            else:
                cursor.execute("INSERT INTO dokumente (beschreibung, kategorie, seitenzahl, erstelldatum, link, autor) VALUES (?, ?, ?, ?, ?, ?)",
                                (beschreibung, kategorie, seitenzahl, erstelldatum, link, autor))
            conn.commit()
    except sqlite3.Error as e:
        messagebox.showerror("Datenbankfehler", f"Ein Fehler ist aufgetreten: {e}")

def update_document_link(doc_id, new_link):
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE dokumente SET link=? WHERE id=?", (new_link, doc_id))
            conn.commit()
    except sqlite3.Error as e:
        messagebox.showerror("Datenbankfehler", f"Ein Fehler ist aufgetreten: {e}")
        
def update_multiple_documents(ids, changes):
    """
    Aktualisiert ein bestimmtes Merkmal für mehrere Dokumente in der Datenbank.

    :param ids: Eine Liste von Dokumenten-IDs, die aktualisiert werden sollen.
    :param changes: Ein Dictionary, das die zu ändernden Merkmale und ihre neuen Werte enthält.
    """
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            for doc_id in ids:
                for key, value in changes.items():
                    cursor.execute(f"UPDATE dokumente SET {key}=? WHERE id=?", (value, doc_id))
            conn.commit()
    except sqlite3.Error as e:
        messagebox.showerror("Datenbankfehler", f"Ein Fehler ist aufgetreten: {e}")

def load_ordered_documents(sort_column, sort_direction):
    """
    Lädt alle Dokumente aus der Datenbank und 
    sortiert sie nach dem aktuellen Sortierkriterium
    """
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            query = f"SELECT * FROM dokumente ORDER BY {sort_column} {'DESC' if sort_direction else 'ASC'}"
            cursor.execute(query)
            return cursor.fetchall()
                
    except sqlite3.Error as e:
        messagebox.showerror("Datenbankfehler", f"Ein Fehler ist aufgetreten: {e}")

def load_all_documents():
    """
    Lädt alle Dokumente aus der Datenbank und 
    sortiert sie nach dem aktuellen Sortierkriterium
    """
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            query = f"SELECT * FROM dokumente"
            cursor.execute(query)
            return cursor.fetchall()
                
    except sqlite3.Error as e:
        messagebox.showerror("Datenbankfehler", f"Ein Fehler ist aufgetreten: {e}")
        
def validate_link(id, link):
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM dokumente WHERE link=?", (link,))
            data = cursor.fetchone()
            
            if data is None:
                return False
                        
            return id is data[0]
    except sqlite3.Error as e:
        messagebox.showerror("Datenbankfehler", f"Ein Fehler ist aufgetreten: {e}")
        
def delete_by_link(document_link):
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM dokumente WHERE link=?", (document_link,))
            conn.commit()
    except sqlite3.Error as e:
            messagebox.showerror("Datenbankfehler", f"Ein Fehler ist aufgetreten: {e}")

def get_document_id_by_link(link):
    """
    Ermittelt die ID eines Dokuments basierend auf seinem Link.

    :param link: Der Link des Dokuments.
    :return: Die ID des Dokuments oder None, falls kein Dokument gefunden wurde.
    """
    id = None
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM dokumente WHERE link=?", (link,))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                return None
            return id
    except sqlite3.Error as e:
        messagebox.showerror("Datenbankfehler", f"Ein Fehler ist aufgetreten: {e}")
        return None

def get_document_by_id(id):
    """
    Lädt die Details eines Dokuments basierend auf seiner ID.

    :param id: Die ID des Dokuments.
    :return: Ein Tupel mit den Details des Dokuments oder None, falls kein Dokument gefunden wurde.
    """
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT beschreibung, kategorie, seitenzahl, erstelldatum, link, autor FROM dokumente WHERE id=?", (id,))
            result = cursor.fetchone()
            if result:
                return result
            else:
                return None
            return id
    except sqlite3.Error as e:
        messagebox.showerror("Datenbankfehler", f"Ein Fehler ist aufgetreten: {e}")
        return None
