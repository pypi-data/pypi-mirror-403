# py_me

py_me is a Python library that provides modules for audio manipulation (music_me) and Tkinter GUI helpers (tk_me).

## Version

**3.5.2** - released on 2026-01-27

## Changes

- new function in tk_me and os_me
- complete overhaul of tk_me

## tk_me
### Example:
```python
from py_me import tk_me

win = tk_me.create_window("hi", "100x100") 
def exit_app():
    win.destroy()
tk_me.create_button("exit", 0, 0, "Arial", 14, exit_app)  
win.mainloop()
```
### Functions
- import_script_window(window_name, window_size, import_file)  
- create_window(window_name, window_size)
- create_label(text, x, y, font, size)  
- create_button(text, x, y, font, size, command)  
- create_text_window(height, width, x, y)  
- error_window()
- destroy_widget(widget)
- import_tk_window(window_name, tk_file, label_text, button_text)
- create_slider(min, max, command, x, y)

## music_me
### Example:
```python
from py_me import music_me

music_me.loop_soundtrack(2, "my\\beat.mp3")            
elem = music_me.musical_element(1, "my\\sound.wav", 12)  
music_me.stop_element_after(elem, 10)                  
```
### Functions
- loop_soundtrack(speed, file)  
- musical_element(speed, file, wait_time=0)  
- pitched_musical_element(speed, pitch, file, wait_time=0)  
- stop_element_after(element, seconds_after_start)  
- stop_all_after(delay_seconds)  
- set_element_volume(element, volume, delay) 
- set_master_volume(volume, delay)

## project_me
### Example:
```python
from py_me import project_me

project_me.create_project()
```

### Function
- create_project() 

## os_me
### Example:
```python
from py_me import os_me

a = os_me.path.FileHunter("example.py")
b = os_me.path.FileHunter("second\\example.py")
os_me.file.execution_sequence([a, b], ignore_error=False, list_erros=False)
```

### API overview
- details:
  - helper
  - configuration fields (log_file, timeline_file, encoding, language, enable_logging, enable_rich_traceback, auto_snapshot_on_edit, avoid_duplicate_snapshots, timestamp_format, custom_logger, silent_FileHunter)
- file:
  - replace(path, content)
  - create(new_path, content="")
  - add(path, content)
  - execution_sequence(paths: list, ignore_error: bool = False, list_erros: bool = False)
- path:
  - FileHunter(relative_path) -> str | None
  - FileHunter_inverse(relative_path, start=None) -> str | None
  - FileHunter_SUPER(relative_path) -> str | None
  - FileHunter_TrueOrFalse(relative_path) -> bool
  - TIMELINE:
    - get_version
    - get_content
    - get_TIMELINE
    - show_TIMELINE
    - del_TIMELINE
    - run_version
    - del_all
- utilidades:
  - registrar_log(message)
- os_me:
  - create_dir_tree

## Dependencies
- pygame
- pydub (requires FFmpeg for many formats)

## Installation

```bash
pip install py-me
```