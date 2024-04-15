import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from tkcalendar import DateEntry
import re
import sqlite3
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import json
from fpdf import FPDF
from datetime import datetime


class TaskManagementApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Task Management")

        self.window_width = 800
        self.window_height = 600
        self.center_window()

        self.department_values = ['Calitate', 'Dezvoltare', 'IT', 'Inginerie', 'Logistica', 'Management', 'Mentenanta',
                                  'Resurse Umane']
        self.priority_values = ["Urgent & Important", "Urgent & NOT Important", "NOT Urgent & Important",
                                "NOT Urgent & NOT Important"]

        # Create form controls
        self.txtName = PlaceholderEntry(root, placeholder="ex: Alexandru Popa")
        self.cmbDepartment = ttk.Combobox(root, values=self.department_values)
        self.txtProject = PlaceholderEntry(root, placeholder="ex: PS07")
        self.txtDescription = PlaceholderText(root, height=5,
                                              placeholder="ex: Suport pentru uscare in cuptoare pana la 100°C")
        self.cmbJobPriority = ttk.Combobox(root, values=self.priority_values)
        self.txtInputData = PlaceholderEntry(root, placeholder="ex: C:\\Research_Development\\01_Proiect")
        self.txtDeadline = DateEntry(root)

        # Arrange form controls
        self.form_controls = [self.txtName, self.cmbDepartment, self.txtProject, self.txtDescription,
                              self.cmbJobPriority, self.txtInputData, self.txtDeadline]

        for i, control in enumerate(self.form_controls):
            control.grid(row=i, column=1, padx=10, pady=5, sticky="ew")

        labels = ["Name:", "Department:", "Project:", "Description:",
                  "Job Priority:", "Input Data:", "Deadline:"]

        for i, label_text in enumerate(labels):
            tk.Label(root, text=label_text).grid(row=i, column=0, padx=10, pady=5, sticky="w")

        # Create buttons
        btn_reset = tk.Button(root, text="Reset", command=self.reset_form)
        btn_reset.grid(row=len(self.form_controls), column=0, pady=10)

        btn_save = tk.Button(root, text="Save", command=self.save_data)
        btn_save.grid(row=len(self.form_controls), column=1, pady=10)

        # Database setup
        self.setup_database()

    def center_window(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - self.window_width) // 2
        y = (screen_height - self.window_height) // 2
        self.root.geometry(f"{self.window_width}x{self.window_height}+{x}+{y}")

    def validate_form(self):
        name_pattern = r'^[a-zA-Z ]+$'
        fields = [
            ("Name", self.txtName, name_pattern),
            ("Department", self.cmbDepartment, self.department_values),
            ("Project", self.txtProject, None),
            ("Description", self.txtDescription, None),
            ("Job Priority", self.cmbJobPriority, self.priority_values),
            ("Input Data", self.txtInputData, None),
            ("Deadline", self.txtDeadline, None)
        ]

        for field_name, field_widget, validation_rule in fields:
            field_widget.config(background="white")
            if validation_rule:
                if not self.validate_input(field_widget.get(), validation_rule):
                    messagebox.showinfo(field_name + " Error", "Invalid input for " + field_name)
                    field_widget.config(background="red")
                    field_widget.focus_set()
                    return False
        return True

    def validate_input(self, value, pattern):
        if pattern:
            if isinstance(pattern, str):
                return bool(re.match(pattern, value))
            elif isinstance(pattern, list):
                return value in pattern
        return True

    def reset_form(self):
        for control in self.form_controls:
            if isinstance(control, PlaceholderEntry):
                if control.get() != control.placeholder:
                    control.delete(0, tk.END)
                control.delete_placeholder()
                control.config(background="white", fg=control.default_fg_color)
            elif isinstance(control, PlaceholderText):
                if control.get("1.0", "end-1c") != control.placeholder:
                    control.delete("1.0", tk.END)
                control.delete_placeholder()
                control.config(background="white", fg=control.default_fg_color)
            elif isinstance(control, tk.Text):
                if control.get("1.0", "end-1c") != control.placeholder:
                    control.delete("1.0", tk.END)
                control.config(background="white", fg=control.default_fg_color)
            else:
                control.delete(0, tk.END)
                control.config(background="white")

    def save_data(self):
        if self.validate_form():
            data = {
                "Name": self.txtName.get(),
                "Department": self.cmbDepartment.get(),
                "Project": self.txtProject.get(),
                "Description": self.txtDescription.get("1.0", tk.END),
                "Job Priority": self.cmbJobPriority.get(),
                "Input Data": self.txtInputData.get(),
                "Deadline": self.txtDeadline.get()
            }

            # Generate file names
            current_date = datetime.now().strftime("%Y-%m-%d")
            name = self.txtName.get().replace(" ", "_")
            json_filename = f"{current_date}_{name}.json"
            pdf_filename = f"{current_date}_{name}.pdf"

            # Export data to JSON file
            with open(json_filename, 'w') as json_file:
                json.dump(data, json_file, indent=4)

            # Convert JSON file to PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)

            # Add data to PDF
            with open(json_filename, 'r') as json_file:
                data_json = json.load(json_file)
                for key, value in data_json.items():
                    if key == "Description":
                        pdf.cell(200, 10, txt=f"{key}: ", ln=True)
                        description_lines = value.split("\n")
                        for line in description_lines:
                            pdf.multi_cell(0, 10, txt=line)
                    else:
                        pdf.cell(200, 10, txt=f"{key}: {value}", ln=True)

            pdf.output(pdf_filename)

            # Insert data into SQLite database
            conn = sqlite3.connect('task_management.db')
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO tasks (name, department, project, description, job_priority, input_data, deadline)
                              VALUES (?, ?, ?, ?, ?, ?, ?)''', tuple(data.values()))
            conn.commit()
            conn.close()

            self.reset_form()

            messagebox.showinfo("Success", "Data saved successfully!")
        else:
            return

    def setup_database(self):
        conn = sqlite3.connect('task_management.db')
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS tasks
                          (id INTEGER PRIMARY KEY, name TEXT, department TEXT, project TEXT, description TEXT,
                          job_priority TEXT, input_data TEXT, deadline TEXT)''')
        conn.close()


