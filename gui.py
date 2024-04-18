# gui.py
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, Menu
from tkcalendar import Calendar, DateEntry
import time
import shutil
import sys
import subprocess
import csv
import PyPDF2
import database
import config

class DocumentManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Dokumentenverwaltung")
        self.sort_column = 'erstelldatum'  # Standard-Sortierspalte
        self.sort_direction = False  # False für aufsteigend, True für absteigend
        self.config = config.load_or_create_config()
        database.create_table()
        self.setup_gui()
        self.load_and_display_documents()
        self.create_menu()
        self.search_and_insert_new_files()
        self.delete_not_existing_files()

    def setup_gui(self):
        """
        Initialisiert die grafische Benutzeroberfläche der Anwendung und konfiguriert die Widgets.
        """
        self.tree = ttk.Treeview(self.root, selectmode='extended', columns=('Beschreibung', 'Kategorie', 'Seitenzahl', 'Erstelldatum', 'Link', 'Autor'), show='headings')
        self.tree.grid(row=0, column=0, columnspan=5, sticky='nsew', padx=5, pady=5)

        # Konfigurieren der Spaltenüberschriften
        self.tree.heading('Beschreibung', text='Beschreibung', command=lambda: self.treeview_sort_column('Beschreibung', False))
        self.tree.heading('Kategorie', text='Kategorie', command=lambda: self.treeview_sort_column('Kategorie', False))
        self.tree.heading('Seitenzahl', text='Seitenzahl', command=lambda: self.treeview_sort_column('Seitenzahl', False))
        self.tree.heading('Erstelldatum', text='Erstelldatum', command=lambda: self.treeview_sort_column('Erstelldatum', False))
        self.tree.heading('Link', text='Link', command=lambda: self.treeview_sort_column('Link', False))
        self.tree.heading('Autor', text='Autor', command=lambda: self.treeview_sort_column('Autor', False))
                
        # Konfigurieren der Spaltenbreiten und verhindern des Streckens
        self.tree.column('Beschreibung', width=300, stretch=tk.YES)
        self.tree.column('Kategorie', width=150, stretch=tk.NO)
        self.tree.column('Seitenzahl', width=100, stretch=tk.NO)  # Schmalere Spalte für "Seitenzahl"
        self.tree.column('Erstelldatum', width=100, stretch=tk.NO)  # Schmalere Spalte für "Erstelldatum"
        self.tree.column('Link', width=300, stretch=tk.YES)
        self.tree.column('Autor', width=150, stretch=tk.NO)
 
        # Höhe des Treeview anpassen
        self.tree.configure(height=20)

        # Scrollbar hinzufügen
        treeview_scroll = tk.Scrollbar(self.root, orient="vertical", command=self.tree.yview)
        treeview_scroll.grid(row=0, column=5, sticky='ns', padx=2)
        self.tree.configure(yscrollcommand=treeview_scroll.set)

        # Action für Doppelklick im Treeview definieren
        self.tree.bind("<Double-1>", self.on_treeview_double_click)
        self.tree.bind("<Button-3>", self.on_treeview_right_click)
        # Bind the selection change event
        self.tree.bind('<<TreeviewSelect>>', self.on_selection_change)
        
        # Button "Neuer Eintrag"
        new_entry_button = tk.Button(self.root, text="Neuer Eintrag", command=self.new_entry_window)
        new_entry_button.grid(row=1, column=0, padx=(10, 20))  # padx=(left, right) für den Abstand links und rechts vom Button

        # Button "Eintrag ändern"
        self.change_entry_button = tk.Button(self.root, text="Eintrag ändern", state='disabled', command=self.change_entry)
        self.change_entry_button.grid(row=1, column=1, padx=(2, 2))  # padx=(left, right) für den Abstand links und rechts vom Button
        
        # Button "Merkmale setzen"
        self.update_button = tk.Button(self.root, text="Merkmale setzen", state='disabled', command=self.open_update_window)
        self.update_button.grid(row=1, column=2, padx=(2, 2))

        # Button "Eintrag löschen" direkt neben "Eintrag ändern"
        self.delete_entry_button = tk.Button(self.root, text="Eintrag löschen", state='disabled', command=self.delete_entry)
        self.delete_entry_button.grid(row=1, column=3, padx=(2, 2))  # Geringer Zwischenabstand zum vorherigen Button

        # Button "Umbenennen"
        self.rename_button = tk.Button(self.root, text="Umbenennen", command=self.rename_entry)
        self.rename_button.grid(row=1, column=4, padx=(2, 10))  # Platzieren Sie den Button neben den anderen Buttons

        # Konfigurieren der Zeilen- und Spaltengewichtung, um die Skalierung zu ermöglichen
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=0)

        # Frame für den Fortschrittsbalken und Label
        self.progress_frame = tk.Frame(self.root)
        self.progress_frame.grid(row=2, column=0, columnspan=5, sticky='ew')
    
        # Label für Fortschrittsanzeige initialisieren
        self.progress_label = tk.Label(self.progress_frame, text="Bereit", bg='white', relief=tk.SUNKEN, anchor='w')
        self.progress_label.pack(fill=tk.X, padx=5, pady=5)

        # Fortschrittsbalken initialisieren
        self.progress = ttk.Progressbar(self.progress_frame)
        self.progress.pack(fill=tk.X, padx=5, pady=5)
        
    def on_selection_change(self, event):
        selected_items = self.tree.selection()
        if not selected_items:
            self.change_entry_button.config(text="Eintrag ändern", state='disabled')
            self.delete_entry_button.config(text="Eintrag löschen", state='disabled')
            self.update_button.config(text="Merkmale setzen", state='disabled')
        elif len(selected_items) == 1:
            self.change_entry_button.config(text="Eintrag ändern", state='normal')
            self.delete_entry_button.config(text="Eintrag löschen", state='normal')
            self.update_button.config(text="Merkmale setzen", state='normal')
        else:
            self.change_entry_button.config(text="Einträge ändern", state='normal')
            self.delete_entry_button.config(text="Einträge löschen", state='normal')
            self.update_button.config(text="Merkmale setzen", state='normal')

    def load_and_display_documents(self):
        """
        Lädt alle Dokumente aus der Datenbank und zeigt sie im Treeview-Widget an,
        sortiert nach dem aktuellen Sortierkriterium
        """
        rows = database.load_ordered_documents(self.sort_column, self.sort_direction)
                
        # Löschen aller vorhandenen Einträge im Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Einfügen der neuen Einträge
        for row in rows:
            self.tree.insert('', 'end', values=(row[1], row[2], row[3], row[4], row[5], row[6]))
        
    def new_entry_window(self, id=None):
        """
        Öffnet ein neues Fenster zur Eingabe oder Bearbeitung von Dokumentdetails.

        :param id: Die ID des zu bearbeitenden Dokuments. Wenn None, wird ein neuer Eintrag erstellt.
        """
        new_window = tk.Toplevel(self.root)
        self.alter_eintrag = False
        
        if id is None:
            new_window.title("Neuer Eintrag")
            self.alter_eintrag = True
        else:
            new_window.title("Eintrag bearbeiten")
        new_window.geometry("800x250")

        labels = ['Beschreibung', 'Kategorie', 'Seitenzahl', 'Erstelldatum', 'Link', 'Autor']
        entries = {}
        for idx, label in enumerate(labels):
            tk.Label(new_window, text=label).grid(row=idx, column=0, sticky="w")

            if label == 'Kategorie':
                # Dropdown für Kategorien erstellen
                categories = self.config.get('categories', [])
                category_var = tk.StringVar(self.root)
                category_dropdown = tk.OptionMenu(new_window, category_var, *categories)
                category_dropdown.grid(row=idx, column=1, sticky="w", padx=5)  # Position anpassen
                entries[label] = category_var              
            else:
                entry = tk.Entry(new_window, width=100)
                entry.grid(row=idx, column=1, sticky="w")
                entries[label] = entry
                
            if label == 'Erstelldatum':
                date_button = tk.Button(new_window, text="Datum auswaehlen", command=lambda: self.choose_date(entries[label]))
                date_button.grid(row=idx, column=2, padx=5, pady=5)
            
        def validate(*args):
            link = link_var.get()
            if not database.validate_link(id, link):
                return
                    
            if link.lower().endswith('.pdf'):
                page_count = self.get_pdf_page_count(link)
                if page_count is not None:
                    page_count_str = "1"
                    if page_count > 1:
                        page_count_str = "1-" + str(page_count)
                    entries['Seitenzahl'].delete(0, tk.END)
                    entries['Seitenzahl'].insert(0, page_count_str)
            elif link.lower().endswith('.jpg') or link.endswith('.jpeg'):
                    entries['Seitenzahl'].delete(0, tk.END)
                    entries['Seitenzahl'].insert(0, "1")
                        

        link_var = tk.StringVar()
        entries['Link'] = tk.Entry(new_window, textvariable=link_var, width=100)
        entries['Link'].grid(row=4, column=1, sticky="w")
        link_var.trace("w", validate)

        if id is not None:
            data = database.get_document_by_id(id)
            if data is not None:
                for idx, label in enumerate(labels):
                    if label == 'Kategorie':
                        entries[label].set(data[idx])
                    else:
                        entries[label].delete(0, tk.END)
                        entries[label].insert(0, data[idx])

        def select_file():
            current_link = entries['Link'].get()
            if current_link:
                initial_directory = os.path.dirname(current_link)
            else:
                initial_directory = self.config.get('file_path', '/')
                
            filename = filedialog.askopenfilename(initialdir=initial_directory).encode('utf-8').decode('utf-8')
            
            if filename:
                entries['Link'].delete(0, tk.END)
                entries['Link'].insert(0, filename)
                
                # Erstelldatum aus den Dateieigenschaften lesen
                erstelldatum = time.strftime('%d.%m.%Y', time.localtime(os.path.getmtime(filename)))
                entries['Erstelldatum'].delete(0, tk.END)
                entries['Erstelldatum'].insert(0, erstelldatum)
                
        file_button = tk.Button(new_window, text="Datei auswaehlen", command=select_file)
        file_button.grid(row=4, column=2, padx=5, pady=5)  # Position des Buttons anpassen
        
        ok_button = tk.Button(new_window, text="Ok", command=lambda: self.save_new_entry(id, entries, new_window))
        ok_button.grid(row=len(labels)+1, column=0, columnspan=2)
    
    def delete_entry(self):
        """
        Löscht den ausgewählten Eintrag aus der Datenbank und aktualisiert das Treeview.
        """
        selected_items = self.tree.selection()  # get selection
        if selected_items:  # check if an item is selected
            if len(selected_items) == 1:
                message_text = f"Sind Sie sicher, dass Sie das Dokument '{document_name}' loeschen wollen?"
            else:
                message_text = f"Sind Sie sicher, dass Sie diese {len(selected_items)} Einträge löschen möchten?"
                
            response = messagebox.askyesno("Löschen bestätigen", message_text)
            if response:
                for item in selected_items:
                    item_values = self.tree.item(selected_items, "values")
                    document_name = item_values[0]
                    document_link = item_values[4]
                    database.delete_by_link(document_link)
                    self.tree.delete(selected_items)
                self.load_and_display_documents()
        else:
            messagebox.showinfo("Hinweis", "Kein Dokument zum Loeschen ausgewaehlt.")

    def search_and_insert_new_files(self):
        """
        Durchsucht den Standardpfad nach neuen Dateien und fügt sie in die Datenbank ein, falls sie noch nicht vorhanden sind.
        """
        total_files = sum([len(files) for r, d, files in os.walk(self.config['file_path']) if r.startswith(tuple(self.config['categories']))])
        processed_files = 0

        self.progress['maximum'] = total_files  # Gesamtzahl der zu verarbeitenden Dateien setzen

        for category in self.config['categories']:
            category_path = os.path.join(self.config['file_path'], category)
            if os.path.exists(category_path):
                for filename in os.listdir(category_path):
                    file_path = os.path.join(category_path, filename)
                    if os.path.isfile(file_path) and self.file_is_valid(file_path, self.config.get('extensions', [])):
                        database.insert_file_if_not_exists(file_path, category)
                    processed_files += 1
                    self.progress['value'] = processed_files  # Aktualisiere den Fortschrittsbalken
                    self.progress_label.config(text=f"Verarbeite {processed_files}/{total_files} Dateien...")
                    self.root.update_idletasks()

        self.progress_label.config(text="Fertig!")
        self.progress['value'] = 0  # Setze den Fortschrittsbalken zurück
        
    def delete_not_existing_files(self):
        """
        Durchsucht den Standardpfad nach neuen Dateien und fügt sie in die Datenbank ein, falls sie noch nicht vorhanden sind.
        """
        documents = database.load_all_documents()
        total_documents = len(documents)
        deleted_count = 0

        # Fortschrittsbalken und Label für die Verarbeitung initialisieren
        self.progress['maximum'] = total_documents
        self.progress['value'] = 0
        self.progress_label.config(text=f"Überprüfung von {total_documents} Dokumenten auf ungültige Links...")

        # Überprüfen jedes Dokuments
        for index, doc in enumerate(documents, start=1):
            doc_id, beschreibung, kategorie, seitenzahl, erstelldatum, link, autor = doc
            if link and not os.path.exists(link):  # Überprüfen, ob der Link existiert
                # database.delete_document_by_link(link)  # Löschen des Eintrags aus der Datenbank, falls der Link nicht existiert
                print(f"Link {link} von {beschreibung} ({autor}) ist ungültig.")
                deleted_count += 1
            self.progress['value'] = index
            self.progress_label.config(text=f"Überprüft {index} von {total_documents} Dokumenten")
            self.root.update_idletasks()  # GUI aktualisieren

        self.progress_label.config(text=f"Überprüfung abgeschlossen. {deleted_count} ungültige Links gelöscht.")
        self.progress['value'] = 0  # Fortschrittsbalken zurücksetzen
        
    def create_menu(self):
        """
        Erstellt das Hauptmenü der Anwendung.
        """
        menu_bar = Menu(self.root)
        self.root.config(menu=menu_bar)

        file_menu = Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Datenbank neu einlesen", command=self.load_and_display_documents)
        file_menu.add_command(label="Standardpfad aendern", command=config.change_default_path)
        file_menu.add_command(label="Importieren aus CSV", command=self.import_from_csv)
        file_menu.add_command(label="Exportieren als CSV", command=self.export_to_csv)
        menu_bar.add_cascade(label="Datei", menu=file_menu)

    def open_update_window(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo("Hinweis", "Bitte wählen Sie mindestens ein Dokument aus.")
            return

        update_window = tk.Toplevel(self.root)
        update_window.title("Merkmale setzen")
        update_window.geometry("400x200")

        # Dropdown-Menü für die Auswahl des Merkmals
        tk.Label(update_window, text="Merkmal:").grid(row=0, column=0, sticky="w")
        attribute_var = tk.StringVar(update_window)
        attributes = ['Beschreibung', 'Kategorie', 'Seitenzahl', 'Erstelldatum', 'Link', 'Autor']
        attribute_dropdown = tk.OptionMenu(update_window, attribute_var, *attributes)
        attribute_dropdown.grid(row=0, column=1, sticky="w")

        # Eingabefeld für den neuen Wert des Merkmals
        tk.Label(update_window, text="Neuer Wert:").grid(row=1, column=0, sticky="w")
        new_value_entry = tk.Entry(update_window)
        new_value_entry.grid(row=1, column=1, sticky="w")

        def update_documents():
            attribute = attribute_var.get().lower()
            new_value = new_value_entry.get()
            if attribute and new_value:
                ids = [database.get_document_id_by_link(self.tree.item(item, "values")[4]) for item in selected_items]  # Angenommen, der Link ist das fünfte Element in values
                database.update_multiple_documents(ids, {attribute: new_value})
                update_window.destroy()
                self.load_and_display_documents()
            else:
                messagebox.showerror("Fehler", "Bitte wählen Sie ein Merkmal und geben Sie einen neuen Wert ein.")

        update_button = tk.Button(update_window, text="Aktualisieren", command=update_documents)
        update_button.grid(row=2, column=1, sticky="w")
        
    def on_treeview_double_click(self, event):
        """
        Wird aufgerufen, wenn der Benutzer einen Eintrag im Treeview doppelt anklickt.

        :param event: Das Event, das den Doppelklick ausgelöst hat.
        """
        item = self.tree.identify_row(event.y)
        if item:
            self.change_entry()
        else:
            self.new_entry_window()
                

    def on_treeview_right_click(self, event):
        """
        Wird aufgerufen, wenn der Benutzer mit der rechten Maustaste auf einen Eintrag im Treeview klickt.

        :param event: Das Event, das den Rechtsklick ausgelöst hat.
        """
        # Identifizieren des angeklickten Items
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)  # Selektieren des Items
            item_values = self.tree.item(item, "values")
            document_link = item_values[4]  # Angenommen, der Link befindet sich in der fünften Spalte
            # Fragen, ob der Ordner geöffnet werden soll
            if messagebox.askyesno("Ordner öffnen", "Möchten Sie den Ordner dieses Dokuments öffnen?"):
                folder_path = os.path.dirname(document_link)
                # Überprüfen, ob der Pfad existiert und ein Verzeichnis ist
                if os.path.isdir(folder_path):
                   self.open_folder(document_link)
                else:
                    messagebox.showerror("Fehler", "Der Ordner existiert nicht.")

    def change_entry(self):
        """
        Wird aufgerufen, wenn der Benutzer einen Eintrag im Treeview auswählt und bearbeiten möchte.
        """
        selected_item = self.tree.selection()
        if selected_item:
            item_values = self.tree.item(selected_item, "values")
            id = database.get_document_id_by_link(item_values[4])
            self.new_entry_window(id)
        else:
            messagebox.showinfo("Fehler", "Kein Element ausgewaehlt")

    def rename_entry(self):
        selected_items = self.tree.selection()
        if len(selected_items) == 0:
            messagebox.showinfo("Hinweis", "Bitte wählen Sie mindestens ein Dokument aus.")
            return
        
        # Sammeln aller relevanten Dokumentinformationen vor jeglicher Verarbeitung
        documents_info = []
        for selected_item in selected_items:
            item_values = self.tree.item(selected_item, "values")
            document_id = database.get_document_id_by_link(item_values[4])  # Annahme: Link befindet sich im 5. Element von 'values'
            if document_id:
                document_data = database.get_document_by_id(document_id)
                if document_data:
                    documents_info.append((document_id, document_data))
                else:
                    messagebox.showerror("Fehler", f"Keine Daten für Dokument-ID {document_id} gefunden.")
            else:
                messagebox.showerror("Fehler", f"Keine ID für das Dokument mit dem Link {item_values[4]} gefunden.")
        
        # Verarbeitung der gesammelten Dokumentinformationen
        for document_id, doc_data in documents_info:
            beschreibung, kategorie, seitenzahl, erstelldatum, link, autor = doc_data

            # Erstellen des vorgeschlagenen Dateinamens
            erstelldatum_str = time.strftime('%Y%m%d', time.strptime(erstelldatum, '%d.%m.%Y'))
                
            # Vorgeschlagener neuer Dateiname basierend auf bestehenden Informationen
            suggested_name = f"{erstelldatum_str}_{beschreibung}_{seitenzahl}_{autor}{os.path.splitext(link)[1]}"
            suggested_name = self.clean_filename(suggested_name)
                
            self.prompt_rename(document_id, link, kategorie, suggested_name)

    def prompt_rename(self, document_id, link, kategorie, suggested_name):
        # Erstellen eines Top-Level-Fensters für den Umbenennungsdialog
        rename_window = tk.Toplevel(self.root)
        rename_window.title("Datei umbenennen")
        rename_window.geometry("600x150")

        # Vorschlag für den neuen Dateinamen, umformen von .jpeg zu .jpg wenn nötig
        if suggested_name.lower().endswith('.jpeg'):
            suggested_name = suggested_name[:-5] + '.jpg'

        # Erstellen und Platzieren der Widgets
        tk.Label(rename_window, text="Neuer Dateiname:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        # Setze den vollständigen Zielpfad zusammen
        base_path = self.config.get('file_path', os.getcwd())
        
        new_filename = f"{os.path.join(self.config.get('file_path', os.getcwd()), kategorie, suggested_name)}"

        new_name_value = tk.StringVar(value=new_filename)
        new_name_entry = tk.Entry(rename_window, width=60, textvariable=new_name_value)
        new_name_entry.grid(row=0, column=1, padx=10, pady=10)

        def confirm_rename():
            new_name = new_name_entry.get()
            new_path = os.path.dirname(new_name)
            
            # Prüfung und Erstellung des Zielverzeichnisses, falls nötig
            if not os.path.exists(new_path):
                try:
                    os.makedirs(new_path)
                except Exception as e:
                    messagebox.showerror("Verzeichnisfehler", f"Kann das Zielverzeichnis nicht erstellen: {e}")
                    return

            # Überprüfen, ob der Quellordner existiert
            if not os.path.exists(link):
                messagebox.showerror("Fehler", "Die Quelldatei existiert nicht.")
                return
                
            # Wiederholte Überprüfung und Umbenennungsversuche
            while True:
                try:
                    # Versuch, die Datei exklusiv zu öffnen
                    with open(link, 'rb+') as f:
                        # Wenn kein Fehler auftritt, versuche die Datei zu verschieben
                        if os.path.dirname(link) != new_path:
                            print(f"Verschiebe die Datei von {os.path.dirname(link)} nach {new_path}.")
                            print(f"von  {link}\nnach {new_name}")
                    shutil.move(link, new_name)
                    database.update_document_link(document_id, new_name)
                    self.load_and_display_documents()
                    rename_window.destroy()
                    break  # Beende die Schleife, wenn erfolgreich
                except IOError as e:
                    # Dateizugriff wird von einem anderen Prozess blockiert
                    response = messagebox.askretrycancel("Datei gesperrt",
                                                         "Die Datei wird gerade verwendet und kann nicht umbenannt werden. "
                                                         "Schließen Sie alle Programme, die möglicherweise auf die Datei zugreifen, "
                                                         "und versuchen Sie es erneut.")
                    if not response:
                        rename_window.destroy()
                        break  # Beende die Schleife, wenn der Benutzer abbricht
                except Exception as e:
                    messagebox.showerror("Fehler", f"Beim Umbenennen der Datei ist ein Fehler aufgetreten: {e}")
                    rename_window.destroy()
                    break  # Beende die Schleife, wenn ein anderer Fehler auftritt

        def cancel_rename():
            rename_window.destroy()

        tk.Button(rename_window, text="Übernehmen", command=confirm_rename).grid(row=1, column=0, padx=10, pady=10)
        tk.Button(rename_window, text="Abbrechen", command=cancel_rename).grid(row=1, column=1, padx=10, pady=10)
        
        # Modal machen
        rename_window.transient(self.root)
        rename_window.grab_set()
        rename_window.focus_set()
        rename_window.wait_window()

    def save_new_entry(self, id, entries, window):
        """
        Speichert einen neuen Eintrag oder aktualisiert einen bestehenden Eintrag in der Datenbank.

        :param id: Die ID des Dokuments, das aktualisiert werden soll. Wenn None, wird ein neuer Eintrag erstellt.
        :param entries: Ein Dictionary mit den Eingabefeldern und ihren Werten.
        :param window: Das Fenster, das nach dem Speichern geschlossen werden soll.
        """
        new_data = (
            entries['Beschreibung'].get(),
            entries['Kategorie'].get(),
            entries['Seitenzahl'].get(),
            entries['Erstelldatum'].get(),
            entries['Link'].get(),
            entries['Autor'].get()
            )
        kategorie = entries['Kategorie'].get()
        link = entries['Link'].get()
        default_directory = self.config.get('file_path', os.path.sep)
        expected_prefix = os.path.join(default_directory, kategorie) + os.path.sep

        if not link.startswith(os.path.join(default_directory, kategorie)):
            if messagebox.askyesno("Bestaetigung", "Die Datei befindet sich nicht im erwarteten Verzeichnis.\nSoll sie kopiert werden?"):
                try:
                    filename = os.path.basename(link)
                    erstelldatum = time.strftime('%Y%m%d', time.localtime(os.path.getmtime(link))) + "_"
                    new_filename = erstelldatum + filename
                    if filename.startswith(new_filename): 
                        erstelldatum = ""
                    new_path = os.path.join(expected_prefix, new_filename)
                    shutil.copyfile(link, new_path)
                    entries['Link'].delete(0, tk.END)
                    entries['Link'].insert(0, new_path)
                except Exception as e:
                    messagebox.showerror("Fehler", f"Beim Kopieren der Datei ist ein Fehler aufgetreten: {e}")

        if not self.detect_changes_and_update(id, new_data):
            database.insert_document(id, 
                entries['Beschreibung'].get(),
                entries['Kategorie'].get(),
                entries['Seitenzahl'].get(),
                entries['Erstelldatum'].get(),
                entries['Link'].get(),
                entries['Autor'].get()
            )
            self.load_and_display_documents()

            
        window.destroy()
        
    def detect_changes_and_update(self, id, new_data):
        existing_data = database.get_document_by_id(id)
        if existing_data:
            changes = []
            columns = ['beschreibung', 'kategorie', 'seitenzahl', 'erstelldatum', 'link', 'autor']
            for idx, column in enumerate(columns):
                if str(new_data[idx]) != str(existing_data[idx]):
                    changes.append(f"{column}: '{existing_data[idx]}' zu '{new_data[idx]}'")
        
            if changes:
                print(f"Änderungen in {id}:")
                for change in changes:
                    print(f"  {change}")
                    
                # Aktualisieren des Datensatzes in der Datenbank
                database.insert_document(id, *new_data)
                self.load_and_display_documents()
                return True
            return False
        else:
            print(f"Dokument {id} nicht gefunden.")
            return False

    def choose_date(self, entry):
        """
        Öffnet ein Kalender-Widget, um ein Datum auszuwählen und das ausgewählte Datum in das übergebene Eingabefeld einzufügen.

        :param entry: Das Tkinter Entry-Widget, in das das ausgewählte Datum eingefügt werden soll.
        """
        def set_date():
            entry.delete(0, tk.END)
            entry.insert(0, cal.selection_get())
            top.destroy()

        top = tk.Toplevel(self.root)
        cal = Calendar(top, selectmode='day', year=time.localtime()[0], month=time.localtime()[1], day=time.localtime()[2])
        cal.pack(pady=20)

        ok_button = tk.Button(top, text="Ok", command=set_date)
        ok_button.pack()
        
    def get_pdf_page_count(self, pdf_path):
        """
        Ermittelt die Anzahl der Seiten einer PDF-Datei.

        :param pdf_path: Der Pfad zur PDF-Datei.
        :return: Die Anzahl der Seiten der PDF-Datei oder None bei einem Fehler.
        """
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                return len(pdf_reader.pages)
        except Exception as e:
            print(f"Fehler beim Lesen der PDF-Datei: {e}")
            return None

    def treeview_sort_column(self, col, reverse):
        """
        Sortiert die Einträge im Treeview-Widget basierend auf der angegebenen Spalte und Richtung,
        und speichert die Sortierkriterien.
        
        :param col: Die Spalte, nach der sortiert werden soll.
        :param reverse: Gibt an, ob in aufsteigender oder absteigender Reihenfolge sortiert werden soll.
        """
        # Speichere die aktuell ausgewählten Einträge
        selected_items = [self.tree.item(item, "values") for item in self.tree.selection()]

        children = self.tree.get_children()
        if not children:
            return

        # Aktualisiere die Sortierkriterien
        if col != self.sort_column:
            self.sort_column = col
            self.sort_direction = reverse
        else:    
            self.sort_direction = not self.sort_direction

        # Lade die Einträge neu
        self.load_and_display_documents()

        # Stelle die ursprüngliche Auswahl und das mittlere sichtbare Item wieder her
        index = 0
        for item in self.tree.get_children():
            if self.tree.item(item, "values") in selected_items:
                self.tree.selection_add(item)
                
        # Setze den Fokus zurück auf das TreeView und wähle das erste Element in der Liste aus, wenn vorhanden
        self.tree.focus_set()
            
    def import_from_csv(self):
        # Dateiauswahldialog öffnen
        csv_file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not csv_file_path:
            return

        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            csvreader = csv.reader(csvfile, delimiter=';')
            rows = list(csvreader)  # Alle Zeilen lesen und in eine Liste umwandeln
            total_rows = len(rows) - 1  # Anzahl der Datensätze ohne Überschriftenzeile
        
            # Fortschrittsbalken und Label initialisieren oder zurücksetzen
            self.progress['maximum'] = total_rows
            self.progress['value'] = 0
            self.progress_label.config(text=f"Verarbeitet 0 von {total_rows} Datensätzen")

            # Überschriftenzeile überspringen
            headers = rows.pop(0)

            # Verarbeitung jeder Zeile
            for index, row in enumerate(rows, start=1):
                id = row[0]
                new_data = row[1:7]
                # Entfernen des führenden Hochkommas bei der Seitenzahl, falls vorhanden
                new_data[2] = new_data[2].replace("'", "")
                self.detect_changes_and_update(id, new_data)
                self.progress['value'] = index
                self.progress_label.config(text=f"Verarbeitet {index} von {total_rows} Datensätzen")
                self.root.update_idletasks()  # Aktualisieren der GUI, um den Fortschritt anzuzeigen

            self.progress_label.config(text="Import abgeschlossen!")
            self.progress['value'] = 0  # Fortschrittsbalken zurücksetzen

    def export_to_csv(self):
        documents = database.load_all_documents()
        
        # Pfad und Dateiname für die CSV-Datei festlegen
        csv_file_path = os.path.join(self.config['file_path'], "exported_documents.csv")
        
        # Spaltenüberschriften für die CSV-Datei
        headers = ['ID', 'Beschreibung', 'Kategorie', 'Seitenzahl', 'Erstelldatum', 'Link', 'Autor']
        
        # CSV-Datei schreiben
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=';')  # Trennzeichen auf Semikolon setzen
            csvwriter.writerow(headers)

            for document in documents:
                # Konvertieren der "Seitenzahl" in einen String
                document = list(document)  # Konvertieren des Tupels in eine Liste, um es bearbeiten zu können
                document[3] = "'" + document[3]
                csvwriter.writerows([document])
        
        messagebox.showinfo("Export erfolgreich", f"Dokumente wurden erfolgreich nach '{csv_file_path}' exportiert.")

    def clean_filename(self, filename):
        # Ersetze andere potenziell problematische Zeichen
        filename = filename.replace('/', '_').replace('\\', '_')
        return filename

    def file_is_valid(self, file_path, extensions):
        return any(file_path.lower().endswith(ext) for ext in extensions)

    def open_folder(self, path):
        """
        Öffnet den Ordner eines Dokuments im Dateimanager.

        :param path: Der Pfad des Dokuments.
        """
        # Überprüfen, ob der Pfad ein Verzeichnis ist
        if not os.path.isfile(path):
            messagebox.showerror("Fehler", "Der ausgewählte Pfad ist keine Datei.")
            return
        # Versuchen, den Ordner im Dateimanager zu öffnen
        try:
            if sys.platform == 'win32':
                # os.startfile(path)
                subprocess.run(f'explorer /select,"{path}"', check=True)
            elif sys.platform == 'darwin':
                subprocess.run(['open', path])
            else:  # 'linux', 'linux2', 'cygwin'
                subprocess.run(['xdg-open', path])
        except Exception as e:
            messagebox.showerror("Fehler", f"Ein Fehler ist aufgetreten: {e}")

