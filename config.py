# config.py
import json
import os
from tkinter import filedialog, messagebox

CONFIG_FILE = 'config.json'

def load_or_create_config():
    """ Lädt die Konfigurationsdatei oder erstellt eine neue, wenn sie nicht existiert. """
    if not os.path.isfile(CONFIG_FILE):
        config = {
            'file_path': os.getcwd(),
            'categories': ['Finanzen', 'Lohnabrechnungen', 'Versicherungen'],
            'extensions': ['.jpeg', '.jpg', '.pdf']
        }
        with open(CONFIG_FILE, 'w') as configfile:
            json.dump(config, configfile, indent=4)
    else:
        with open(CONFIG_FILE, 'r') as configfile:
            config = json.load(configfile)
            
    # Ordner gemäß der Kategorienbezeichnungen anlegen, wenn sie noch nicht existieren
    for category in config['categories']:
        category_path = os.path.join(config['file_path'], category)
        if not os.path.exists(category_path):
            os.makedirs(category_path)
            # Benutzer über die Erstellung des Ordners informieren
            messagebox.showinfo("Information", f"Ordner '{category}' wurde erstellt.")
            
    return config

def save_config(config):
    """
    Speichert die aktuelle Konfiguration in der Konfigurationsdatei.
    
    :param config: Das Konfigurationsdictionary, das gespeichert werden soll.
    """
    with open(CONFIG_FILE, 'w') as configfile:
        json.dump(config, configfile, indent=4)
    
def change_default_path():
    """
    Ermöglicht dem Benutzer, den Standardpfad für die Dokumentenspeicherung zu ändern.
    """
    new_path = filedialog.askdirectory()
    if new_path:
        config = load_or_create_config()
        config['file_path'] = new_path
        save_config(config)
        messagebox.showinfo("Erfolg", f"Der neue Standardpfad '{new_path}' wurde gespeichert.")

            