class PlaceholderEntry(tk.Entry):
    def __init__(self, master=None, placeholder="", color='grey'):
        super().__init__(master)

        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = self['fg']

        self.bind("<FocusIn>", self.on_focus_in)
        self.bind("<FocusOut>", self.on_focus_out)

        self.put_placeholder()

    def put_placeholder(self):
        self.insert(0, self.placeholder)
        self.config(fg=self.placeholder_color)

    def on_focus_in(self, _):
        if self.get() == self.placeholder:
            self.delete(0, "end")
            self.config(fg=self.default_fg_color)

    def on_focus_out(self, _):
        if not self.get():
            self.put_placeholder()

    def delete_placeholder(self):
        if self.get() == self.placeholder:
            self.delete(0, "end")
            self.config(fg=self.default_fg_color)


class PlaceholderText(tk.Text):
    def __init__(self, master=None, placeholder="", color='grey', **kwargs):
        super().__init__(master, **kwargs)

        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = self.cget("fg")

        self.put_placeholder()

        self.bind("<FocusIn>", self.on_focus_in)
        self.bind("<FocusOut>", self.on_focus_out)

    def put_placeholder(self):
        self.insert("1.0", self.placeholder)
        self.config(fg=self.placeholder_color)

    def on_focus_in(self, _):
        if self.get("1.0", "end-1c") == self.placeholder:
            self.delete("1.0", "end")
            self.config(fg=self.default_fg_color)

    def on_focus_out(self, _):
        if not self.get("1.0", "end-1c"):
            self.put_placeholder()

    def delete_placeholder(self):
        if self.get("1.0", "end-1c") == self.placeholder:
            self.delete("1.0", "end")
            self.config(fg=self.default_fg_color)


def export_to_pdf(data):
    file_name = "task_data.pdf"
    c = canvas.Canvas(file_name, pagesize=letter)
    text = "\n".join([f"{key}: {value}" for key, value in data.items()])
    c.drawString(100, 750, text)
    c.save()
    messagebox.showinfo("PDF Export", f"Data exported to {file_name}")


if __name__ == "__main__":
    root = tk.Tk()
    app = TaskManagementApp(root)
    root.mainloop()
