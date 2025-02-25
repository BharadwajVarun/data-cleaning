import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd

# Global variables
df = None
file_path = None
checkbox_vars = {}
categorical_columns = []  # Global list to track categorical columns

def open_file_dialog():
    global df, file_path
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if file_path:
        try:
            df = pd.read_csv(file_path)
            display_excel_info(df)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while reading the file:\n{e}")
    else:
        messagebox.showwarning("No File Selected", "You didn't select any file.")

def display_excel_info(df):
    global checkbox_vars
    checkbox_vars = {}

    # Clear existing widgets in info_frame_inner
    for widget in info_frame_inner.winfo_children():
        widget.destroy()
    
    # Create headers
    headers = ["Select", "Column", "Data Type", "Null Values"]
    for col_num, header in enumerate(headers):
        header_label = tk.Label(info_frame_inner, text=header, font=('Arial', 12, 'bold'), bg='#f8f9fa', anchor='w')
        header_label.grid(row=0, column=col_num, padx=10, pady=5, sticky='w')
    
    # Display column information with checkboxes
    for row_num, col in enumerate(df.columns, start=1):
        var = tk.BooleanVar()
        checkbox = tk.Checkbutton(info_frame_inner, variable=var, bg='#ffffff', font=('Arial', 12))
        checkbox.grid(row=row_num, column=0, padx=10, pady=5, sticky='w')
        
        col_label = tk.Label(info_frame_inner, text=col, anchor='w', bg='#ffffff', font=('Arial', 12))
        col_label.grid(row=row_num, column=1, padx=10, pady=5, sticky='w')
        
        data_type = str(df[col].dtype)
        data_type_label = tk.Label(info_frame_inner, text=data_type, anchor='w', bg='#ffffff', font=('Arial', 12))
        data_type_label.grid(row=row_num, column=2, padx=10, pady=5, sticky='w')
        
        null_values = df[col].isna().sum()
        null_values_label = tk.Label(info_frame_inner, text=null_values, anchor='w', bg='#ffffff', font=('Arial', 12))
        null_values_label.grid(row=row_num, column=3, padx=10, pady=5, sticky='w')
        
        checkbox_vars[col] = var

def delete_selected():
    global df
    selected_columns = [col for col, var in checkbox_vars.items() if var.get()]
    
    if selected_columns:
        df.drop(columns=selected_columns, inplace=True)
        display_excel_info(df)
        messagebox.showinfo("Success", "Selected columns have been deleted. Remember to download the cleansed dataset.")

def remove_duplicates():
    global df
    if df.duplicated().any():
        df.drop_duplicates(inplace=True)
        display_excel_info(df)
        messagebox.showinfo("Success", "Duplicates have been removed. Remember to download the cleansed dataset.")
    else:
        messagebox.showinfo("No Duplicates", "No duplicates found in the dataset.")

def type_of_dataset():
    global df
    
    for widget in dataset_type_frame.winfo_children():
        widget.destroy()
    
    categorical_cols = df.select_dtypes(include=['category']).columns.tolist()  
    numerical_columns = df.select_dtypes(include=['number']).columns.tolist()
    
    # Highlight numerical columns
    for col in numerical_columns:
        highlight_column(col)
    
    info_message = f"Categorical Columns: {', '.join(categorical_cols) if categorical_cols else 'None'}\n"
    info_message += f"Numerical Columns: {', '.join(numerical_columns) if numerical_columns else 'None'}"
    
    info_label = tk.Label(dataset_type_frame, text=info_message, font=('Arial', 12), bg='#f8f9fa', justify=tk.LEFT, anchor='w')
    info_label.pack(pady=10, padx=10, anchor='w')

def highlight_column(col):
    # Highlight numerical columns in info_frame
    for row_num, widget in enumerate(info_frame_inner.winfo_children(), start=1):
        if isinstance(widget, tk.Label) and widget.cget("text") == col:
            widget.config(bg='#d3f2d0')  # Very subtle green background for numerical columns
            break

def handle_null():
    global df
    threshold = len(df) * (2/3)
    columns_to_delete = df.columns[df.isnull().sum() > threshold]
    
    if not columns_to_delete.empty:
        df.drop(columns=columns_to_delete, inplace=True)
        display_excel_info(df)
        messagebox.showinfo("Success", f"Columns {', '.join(columns_to_delete)} with more than 2/3 null values have been deleted.")
    else:
        messagebox.showinfo("No Columns Deleted", "No columns found with more than 2/3 null values.")

def handle_outliers():
    global df
    outliers_removed = False
    numerical_cols = df.select_dtypes(include=['number']).columns.tolist()
    
    for col in numerical_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        if df[(df[col] < lower_bound) | (df[col] > upper_bound)].any().any():
            df = df[(df[col] >= lower_bound) & (df[col] <= upper_bound)]
            outliers_removed = True
    
    if outliers_removed:
        display_excel_info(df)
        messagebox.showinfo("Success", "Outliers have been removed.")
    else:
        messagebox.showinfo("No Outliers", "No outliers found in the dataset.")

