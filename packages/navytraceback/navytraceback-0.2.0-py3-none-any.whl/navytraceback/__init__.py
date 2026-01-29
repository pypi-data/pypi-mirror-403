import sys
import traceback
import os
import datetime
import time
import types

# --- CONFIGURATION ---
BSOD_NAVY = "\033[48;2;0;0;130m" 
BSOD_WHITE = "\033[97m"
RESET = "\033[0m"
CLEAR_SCREEN = "\033[2J\033[H"

# State Flag
_SAFE_MODE = False

def get_desktop_path():
    path = os.path.join(os.path.expanduser("~"), "Desktop")
    if not os.path.exists(path):
        return os.getcwd() 
    return path

def scan_libraries(tb, exc_type, exc_value):
    lib_status = {}
    if tb:
        all_vars = {**tb.tb_frame.f_globals, **tb.tb_frame.f_locals}
        for name, val in all_vars.items():
            if isinstance(val, types.ModuleType):
                pkg_name = val.__name__.split('.')[0]
                if not pkg_name.startswith("_") and pkg_name != "builtins":
                    lib_status[pkg_name] = 'O'
    if exc_type is ModuleNotFoundError and exc_value.name:
        lib_status[exc_value.name] = 'X'
    return lib_status

def interactive_bsod(exc_type, exc_value, tb):
    # --- VISUAL TOGGLE ---
    if not _SAFE_MODE:
        # Full Experience: Clear screen, Navy Blue background
        sys.stderr.write(BSOD_NAVY + CLEAR_SCREEN)
        # Fill background to prevent gaps
        for _ in range(50):
            sys.stderr.write(" " * 120 + "\n")
        sys.stderr.write(CLEAR_SCREEN)
        sys.stderr.write(BSOD_NAVY + BSOD_WHITE)
    else:
        # Safe Mode: Just reset colors, do NOT clear screen
        # We add a separator line so it stands out from previous logs
        sys.stderr.write(RESET + "\n" + "-"*60 + "\n")

    # --- COMMON LOGIC (Runs in both modes) ---
    sys.stderr.write("\n" + "An exception occured".center(60, " ") + "\n\n")
    sys.stderr.write("This script has ran into a problem and has been force-closed.\n\n")
    
    # In safe mode, we might want to be less verbose, but you said keep it same.
    sys.stderr.write("The error might have been a one-time error, if it still persists,\n")
    sys.stderr.write("please troubleshoot the problem by debugging or ask for help.\n\n")
    sys.stderr.write(f"Error Code: {exc_type.__name__}: {exc_value}\n\n")
    
    try:
        sys.stderr.write("Create a dump file in your desktop? Y/N ")
        sys.stderr.flush()
        choice = input().strip().upper()
    except EOFError:
        choice = 'N'
        
    if choice == 'Y':
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"CRASH_DUMP_{timestamp}.txt"
            filepath = os.path.join(get_desktop_path(), filename)
            
            dump_content = ""
            
            # Error Chain
            error_chain = []
            current_err = exc_value
            while current_err:
                error_chain.append(current_err)
                current_err = current_err.__cause__ or current_err.__context__
            error_chain.reverse() 
            
            for i, err in enumerate(error_chain):
                err_name = type(err).__name__
                err_msg = str(err)
                if i > 0: dump_content += "\n" + "-"*40 + "\n\n"
                dump_content += f"ERROR:: TRACEBACK error (Sequence #{i+1})\n"
                dump_content += f"               DETAIL:: {err_name}\n"
                dump_content += f"                               DETAILNAME:: {err_msg}\n"
            
            # Library Status
            dump_content += "\n" + "-"*40 + "\n\n"
            dump_content += "LIBRARIES::\n"
            libraries = scan_libraries(tb, exc_type, exc_value)
            if libraries:
                for lib_name, status in libraries.items():
                    dump_content += f"                    {lib_name} = {status}\n"
            else:
                dump_content += "                    (No specific libraries detected)\n"
                
            sys.stderr.write("\nDump file created...")
            time.sleep(1) 
            with open(filepath, "w") as f:
                f.write(dump_content)
            sys.stderr.write(f" [OK]\nLocation: {filepath}\n")

        except Exception:
            sys.stderr.write("\n[FAILURE] Dump file has been force-stopped due to a problem\n")
            
    sys.stderr.write(RESET + "\n")

# --- TOGGLE CONTROLS ---

def safe_mode(enabled=True):
    """
    If enabled=True: Disables the Blue Screen background but keeps the 
                     interactive dump file logic.
    If enabled=False: Returns to full Blue Screen mode.
    """
    global _SAFE_MODE
    _SAFE_MODE = enabled

# Activate immediately
sys.excepthook = interactive_bsod