import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.toast import ToastNotification

from get_data import get_data_locally as get_data

class IoFront(ttk.Frame):
    def __init__(self, master_window):
        super().__init__(master_window, padding=(20, 10))
        self.grid(row=0, column=0)

        #kontener z listą zapisanych spotkań
        self.left_container = ttk.LabelFrame(self,text="spotkania")
        self.left_container.pack(padx=5, pady=10, side=LEFT, fill=Y)
        #dodanie listy spotkań
        self.tree = self.create_treeview()


        self.right_container = ttk.Frame(self)

        #kontener z menu i przyciskiem do nagrywania nowego spotkania
        self.new_record_container = ttk.LabelFrame(self.right_container,text="nowe nagranie")
        self.quality_menu = self.create_quality_menu()
        self.start_recording_button()
        self.new_record_container.pack(padx=5, pady=10)

        #kontener z przyciskami akcji do wybranego spotkania
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

        data = get_data.get_data_locally() #importowanie danych

        # for i in self.data:
        #     if (int(i[0]) % 2 == 1):
        #         tree.insert("", "end", values=i, tags="change_bg")
        #     else:
        #         tree.insert("", "end", values=i)
        #     tree.bind("<<TreeviewSelect>>", self.tree_on_click_element)

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
        button.grid(row=3, column=1, rowspan=2, padx=5, pady= 10,columnspan=3)
        return button

    def open_in_browser_button(self):
        button = ttk.Button(master=self.action_container, width=20, text="Open in browser")
        button.grid(row=3, column=1, rowspan=2, padx=5, pady= 10,columnspan=3)
        return button

    def delete_recording_button(self):
        button = ttk.Button(master=self.action_container, width=20, text="Delete recording")
        button.grid(row=5, column=1, rowspan=2, padx=5, pady=10, columnspan=3)
        return button

if __name__ == "__main__":
    app = ttk.Window("io_app","superhero",resizable=(True,True))
    app.geometry("900x500")
    IoFront(app)
    app.mainloop()