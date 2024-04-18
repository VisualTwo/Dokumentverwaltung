# main.py
import tkinter as tk
from gui import DocumentManagerGUI

def main():
    root = tk.Tk()
    root.geometry("800x600")
    app = DocumentManagerGUI(root)
    root.mainloop()
    
if __name__ == "__main__":
    main()