def replace_null():
    global df
    selected_columns = [col for col, var in checkbox_vars.items() if var.get()]
    
    if selected_columns:
        for col in selected_columns:
            if df[col].dtype == 'object':  # Check if the column is categorical
                mode_value = df[col].mode()[0]
                df[col] = df[col].fillna(mode_value)
            else:
                mean_value = df[col].mean()
                df[col] = df[col].fillna(mean_value)
        
        display_excel_info(df)
        messagebox.showinfo("Success", "Null values have been replaced in the selected columns.")
    else:
        messagebox.showwarning("No Columns Selected", "Please select columns to replace null values.")

def convert_datatype():
    global df, checkbox_vars, categorical_columns

    selected_columns = [col for col, var in checkbox_vars.items() if var.get()]
    
    if selected_columns:
        # Create a dialog window for datatype conversion selection
        convert_window = tk.Toplevel(root)
        convert_window.title("Convert Datatype")
        convert_window.geometry("300x200")
        convert_window.configure(bg='#f8f9fa')
        
        def handle_conversion(selection):
            nonlocal convert_window
            convert_window.destroy()
            
            if selection == "to string":
                for col in selected_columns:
                    df[col] = df[col].astype(str)
            elif selection == "to date":
                for col in selected_columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            elif selection == "to categorical":
                for col in selected_columns:
                    df[col] = df[col].astype('category')
                    if col not in categorical_columns:  # Track categorical columns
                        categorical_columns.append(col)
            
            display_excel_info(df)
            messagebox.showinfo("Convert Datatype", f"Columns {', '.join(selected_columns)} converted to {selection}.")
        
        # Create buttons for datatype conversion options with subtle styling
        string_button = tk.Button(convert_window, text="to string", command=lambda: handle_conversion("to string"), font=('Arial', 12), bg="#cfe2f3", fg="black", width=20, pady=5)
        string_button.pack(pady=5)
        
        date_button = tk.Button(convert_window, text="to date", command=lambda: handle_conversion("to date"), font=('Arial', 12), bg="#cfe2f3", fg="black", width=20, pady=5)
        date_button.pack(pady=5)
        
        categorical_button = tk.Button(convert_window, text="to categorical", command=lambda: handle_conversion("to categorical"), font=('Arial', 12), bg="#cfe2f3", fg="black", width=20, pady=5)
        categorical_button.pack(pady=5)
        
        cancel_button = tk.Button(convert_window, text="Cancel", command=convert_window.destroy, font=('Arial', 12), bg="#e06666", fg="white", width=20, pady=5)
        cancel_button.pack(pady=10)
    else:
        messagebox.showwarning("No Columns Selected", "Please select columns to convert their datatype.")

def download_cleaned():
    global df
    if df is not None:
        save_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")], initialfile="cleansed_dataset.csv")
        if save_path:
            df.to_csv(save_path, index=False)
            messagebox.showinfo("Success", f"Cleaned dataset saved to {save_path}")
    else:
        messagebox.showwarning("No Data", "No data to save. Please load a dataset first.")

root = tk.Tk()
root.title("Data Preprocessing Application")
root.geometry("1200x800")
root.configure(bg='#f8f9fa')

# Title label
title_label = tk.Label(root, text="Data Preprocessing Application", font=('Arial', 20, 'bold'), bg='#f8f9fa')
title_label.pack(pady=10)

# Info frame
info_frame = tk.Frame(root, bg='#f8f9fa')
info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Canvas for scrollable info frame
canvas = tk.Canvas(info_frame, bg='#f8f9fa')
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Scrollbar for the canvas
scrollbar = tk.Scrollbar(info_frame, orient=tk.VERTICAL, command=canvas.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# Frame inside the canvas
info_frame_inner = tk.Frame(canvas, bg='#ffffff')
canvas.create_window((0, 0), window=info_frame_inner, anchor='nw')

# Configure canvas scrolling
canvas.configure(yscrollcommand=scrollbar.set)
info_frame_inner.bind("<Configure>", lambda event: canvas.configure(scrollregion=canvas.bbox("all")))

# Dataset type frame
dataset_type_frame = tk.Frame(root, bg='#f8f9fa')
dataset_type_frame.pack(side=tk.TOP, fill=tk.X, pady=10)

# Button frame
button_frame = tk.Frame(root, bg='#f8f9fa')
button_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10)

# File open button
open_button = tk.Button(button_frame, text="Open CSV File", command=open_file_dialog, font=('Arial', 12), bg="#6fa3ef", fg="white", width=20)
open_button.pack(pady=5)

# Feature buttons with styling
features = [
    ("Remove Duplicates", remove_duplicates),
    ("Type of Dataset", type_of_dataset),
    ("Delete Selected", delete_selected),
    ("Handle Null", handle_null),
    ("Handle Outliers", handle_outliers),
    ("Replace Null", replace_null),
    ("Change Datatype", convert_datatype),
    ("Download Cleansed", download_cleaned),
]

for (text, command) in features:
    button = tk.Button(button_frame, text=text, command=command, font=('Arial', 12), bg="#6fa3ef", fg="white", width=20)
    button.pack(pady=5)

root.mainloop()
