#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Date          : 2025-08-28
# Author        : Lancelot PINCET
# GitHub        : https://github.com/LancelotPincet
# Library       : rootLP
# Module        : main

"""
This function can decorate the main function of a script.
"""



# %% Libraries
from corelp import folder, selfkwargs, kwargsself, resources_dir, Path
from rootlp import print, Section, user_inputs
import time
import functools
import os
from datetime import datetime
import tkinter as tk
from tkinter import filedialog
import types
import marimo as mo



# %% Function
def main() :
    '''
    This function can decorate the main function of a script.
    User inputs parameters shoud be put in the beginning of the main file, and the decorated function will recognize them.
    Decorated function can change the values of these parameters with keyword arguments when called.
    Section can be created bellow the mainfunction.
    
    Global parameters
    -----------------
    import_path : Path or str or None
        Path where to import script data to process.
        If None, will manually ask user to select it.
        If not existent, will be ignored.
    export_path : Path or str or None
        Path where to export script data to process.
        A new folder will be created inside at the call time as name.
        If None, will save in import_path. If not existent, will be ignored.
        If a previous call was already made in this same folder, and new is False, will try to reload data from this last folder.
    new : bool
        Overrides Decorator new parameter.
    bulk : function
        function(import_path) that returns a dictionnary of {import_subfolder:export_subfolder} for multiple decorated function run.
        If bulk is not None, the decorated function will run with import_subfolder, export_subfolder instead of import_path, export_path (see below).
        The import_subfolders and export_subfolder are defined from import_path and export_path respectively (they are not absolute from root path).
    overnight : bool
        If True and exception occurs, will skip and pass to the next run in bulk processing. To use for example for overnight bulk processing.
    
    Examples
    --------
    >>> from root import main
    ...
    >>> import_path = None # will be asked via a GUI
    >>> export_path = None # will create inside import_path
    >>> new = False # True to create a new export folder, False to reload precalculated data
    >>> bulk = None # function(import_path) that returns a dictionnary of {import_subfolder:export_subfolder} for multiple decorated function run.
    >>> overnight= False # If True and exception occurs, will skip and pass to the next run in bulk processing.
    >>> main_string = "Hello from main!" # User input parameter
    ...
    >>> @main(new=True) # if previous new is not defined, new is defined here
    ... def myscript() :
    ...     print(main_string) # By default prints "Hello from main!"
    ...     result = mysection() # Section defined bellow, result can be reloaded from previous run
    ...     return result
    ...
    ... @main.section()
    ... def mysection() :
    ...     print("Hello from section!")
    ...     return True # Will be saved into export_path and can be reuploaded at next run with same inputs
    ...
    >>> # Launch
    >>> if __name__ == "__main__" :
    ...     myscript() # prints "Hello from main!"
    ...     myscript(main_string = "Hello changed!!") # prints "Hello changed!!" and loads section result from first run
    '''



    def decorator(func) :
        name = func.__name__

        # Get globals around function definition
        definition_globals = func.__globals__

        @functools.wraps(func)
        def wrapper(**overrides) -> None :

            # Creates new globals
            exec_globals = definition_globals.copy()
            exec_globals.update(overrides)
            _new = exec_globals.get("new", False)
            _overnight = exec_globals.get("overnight", False)

            # Creates new function
            new_func = types.FunctionType(
                func.__code__,
                exec_globals,
                name=name,
                argdefs=func.__defaults__,
                closure=func.__closure__,
            )

            # Getting paths
            ipath = exec_globals.get('import_path', "None")
            if ipath is None :
                with resources_dir() as path:
                    icon_path = path / "icon_pythonLP.png"
                root = tk.Tk()
                root.title("Select import path")
                img = tk.PhotoImage(file=icon_path)
                root.iconphoto(True, img)
                root._icon_img = img  # keep reference
                root.withdraw()
                root.update_idletasks()
                root.attributes("-topmost", True)
                root.update()
                root.focus_force()
                ipath = filedialog.askdirectory(title=f'Select import path for {name}')
                root.destroy()
                if not ipath :
                    print('Searching for import_path was cancelled', style='red')
                    raise ValueError('Searching for import_path was cancelled')
            epath = exec_globals.get('export_path', "None")
            if ipath != "None" :
                ipath = Path(ipath)
                exec_globals['import_path'] = ipath
            if epath != "None" :
                epath = ipath.parent if epath is None else Path(epath)

            # Creating new export path
            prefix = name.replace('.', '_')
            if epath != "None" :
                if _new :
                    base_path = folder(epath / (f'{prefix}_' + datetime.now().strftime("%Y-%m-%d-%Hh%Mmin%Ss")), warning=False)
                else :
                    #Searching for newest old folder
                    base_folder = None
                    _date = None
                    for f in epath.iterdir() :
                        if (not f.is_dir()) or (not f.name.startswith(f'{prefix}_')) :
                            continue
                        date_str = f.name.split('_')[-1]
                        date = datetime.strptime(date_str, "%Y-%m-%d-%Hh%Mmin%Ss")
                        if _date is None or date > _date :
                            _date, base_folder = date, f
                    base_path = base_folder if base_folder is not None else epath / (f'{prefix}_' + datetime.now().strftime("%Y-%m-%d-%Hh%Mmin%Ss"))
                epath = base_path / 'export_folder'
                exec_globals['export_path'] = epath
                if not epath.exists():
                    os.makedirs(epath) #creates folders until end
                if ipath != "None" :
                    ilink = base_path / 'import_folder'
                    if ilink.exists() or ilink.is_symlink():
                        ilink.unlink()
                    if os.name == "nt":
                        try :
                            ilink.symlink_to(ipath, ipath.is_dir())
                        except OSError :
                            print("Windows does not allow to create symlink, aborting. Consider using Windows in Developper mode.")
                    else:
                        ilink.symlink_to(ipath)
                md_file = epath / (name+'_log.md')
                html_file = epath / (name+'_log.html')
            else :
                md_file = None
                html_file = None

            # Defining bulk processing subfolders
            subfolders = {"" : ""} if wrapper.bulk is None else wrapper.bulk(**exec_globals)

            #Begining prints
            print_status = kwargsself(print)
            print.console = None
            print.file = md_file
            print(f'\n\n\n# **BEGIN {name}**\n')
            print(f"{time.ctime()}")
            if ipath != "None" :
                print(f'import_path : {ipath}\n')
            if epath != "None" :
                print(f'export_path : {epath}\n')

            # Bulk processing
            results = {} # {export_subfolder : fucntion result}
            for import_subfolder, export_subfolder in subfolders.items() :
                if ipath != "None" :
                    impath = ipath / import_subfolder
                    exec_globals["import_path"] = impath
                if epath != "None" :
                    expath = epath / export_subfolder
                    exec_globals["export_path"] = expath

                # Create export subfolder
                if not expath.exists() :
                    os.mkdir(expath)
                
                # Updating sections
                wrapper.section.parent_path = epath
                wrapper.section.path = expath
                wrapper.section.new = _new

                #Applying function
                print("\n---\n")
                subfolder_string = f"{export_subfolder}" if export_subfolder != "" else ""
                print(f'## **Launched script {subfolder_string}**\n')
                tic = time.perf_counter()
                try :
                    results[export_subfolder] = new_func()
            
                # Errors
                except Exception as e :
                    toc = time.perf_counter()
                    print.error()
                    print(f'\n## **{subfolder_string} took {toc-tic:.2f}s**')
                    print("\n---\n")
                    if not _overnight :
                        raise e

                # No error
                else :
                    toc = time.perf_counter()
                    print(f'\n## **{subfolder_string} took {toc-tic:.2f}s**')
                    print("\n---\n")

            # END
            print(time.ctime())
            print(f'# **END {name}**\n\n')
            print.export_html(html_file)
            selfkwargs(print, print_status)
            if wrapper.bulk is None :
                results = results[""]
            return results

        # Making sections
        section = Section()
        wrapper.section = section
        wrapper.bulk = None
        wrapper.export = lambda : main_export(name)
        wrapper.overview = lambda : main_overview(name)
        wrapper.rawcode = lambda *args : main_rawcode(name, *args)

        return wrapper
    return decorator



