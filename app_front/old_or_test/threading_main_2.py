import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.toast import ToastNotification
import threading

# from get_data import get_data_locally
import class_record as rec_t

class IoFront(ttk.Frame):
    def __init__(self, master_window):
        super().__init__(master_window, padding=(20, 10))
        self.grid(row=0, column=0)

        # Utworzenie instancji ScreenRecorder
        # self.screen_recorder = rec_t.ScreenRecorder()

        # kontener z listą zapisanych spotkań
        self.left_container = ttk.LabelFrame(self, text="spotkania")
        self.left_container.pack(padx=5, pady=10, side=LEFT, fill=Y)
        # dodanie listy spotkań
        self.tree = self.create_treeview()

        self.right_container = ttk.Frame(self)

        # kontener z menu i przyciskiem do nagrywania nowego spotkania
        self.new_record_container = ttk.LabelFrame(self.right_container, text="nowe nagranie")
        self.quality_menu = self.create_quality_menu()
        self.start_recording_button()
        self.stop_recording_button()
        self.new_record_container.pack(padx=5, pady=10)

        # kontener z przyciskami akcji do wybranego spotkania
        self.action_container = ttk.LabelFrame(self.right_container, text="do wybranego nagrania")
        self.open_in_browser_button()
        self.delete_recording_button()
        self.action_container.pack(padx=5, pady=10)

        self.right_container.pack(side=LEFT, padx=20, pady=10, fill=Y)

    def create_treeview(self):
        columns = ["id", "date", "name"]
        tree = ttk.Treeview(master=self.left_container, bootstyle="secondary", columns=columns, show='headings', height=20)
        tree.grid_configure(row=0, column=0, columnspan=4, rowspan=5, padx=20, pady=10)

        tree.column("id", width=50, anchor=CENTER)
        tree.column("date", anchor=CENTER)
        tree.column("name", anchor=CENTER)

        tree.heading("id", text="id")
        tree.heading("date", text="date")
        tree.heading("name", text="name")

        tree.tag_configure('change_bg', background="#20374C")

        # data = get_data_locally()  # importowanie danych z pliku

        return tree

    def create_quality_menu(self):
        mb = ttk.Menubutton(master=self.new_record_container, width=16, text="Recording quality")
        mb.grid(row=1, column=1, columnspan=3, rowspan=2, padx=5, pady=10)
        options = ["op1", "op2", "op3", "op4"]
        inside_menu = ttk.Menu(mb, tearoff=0)
        for option in options:
            inside_menu.add_radiobutton(label=option)
        mb["menu"] = inside_menu
        return mb

    def start_recording_button(self):
        button = ttk.Button(master=self.new_record_container, width=20, text="Start recording")
        # Uruchomienie nagrywania w osobnym wątku
        button.bind("<Button-1>", lambda e: threading.Thread(target=self.start_recording).start())
        button.grid(row=3, column=1, rowspan=2, padx=5, pady=10, columnspan=3)
        return button

    def stop_recording_button(self):
        button = ttk.Button(master=self.new_record_container, width=20, text="Stop recording")
        # Uruchomienie zatrzymywania nagrywania w osobnym wątku
        button.bind("<Button-1>", lambda e: [threading.Thread(target=self.stop_recording).start()])
        button.grid(row=5, column=1, rowspan=2, padx=5, pady=10, columnspan=3)
        return button

    def open_in_browser_button(self):
        button = ttk.Button(master=self.action_container, width=20, text="Open in browser")
        button.grid(row=3, column=1, rowspan=2, padx=5, pady=10, columnspan=3)
        return button

    def delete_recording_button(self):
        button = ttk.Button(master=self.action_container, width=20, text="Delete recording")
        button.grid(row=5, column=1, rowspan=2, padx=5, pady=10, columnspan=3)
        return button

    # Nowa metoda uruchamiająca nagrywanie
    def start_recording(self):
        self.screen_recorder = rec_t.ScreenRecorder()
        self.screen_recorder.start_record()

    # Nowa metoda zatrzymująca nagrywanie
    def stop_recording(self):
        if hasattr(self, 'screen_recorder'):  # Upewnij się, że instancja istnieje
            self.screen_recorder.stop_record()

if __name__ == "__main__":
    app = ttk.Window("io_app", "superhero", resizable=(True, True))
    app.geometry("900x500")
    IoFront(app)
    app.mainloop()
