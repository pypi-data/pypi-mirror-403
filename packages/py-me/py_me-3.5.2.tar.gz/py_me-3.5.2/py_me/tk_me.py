import tkinter as tk
import random as ram
import sys
import threading
import os

class optional:
    pass

class TkMeError(Exception):
  def __init__(self, exception):
    super().__init__(exception)
    self.exception = exception

class Callable:
    pass
    
class NoReturn:
    pass

class tk_me:
    """
    Utilities to make creating Tk apps faster and less repetitive.
    tk_me provides helper functions to create common Tk widgets and
    small helper windows that simulate terminal behavior and other effects.

    Methods (English names, Portuguese aliases preserved at end):
        import_script_window(window_name, window_size, script_path)
        create_window(window_name, window_size)
        create_label(text, x, y, font, size)
        create_button(text, x, y, font, size, command)
        create_text_window(height, width, x, y)
        error_window()
        destroy_widget(widget)
        import_tk_window(window_name, script_path, label_text, button_text)
        create_slider(min_val, max_val, command, x, y)
    """

    def import_script_window(window_name: str, window_size: str, script_path: str) -> NoReturn:
        """
        Create a Tk window that runs a Python script with redirected print/input.

        Args:
            window_name (str): Window title.
            window_size (str): Window geometry like "1000x700".
            script_path (str): Path to the Python file to execute.

        Behavior:
            - creates a window that simulates a terminal
            - redirects print and stderr to a large Text widget
            - simulates input() using Entry widgets below the run button
            - provides a button to start/reset execution and a status label

        Example:
            >>> from py_me import tk_me
            >>> tk_me.import_script_window("win1", "1000x700", "myscript.py")

        Returns:
            None
        """
        try:
            window = tk.Tk()
            window.title(window_name)
            window.geometry(window_size)

            status_label = tk.Label(window, text=f"enjoy {window_name}")
            status_label.pack(pady=20)

            output = tk.Text(window, height=30, width=100)
            output.pack()

            class Redirector:
                def __init__(self, widget):
                    self.widget = widget
                def write(self, text):
                    self.widget.insert(tk.END, text)
                    self.widget.see(tk.END)
                def flush(self):
                    pass

            sys.stdout = Redirector(output)
            sys.stderr = Redirector(output)

            info_label = tk.Label(window, text="Click the button below to start. Enter inputs in the fields under the button and press Enter.")
            info_label.pack(pady=10)

            entry_main = tk.Entry(window)
            entry_main.pack()

            entries = []
            current_step = [0]

            def create_entries(qty):
                for i in range(qty):
                    new_entry = tk.Entry(window)
                    new_entry.pack()
                    new_entry.config(state='disabled')
                    entries.append(new_entry)
                if entries:
                    entries[0].config(state='normal')

            def reset_entries():
                current_step[0] = 0
                for e in entries:
                    e.delete(0, tk.END)
                    e.config(state='disabled')
                if entries:
                    entries[0].config(state='normal')

            def fake_input(prompt=''):
                idx = current_step[0]
                if idx >= len(entries):
                    output.insert(tk.END, "\n")
                    reset_entries()
                    return ""
                ent = entries[idx]
                output.insert(tk.END, f"{prompt}\n")
                ent.config(state="normal")
                ent.focus()
                val_var = tk.StringVar()
                def confirm(event=None):
                    val = ent.get().strip()
                    if val:
                        val_var.set(val)
                    else:
                        output.insert(tk.END, "empty!\n")
                ent.bind("<Return>", confirm)
                window.wait_variable(val_var)
                current_step[0] += 1
                if current_step[0] < len(entries):
                    entries[current_step[0]].config(state='normal')
                else:
                    output.insert(tk.END, "\n")
                    reset_entries()
                return val_var.get()

            def run_code():
                status_label.config(text="running... press button to reset if needed.")
                try:
                    if getattr(sys, 'frozen', False):
                        base_dir = sys._MEIPASS
                    else:
                        base_dir = os.path.dirname(__file__)
                    script_full = os.path.join(base_dir, script_path)
                    with open(script_full, "r", encoding="utf-8") as f:
                        content = f.read()
                        exec(content, {**globals(), 'input': fake_input})
                except Exception as e:
                    status_label.config(text=f"Error: {e}")

            def click():
                current_step[0] = 0
                for e in entries:
                    e.delete(0, tk.END)
                    e.config(state='disabled')
                if entries:
                    entries[0].config(state='normal')
                thread = threading.Thread(target=run_code)
                thread.start()

            run_button = tk.Button(window, text="start/reset", command=click)
            run_button.pack(pady=10)
            create_entries(1)
            window.mainloop()
        except Exception as p:
            raise TkMeError(f"An error occurred during execution: {p}") from p

    def create_window(window_name: str, window_size: str) -> tk.Tk:
        """
        Create a simple Tk window.

        Args:
            window_name (str): Title of the window.
            window_size (str): Geometry string like "800x600".

        Behavior:
            - creates a new Tk window instance
            - sets the window title to the provided name
            - sets the window geometry to the specified size
            - restores stdout and stderr before creating the window

        Example:
            >>> from py_me import tk_me
            >>> root = tk_me.create_window("My App", "800x600")
            >>> root.mainloop()

        Returns:
            tkinter.Tk: created window instance.
        """
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        try:
            window = tk.Tk()
            window.title(window_name)
            window.geometry(window_size)
            return window
        except Exception as e:
            raise TkMeError(f"The tk window could not be created due to an unexpected error: {e}") from e

    def create_label(text: str, x: int, y: int, font: str, size: int) -> tk.Label:
        """
        Create and place a Tk Label widget.

        Args:
            text (str): The text to display in the label.
            x (int): X-coordinate position on the parent window.
            y (int): Y-coordinate position on the parent window.
            font (str): Font family name (e.g., "Arial", "Helvetica").
            size (int): Font size in points.

        Behavior:
            - restores stdout and stderr before creating the label
            - creates a Label widget with the specified text and font
            - places the label at the given (x, y) coordinates using .place()
            - raises TkMeError if creation fails

        Example:
            >>> from py_me import tk_me
            >>> root = tk_me.create_window("App", "600x400")
            >>> lbl = tk_me.create_label("Hello World", 50, 100, "Arial", 14)
            >>> root.mainloop()

        Returns:
            tkinter.Label: The created Label widget.
        """
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        try:
            lbl = tk.Label(text=text, font=(font, size))
            lbl.place(x=x, y=y)
            return lbl
        except Exception as e:
            raise TkMeError(f"It was not possible to create the label because an unexpected error occurred: {e}") from e

    def create_button(text: str| None, x: int, y: int, font: str, size: int, command: Callable, color: str, color_bg: str) -> tk.Button:
        """
        Create and place a Tk Button widget.

        Args:
            text (str or None): Button text to display (can be empty string).
            x (int): X-coordinate position on the parent window.
            y (int): Y-coordinate position on the parent window.
            font (str): Font family name (e.g., "Arial", "Helvetica").
            size (int): Font size in points.
            command (Callable): Function or method to call when the button is clicked.
            color (str): Text color name (e.g., "white", "black", "#FF0000").
            color_bg (str): Background color name (e.g., "blue", "green", "#00FF00").

        Behavior:
            - restores stdout and stderr before creating the button
            - creates a Button widget with the specified text, font, and colors
            - if text is empty string, creates button without text
            - places the button at the given (x, y) coordinates using .place()
            - binds the provided command function to the click event
            - raises TkMeError if creation fails

        Example:
            >>> from py_me import tk_me
            >>> root = tk_me.create_window("App", "600x400")
            >>> def on_click():
            >>>     print("Button clicked!")
            >>> btn = tk_me.create_button("Click Me", 100, 150, "Arial", 12, on_click, "white", "blue")
            >>> root.mainloop()

        Returns:
            tkinter.Button: The created Button widget.
        """
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        try:
            if text != "":
                btn = tk.Button(text=text, command=command, font=(font, size), fg=color, bg=color_bg)
                btn.place(x=x, y=y)
                return btn
            else:
                btn = tk.Button(command=command, font=(font, size))
                btn.place(x=x, y=y)
                return btn
        except Exception as e:
            raise TkMeError(f"It was not possible to create the button because an unexpected error occurred: {e}") from e 

    def create_text_widget(height: int, width: int, x: int, y: int) -> tk.Text:
        """
        Create and place a Tk Text widget.

        Args:
            height (int): Height of the Text widget in number of visible lines.
            width (int): Width of the Text widget in approximate number of characters.
            x (int): X-coordinate position on the parent window.
            y (int): Y-coordinate position on the parent window.

        Behavior:
            - restores stdout and stderr before creating the text widget
            - creates a Text widget with the specified dimensions
            - places the text widget at the given (x, y) coordinates using .place()
            - raises TkMeError if creation fails

        Example:
            >>> from py_me import tk_me
            >>> root = tk_me.create_window("App", "600x400")
            >>> txt = tk_me.create_text_widget(10, 40, 50, 100)
            >>> txt.insert("1.0", "Hello World")
            >>> root.mainloop()

        Returns:
            tkinter.Text: The created Text widget.
        """
        try:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
            txt = tk.Text(height=height, width=width)
            txt.place(x=x, y=y)
            return txt
        except Exception as e:
            raise TkMeError(f"It was not possible to create the text window because an unexpected error occurred: {e}") from e

    def error_window() -> NoReturn:
        """
        Create a full-screen-like 'error' window that continuously randomizes 
        the font family and size of an "error" label for visual/demo effects.

        Args:
            None

        Behavior:
            - creates a large 1600x700 window titled "error"
            - displays a centered "error" label that changes font family and size randomly
            - updates the label every 100 milliseconds with a new random font and size
            - includes a "close" button to destroy the window
            - restores the original stdout and stderr streams before starting
            - runs indefinitely until the window is closed

        Example:
            >>> from py_me import tk_me
            >>> tk_me.error_window()  # launches the chaotic error animation window

        Returns:
            None
        """
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        window = tk.Tk()
        window.title("error")
        window.geometry("1600x700")
        status_label = tk.Label(text="", font=("Arial", 14))
        status_label.pack()
        def random_error():
            a = ram.randint(1,5)
            nu = ram.randint(1,500)
            fonts = {1: "Arial", 3: "Calibri", 4: "Times New Roman"}
            chosen = fonts.get(a, "Verdana")
            status_label.config(text="error", font=(chosen, nu))
            window.after(100, random_error)
        random_error()
        def close():
            window.destroy()
        btn = tk.Button(text="close", font=("Arial", 14), command=close)
        btn.place(x=1000, y=100)
        window.mainloop()

    def destroy_widget(widget: tk.Widget) -> NoReturn:
        """
        Safely destroy a Tkinter widget and clean up related resources.

        Args:
            widget (tk.Widget): The Tkinter widget instance to be destroyed.

        Behavior:
            - restores the original stdout and stderr streams
            - calls the widget's .destroy() method to remove it from the window
            - raises a TkMeError with details if destruction fails for any reason

        Example:
            >>> from py_me import tk_me
            >>> root = tk_me.create_window("hi", "600x600)
            >>> lbl = create_label("hi", 0, 0, Arial, 14)
            >>> tk_me.destroy_widget(lbl)  # removes the label from the window

        Returns:
            None
        """
        try:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
            widget.destroy()
        except Exception as e:
            raise TkMeError(f"It was not possible to destroy {widget} due to an unexpected error: {e}") from e

    def import_tk_window(window_name: str, script_path: str, label_text: str, button_text: str) -> NoReturn:
        """
        Create a simple 500x500 Tkinter window with a label and a button 
        that executes an external Python script when clicked.

        The executed script will receive the 'window' object in its global scope.

        Args:
            window_name (str): Title of the created window.
            script_path (str): Path to the Python script file that will be executed.
            label_text (str): Text to display in the window's label.
            button_text (str): Text to display on the run button.

        Behavior:
            - creates a fixed-size window of 500x500 pixels
            - places a label and a button in the center of the window
            - when the button is clicked:
                - closes/destroys the current window
                - reads the target script file
                - executes the script using exec() with the original window object available
            - restores the original stdout and stderr before running the script
            - raises a TkMeError with details if the script execution fails

        Example:
            >>> from py_me import tk_me
            >>> tk_me.import_tk_window(
            >>>     "Launch Game",
            >>>     "game.py",
            >>>     "Ready to play?",
            >>>     "Start Game Now"
            >>> )

        Returns:
            None
        """
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        window = tk.Tk()
        window.title(window_name)
        window.geometry("500x500")
        label = tk.Label(window, text=label_text, font=("Arial", 14))
        label.place(x=150, y=200)
        def run():
            window.destroy()
            try:
                with open(script_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    exec(content, {"window": window})
            except Exception as e:
                raise TkMeError(f"Error running script: {e}") from e
        btn = tk.Button(window, text=button_text, font=("Arial", 14), command=run)
        btn.place(x=150, y=250)
        window.mainloop()

    def create_slider(num_min: int, num_max: int, command: Callable, x: int, y: int, orient: str | optional = "horizontal") -> tk.Scale:
        """
        Quickly create and place a Tkinter Scale (slider) widget.

        Args:
            num_min (int): Minimum value of the slider.
            num_max (int): Maximum value of the slider.
            command (Callable): Function to call whenever the slider value changes.
            x (int): X-coordinate to place the slider on the parent window.
            y (int): Y-coordinate to place the slider on the parent window.
            orient (str, optional): Slider orientation. 
                "horizontal" (default) or "vertical".

        Behavior:
            - creates a Scale widget with the specified range and orientation
            - automatically places it at the given (x, y) coordinates using .place()
            - sets a default length of 400 pixels
            - calls the provided command function on value change

        Example:
            >>> from py_me import tk_me
            >>> root = tk_me.create_window("hi", "600x600)
            >>> def on_change(value):
            >>>     print(f"Slider value: {value}")
            >>> slider = tk_me.create_slider(0, 100, on_change, 50, 100)
            >>> root.mainloop()

        Returns:
            tk.Scale: The created and placed Scale (slider) widget.
        """
        try:
            slider = tk.Scale(from_=num_min, to=num_max, orient= orient, command=command, length=400)
            slider.place(x=x, y=y)
            return slider
        except Exception as e:
            raise TkMeError(f"It was not possible to create the slider due to an error that occurred: {e}") from e
    
    def create_listbox(height: int, width: int , font: str , size: int, selectmode: any, List: list, insert: any | optional = tk.END) -> tk.Listbox:
        """
        Create a Tkinter Listbox widget pre-filled with items from a list.

        Args:
            height (int): Height of the Listbox in number of visible lines.
            width (int): Width of the Listbox in approximate number of characters.
            font (str): Name of the font family to use (e.g. "Arial", "Helvetica").
            size (int): Font size in points.
            selectmode (any): Selection mode. Common values:
                - tk.SINGLE: select only one item (default behavior)
                - tk.MULTIPLE: allow multiple selection
                - tk.EXTENDED: extended selection with Shift/Ctrl
            List (list): List of items (usually strings) to insert into the Listbox.
            insert (any, optional): Position where items will be inserted.
                Defaults to tk.END (append to the end).

        Behavior:
            - creates a Listbox widget with the specified dimensions, font and selection mode
            - inserts all items from the provided list at the chosen position
            - does not automatically pack/grid/place the widget or add a scrollbar

        Example:
            >>> from py_me import tk_me
            >>> root = tk_me.create_window("hi", "600x600)
            >>> fruits = ["Apple", "Banana", "Orange", "Strawberry"]
            >>> lb = tk_mecreate_listbox(8, 30, "Arial", 12, SINGLE, fruits, insert=END)
            >>> lb.pack(pady=10)

        Returns:
            tk.Listbox: The created and populated Listbox widget.
        """
        listbox = tk.Listbox(
            height= height,
            width= width,
            font= (font, size),
            selectmode= selectmode
        )
        for Any in List:
            listbox.insert(insert, Any)
        
        return listbox