def main_export(name) :
    launch = mo.ui.run_button(label=f"**--->>> {name} <<<---**")
    launch.center()

    user_inputs(True)
    import_path = mo.ui.text(placeholder="copy-paste import path", full_width=True)
    export_path = mo.ui.text(placeholder="copy-paste export path", full_width=True)
    new = mo.ui.switch(value=True, label="**New**: check to create new processing folder each time [default: True]")
    overnight = mo.ui.switch(value=False, label="**Overnight**: check to ignore bulk processing errors [default: False]")
    parameters_execution = user_inputs()

    # Markdown output
    md_execution = f"""
# **{name} launch script**

---

## **Script execution inputs**

### Launch script button

{launch}

Execution logs will appear on the right panel -->

(Check user inputs parameters before launching)

### Execution parameters

**Import path** : Folder with data to process [default: will open a browse window]
{import_path}

**Export path** : Folder where to save [default: import path **parent**]
{export_path}

{mo.hstack([new, overnight])}
"""

    return launch, parameters_execution, mo.md(md_execution);



def main_overview(name) :
    string = f"""
# **{name} code overview**

In the next tab is defined the raw code for {name}, using functions from the custom package. You can use this notebook as a template to learn how to use these functions. For any help, please contact authors.

Below is the definition of this script main function (`{name}`), which can be identified by the `@main` decorator. All the logic of the script is orchestrated from this function.

A *main script function* generally aims to transform data stored on disk into processed data that is also saved back to disk. As such, it usually defines:
- a path **from which to import** the input data
- a path **where to save** the processed data

---

## **Sections and Checkpoints**

The processing logic is divided into **sections**, which are identified by the `@{name}.section` decorator.

Each section can be seen as a *checkpoint* in the pipeline:
- It computes intermediate data of interest
- These computations may be heavy or time-consuming
- Results are cached into a **dedicated folder**

Thanks to this mechanism, re-running the script on the same data allows previously computed results to be automatically loaded from disk, avoiding unnecessary recomputation.

The `section` decorator attaches a new attribute named `path` (of type `pathlib.Path`) to the decorated function. This attribute points to the directory associated with the section, where cached data and intermediate outputs are stored.

---

## **Bulk Processing and Batches**

Another feature of the `@main` decorator is support for **bulk processing**.

The basic use case is to define a single import directory that contains one batch of data to process. However, it is also possible to define a function that:
- selects subfolders based on specific criteria
- returns a list of independent import subfolders
This function is stored as `{name}.bulk`.

Each of these subfolders is treated as a separate **batch** and can be processed in a single run.

A typical use case is to launch a large processing job overnight after collecting sufficient data during the day. In this scenario, faulty batches can be skipped to avoid interrupting the processing of the remaining batches.

---

## **Export Directory Structure**

In the export directory, a dedicated **processing folder** is created for each run.
This folder is named using the launch timestamp (e.g. hour and date) to clearly distinguish multiple runs.

Inside this processing folder, three subfolders are created:

- **import_folder**
  A symbolic link to the `import_path`, allowing easy identification of the input data used.

- **export_folder**
  Contains all processed data, organized by batch and by section.

- **_outputs**
  Contains symbolic links to selected output files of interest, grouped by file type and batch.

---

## **Export Folder Layout**

Inside the `export_folder`:
- One folder is created per **batch**
- Inside each batch folder, one folder is created per **section**
- These section folders store cached data, intermediate results, and section-specific outputs

The overall structure of the `export_path` directory is as follows:

```text
export_path/
├── import_path/ (by default export_path is the parent of import_path)
│   ├── import_data.xx
│   └── ...
└── extract_signals_YYYY-MM-DD-HHhMMminSSs/
    ├── import_folder -> /path/to/import_path (symlink)
    ├── export_folder/
    │   ├── batch_00/
    │   │   ├── 000_section/
    │   │   │   ├── cache_hash.pkl/
    │   │   │   ├── output_00.xx/
    │   │   │   └── ...
    │   │   ├── 001_section/
    │   │   │   ├── cache_hash.pkl/
    │   │   │   ├── output_00.xx/
    │   │   │   └── ...
    │   │   └── ...
    │   ├── batch_01/
    │   │   ├── 000_section/
    │   │   └── ...
    │   └── ...
    └── _outputs/
        ├── output_file_00/
        │   ├── batch_00.xx (symlink)
        │   ├── batch_01.xx (symlink)
        │   └── ...
        ├── output_file_01/
        │   ├── batch_00.xx (symlink)
        │   ├── batch_01.xx (symlink)
        │   └── ...
        └── ...
```

---

## **Execution Parameters**

The `@main` decorator adds several execution parameters to the function call:

1. **`import_path`** and **`export_path`**
   - If set to `None`, a file dialog prompts the user to select an import directory
   - The export path is then automatically defined as the **parent directory** of the import path
   - Paths are passed to the function as `pathlib.Path` objects for improved usability

2. **`new`** (`bool`)
   - If `True`, a new processing folder is created using the current launch timestamp
   - If `False`, the most recent processing folder is reused

3. **`overnight`** (`bool`)
   - If `True`, errors in individual batches are skipped
   - This allows long-running bulk processing jobs to continue without interruption
"""
    return mo.md(string)



def main_rawcode(name, showcode) :
    string = f"""
# **{name} raw code**

---

{showcode}
"""
    return mo.md(string)



# %% Test function run
if __name__ == "__main__":
    from corelp import test
    test(__file__)