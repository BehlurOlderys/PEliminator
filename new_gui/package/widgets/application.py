import tkinter as tk
from tkinter import ttk


class BaseGuiApplication:
    def __init__(self, geometry="800x640", title="MyApp", *args, **kwargs):
        self._root = tk.Tk()
        self._root.title(title)
        self._root.geometry(geometry)

        self._style = ttk.Style()
        self._style.theme_use('alt')
        self._style.configure("B.TSeparator", background='#222222')
        self._style.configure('TButton', font=('calibre', 10, 'bold'), background='#333333', foreground='white')
        self._style.map('TButton', background=[('active', '#444444')])
        self._style.configure("B.TFrame", background="#222222")
        self._style.configure("C.TFrame", background="#772222")
        self._style.configure("D.TFrame", background="#222277")
        self._style.configure("E.TFrame", background="#227722")
        self._style.configure("B.TCombobox", font=('calibre', 10, 'bold'), background='#222222', foreground='white',
                              fieldbackground='#333333')

        self._style.configure("B.TSpinbox",
                              font=('calibre', 10, 'bold'), background='#333333', foreground='white',
                              fieldbackground='#333333')
        self._style.configure("B.TLabel", background="#222222", foreground="white", font=('calibre', 10, 'bold'))

    def run(self):
        self._root.mainloop()


class SimpleGuiApplication(BaseGuiApplication):
    def __init__(self, *args, **kwargs):
        super(SimpleGuiApplication, self).__init__(*args, **kwargs)
        self._main_frame = ttk.Frame(self._root, style="B.TFrame")
        self._main_frame.pack(expand=True, fill='both')
