"""
Macer: Machine-learning accelerated Atomic Computational Environment for automated Research workflows
Copyright (c) 2025 The Macer Package Authors
Author: Soungmin Bae <soungminbae@gmail.com>
License: MIT
"""

import curses
import os
import sys
import glob
import traceback
import yaml
from pathlib import Path

from macer.utils.validation import check_poscar_format
from macer.relaxation.optimizer import relax_structure
from macer.molecular_dynamics.cli import run_md_simulation
from macer.molecular_dynamics.gibbs import run_gibbs_workflow
from macer.utils.logger import Logger
from macer.defaults import (
    DEFAULT_MODELS, _model_root, DEFAULT_DEVICE, DEFAULT_FF, 
    resolve_model_path, DEFAULT_MLFF_DIRECTORY, _user_yaml_path, 
    _default_yaml_path, AVAILABLE_MODELS, MODEL_SOURCES
)
from macer.calculator.factory import get_available_ffs, ALL_SUPPORTED_FFS
from macer.utils.model_manager import get_installed_models
# from macer import __version__

# Utilities imports
from macer.utils.md_tools import traj2xdatcar, md_summary, calculate_conductivity
from macer.utils.model_tools import convert_model_precision, list_models
from macer.utils.struct_tools import vasp4to5
from macer.utils.viz_tools import plot_md_log, plot_rdf, plot_phonon_band, plot_gruneisen_band

# Phonopy imports
from macer.cli.phonopy_main import run_phonon_band_cli
from macer.phonopy.qha import run_qha_workflow
from macer.phonopy.sscha import run_sscha_workflow
from macer.phonopy.relax_unit import run_relax_unit
from macer.phonopy.thermal_conductivity import run_tc_workflow
from macer.phonopy.dynaphopy import run_dynaphopy_workflow

# Pydefect imports
from macer.pydefect.cpd import run_cpd_workflow
from macer.pydefect.defect import run_defect_workflow
from macer.pydefect.full import run_full_workflow

# Copy of the logo for independent display
MACER_LOGO = r"""
███╗   ███╗  █████╗   ██████╗ ███████╗ ██████╗
████╗ ████║ ██╔══██╗ ██╔════╝ ██╔════╝ ██╔══██╗
██╔████╔██║ ███████║ ██║      █████╗   ██████╔╝
██║╚██╔╝██║ ██╔══██║ ██║      ██╔══╝   ██╔══██╗
██║ ╚═╝ ██║ ██║  ██║ ╚██████╗ ███████╗ ██║  ██║
╚═╝     ╚═╝ ╚═╝  ╚═╝  ╚═════╝ ╚══════╝ ╚═╝  ╚═╝
ML-accelerated Atomic Computational Environment for Research
"""

# Global Runtime Configuration
RUNTIME_CONFIG = {
    "device": DEFAULT_DEVICE,
    "ff": None,  # Will be set in init_runtime_config
    "models": DEFAULT_MODELS.copy(),
    "mlff_directory": DEFAULT_MLFF_DIRECTORY
}

def init_runtime_config(start_ff=None):
    """Initialize configuration with available defaults."""
    installed_ffs = get_available_ffs()
    
    if start_ff:
        RUNTIME_CONFIG["ff"] = start_ff
    elif DEFAULT_FF in installed_ffs:
        RUNTIME_CONFIG["ff"] = DEFAULT_FF
    elif installed_ffs:
        RUNTIME_CONFIG["ff"] = installed_ffs[0]
    else:
        RUNTIME_CONFIG["ff"] = "mattersim" # Absolute fallback
        
    # Global directory defaults
    RUNTIME_CONFIG.setdefault("global_execution_dir", None)
    RUNTIME_CONFIG.setdefault("global_output_dir", None)

    # Relaxation defaults
    RUNTIME_CONFIG.setdefault("isif", 3)
    RUNTIME_CONFIG.setdefault("fmax", 0.01)
    RUNTIME_CONFIG.setdefault("max_steps", None)
    RUNTIME_CONFIG.setdefault("optimizer", "FIRE")

    # MD defaults
    RUNTIME_CONFIG.setdefault("md_ensemble", "npt")
    RUNTIME_CONFIG.setdefault("md_temp", 300.0)
    RUNTIME_CONFIG.setdefault("md_press", 0.0)
    RUNTIME_CONFIG.setdefault("md_nsteps", 5000)
    RUNTIME_CONFIG.setdefault("md_tstep", 2.0)
    RUNTIME_CONFIG.setdefault("md_save_every", 100)
    
    # Gibbs defaults
    RUNTIME_CONFIG.setdefault("gibbs_temp_start", 100.0)
    RUNTIME_CONFIG.setdefault("gibbs_temp_end", 1000.0)
    RUNTIME_CONFIG.setdefault("gibbs_temp_step", 50.0)
    RUNTIME_CONFIG.setdefault("gibbs_nsteps", 50000)
    RUNTIME_CONFIG.setdefault("gibbs_equil_steps", 10000)
    RUNTIME_CONFIG.setdefault("gibbs_ensemble", "npt")
    RUNTIME_CONFIG.setdefault("gibbs_dim", "2 2 2")
    RUNTIME_CONFIG.setdefault("gibbs_qha_ref", None)
    
    # Phonopy defaults
    RUNTIME_CONFIG.setdefault("phonopy_dim", None)
    RUNTIME_CONFIG.setdefault("phonopy_mesh", "20 20 20")
    RUNTIME_CONFIG.setdefault("phonopy_temp", 300.0)
    RUNTIME_CONFIG.setdefault("phonopy_tmax", 1300.0)
    RUNTIME_CONFIG.setdefault("phonopy_tolerance", 0.01)
    RUNTIME_CONFIG.setdefault("phonopy_min_length", 20.0)
    RUNTIME_CONFIG.setdefault("phonopy_tc_method", "br")
    
    # Finite-Temp (DynaPhoPy) defaults
    RUNTIME_CONFIG.setdefault("ft_temp", 300.0)
    RUNTIME_CONFIG.setdefault("ft_md_steps", 8000)
    RUNTIME_CONFIG.setdefault("ft_md_equil", 2000)
    RUNTIME_CONFIG.setdefault("ft_time_step", 2.0)
    RUNTIME_CONFIG.setdefault("ft_dim", None)
    RUNTIME_CONFIG.setdefault("ft_mem", 1000)
    RUNTIME_CONFIG.setdefault("ft_resolution", 0.05)

    # Gruneisen defaults
    RUNTIME_CONFIG.setdefault("gru_gmin", None)
    RUNTIME_CONFIG.setdefault("gru_gmax", None)
    RUNTIME_CONFIG.setdefault("gru_fmin", None)
    RUNTIME_CONFIG.setdefault("gru_fmax", None)
    RUNTIME_CONFIG.setdefault("gru_filter", 3.0)

    # Pydefect defaults
    RUNTIME_CONFIG.setdefault("pydefect_formula", None)
    RUNTIME_CONFIG.setdefault("pydefect_mpid", None)
    RUNTIME_CONFIG.setdefault("pydefect_doping", "")
    RUNTIME_CONFIG.setdefault("pydefect_fmax", 0.03)
    RUNTIME_CONFIG.setdefault("pydefect_matrix", None)
    RUNTIME_CONFIG.setdefault("pydefect_min_atoms", 50)
    RUNTIME_CONFIG.setdefault("pydefect_max_atoms", 300)
    RUNTIME_CONFIG.setdefault("pydefect_analyze_symmetry", True)
    RUNTIME_CONFIG.setdefault("pydefect_energy_shift_target", 0.0)


# --- Helper Functions ---

def view_file(stdscr, file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
    except Exception as e:
        show_alert(stdscr, f"Error reading file: {e}")
        return

    curses.curs_set(0)
    height, width = stdscr.getmaxyx()
    pad_h = max(len(lines), height)
    pad_w = max(max((len(line) for line in lines), default=0) + 2, width)
    pad = curses.newpad(pad_h, pad_w)

    for i, line in enumerate(lines):
        pad.addstr(i, 0, line.rstrip()[:pad_w-1])

    scroll_y = 0
    scroll_x = 0
    
    while True:
        stdscr.erase()
        view_h = height - 2
        view_w = width
        
        header_str = f" Viewing: {os.path.basename(file_path)} ({len(lines)} lines) "
        stdscr.attron(curses.A_REVERSE)
        try:
            stdscr.addstr(0, 0, header_str.ljust(width))
            stdscr.addstr(height-1, 0, " [Arrows/PgUp/PgDn] Scroll  [q/ESC] Close ".ljust(width))
        except curses.error:
            pass
        stdscr.attroff(curses.A_REVERSE)

        stdscr.noutrefresh()
        
        try:
            pad.noutrefresh(scroll_y, scroll_x, 1, 0, view_h, view_w - 1)
        except curses.error:
            pass
        
        curses.doupdate()
        key = stdscr.getch()
        
        if key == ord('q') or key == 27:
            stdscr.clear()
            stdscr.refresh()
            break
        elif key == curses.KEY_UP:
            scroll_y = max(0, scroll_y - 1)
        elif key == curses.KEY_DOWN:
            scroll_y = min(max(0, len(lines) - view_h), scroll_y + 1)
        elif key == curses.KEY_LEFT:
            scroll_x = max(0, scroll_x - 5)
        elif key == curses.KEY_RIGHT:
            scroll_x = min(max(0, pad_w - width), scroll_x + 5)
        elif key == curses.KEY_PPAGE: # Page Up
            scroll_y = max(0, scroll_y - view_h)
        elif key == curses.KEY_NPAGE: # Page Down
            scroll_y = min(max(0, len(lines) - view_h), scroll_y + view_h)

def draw_header(stdscr, title):
    from macer import __version__
    height, width = stdscr.getmaxyx()
    stdscr.addstr(0, 0, f" Macer Interactive (v{__version__}) | Device: {RUNTIME_CONFIG['device']} | Active FF: {RUNTIME_CONFIG['ff']}", curses.A_REVERSE)
    stdscr.addstr(1, 0, f" {title}", curses.A_BOLD)
    stdscr.addstr(2, 0, "-" * (width - 1))

def show_intro(stdscr):
    curses.curs_set(0)
    stdscr.clear()
    height, width = stdscr.getmaxyx()
    
    # Draw Logo centered
    lines = MACER_LOGO.strip().split('\n')
    start_y = max(1, (height - len(lines)) // 2 - 2)
    
    for i, line in enumerate(lines):
        start_x = max(0, (width - len(line)) // 2)
        if start_y + i < height - 1:
            try:
                stdscr.addstr(start_y + i, start_x, line, curses.A_BOLD)
            except curses.error:
                pass
    
    from macer import __version__
    info_text = f"Machine-learning accelerated Atomic Computational Environment (v{__version__})"
    info_x = max(0, (width - len(info_text)) // 2)
    if start_y + len(lines) + 1 < height:
        try:
            stdscr.addstr(start_y + len(lines) + 1, info_x, info_text)
        except curses.error:
            pass
        
    press_key_text = "Press any key to start..."
    press_x = max(0, (width - len(press_key_text)) // 2)
    if height - 2 > 0:
        try:
            stdscr.addstr(height - 2, press_x, press_key_text, curses.A_BLINK)
        except curses.error:
            pass
        
    stdscr.refresh()
    stdscr.getch()
    stdscr.clear()
    stdscr.refresh()

def input_text(stdscr, title, prompt, default_val=""):
    curses.curs_set(1)
    stdscr.clear()
    draw_header(stdscr, title)
    
    try:
        stdscr.addstr(4, 4, prompt)
        val_str = str(default_val) if default_val is not None else ""
        stdscr.addstr(6, 4, f"Current: {val_str}")
        stdscr.addstr(8, 4, "> ")
    except curses.error:
        pass
    
    curses.echo()
    stdscr.refresh()
    
    inp_bytes = stdscr.getstr(8, 6, 60)
    inp = inp_bytes.decode('utf-8').strip()
    
    curses.noecho()
    curses.curs_set(0)
    
    if not inp:
        return default_val
    return inp

def show_alert(stdscr, msg):
    height, width = stdscr.getmaxyx()
    stdscr.attron(curses.A_BOLD)
    stdscr.attron(curses.A_REVERSE)
    try:
        stdscr.addstr(height // 2, max(0, (width - len(msg)) // 2), f" {msg} ")
        stdscr.addstr(height // 2 + 1, max(0, (width - 20) // 2), " Press any key... ")
    except curses.error:
        pass
    stdscr.attroff(curses.A_REVERSE)
    stdscr.attroff(curses.A_BOLD)
    stdscr.refresh()
    stdscr.getch()

# --- Configuration Editor ---

def user_config_editor(stdscr):
    curses.curs_set(0)
    idx = 0
    
    # Load initial config once
    try:
        if _user_yaml_path.exists():
            with open(_user_yaml_path, 'r') as f:
                config = yaml.safe_load(f) or {}
        else:
            config = {}
    except Exception:
        config = {}

    # Fill defaults
    config.setdefault('default_mlff', DEFAULT_FF)
    config.setdefault('device', DEFAULT_DEVICE)
    config.setdefault('mlff_directory', '')
    config.setdefault('models', DEFAULT_MODELS.copy())

    while True:
        height, width = stdscr.getmaxyx()
        curr_ff = config['default_mlff']
        curr_model = config['models'].get(curr_ff, "Default")
        
        options = [
            f"Default Force Field: {curr_ff}",
            f"Compute Device      : {config['device']}",
            f"MLFF Directory      : {config['mlff_directory'] or '(Not set)'}",
            f"Configure Model Files (per FF) : {curr_model}",
            "Save and Apply",
            "Reset configuration to defaults",
            "Back (Cancel)"
        ]

        stdscr.clear()
        draw_header(stdscr, "Default Setting Editor (~/.macer.yaml)")
        
        for i, opt in enumerate(options):
            style = curses.A_REVERSE if i == idx else curses.A_NORMAL
            if i == 4: style |= curses.A_BOLD # Make Save bold
            if i == 5: style |= curses.A_DIM # Make Reset dim/different
            prefix = " > " if i == idx else "   "
            try: stdscr.addstr(5 + i, 4, f"{prefix}{opt}", style)
            except curses.error: pass

        try:
            footer = " [Enter] Select  [m] Menu  [u] Utils  [s] Global Settings  [q] Back "
            stdscr.addstr(height-1, 0, footer.ljust(width - 1), curses.A_REVERSE)
        except curses.error: pass
            
        stdscr.refresh()
        key = stdscr.getch()
        
        if key == curses.KEY_UP: idx = max(0, idx - 1)
        elif key == curses.KEY_DOWN: idx = min(len(options) - 1, idx + 1)
        elif key == ord('m'): return "__MAIN_MENU__"
        elif key == ord('u'): return "__UTILITIES__"
        elif key == ord('s'): return "__SETTINGS__"
        elif key in [ord('q'), 27]: break
        elif key == 10 or key == 13: # Enter
            if idx == 0: # FF
                ffs = ["mace", "sevennet", "allegro", "mattersim", "fairchem", "orb"]
                sel = select_option(stdscr, "Select Default Force Field", ffs, config['default_mlff'])
                if sel: config['default_mlff'] = sel
            elif idx == 1: # Device
                sel = select_option(stdscr, "Select Default Device", ["cpu", "mps", "cuda"], config['device'])
                if sel: config['device'] = sel
            elif idx == 2: # Directory
                current_mlff_dir = config.get('mlff_directory', '')
                def mlff_info_func():
                    return [f"Current MLFF Directory: {current_mlff_dir or '(Not set, using package default)'}"]
                
                start_dir = current_mlff_dir if current_mlff_dir and os.path.exists(current_mlff_dir) else os.getcwd()
                val = file_browser(stdscr, start_dir, title="Select MLFF Directory", header_info_func=mlff_info_func, allow_dir_select=True)
                if val: config['mlff_directory'] = val if os.path.isdir(val) else os.path.dirname(val)
            elif idx == 3: # Models
                config['models'] = model_file_config_sub_menu(stdscr, config)
            elif idx == 4: # Save and Apply
                try:
                    with open(_user_yaml_path, 'w') as f:
                        yaml.dump(config, f, default_flow_style=False)
                    show_alert(stdscr, "Settings successfully saved to ~/.macer.yaml")
                    # Update runtime config immediately
                    RUNTIME_CONFIG['ff'] = config['default_mlff']
                    RUNTIME_CONFIG['device'] = config['device']
                    RUNTIME_CONFIG['mlff_directory'] = config['mlff_directory']
                    RUNTIME_CONFIG['models'] = config['models'].copy()
                    return # Exit after save
                except Exception as e:
                    show_alert(stdscr, f"Error saving: {e}")
            elif idx == 5: # Reset
                sel = select_option(stdscr, "Really reset configuration?", ["No, cancel", "Yes, reset to defaults"], "No, cancel")
                if sel == "Yes, reset to defaults":
                    try:
                        import shutil
                        import time
                        # Backup
                        if _user_yaml_path.exists():
                            timestamp = time.strftime("%Y%m%d_%H%M%S")
                            backup_path = _user_yaml_path.with_suffix(f".yaml.bak.{timestamp}")
                            shutil.move(_user_yaml_path, backup_path)
                            backup_msg = f" (Backup saved to {backup_path.name})"
                        else:
                            backup_msg = ""
                        
                        # Copy default
                        if _default_yaml_path.exists():
                            shutil.copy(_default_yaml_path, _user_yaml_path)
                            
                        show_alert(stdscr, f"Configuration reset successfully!{backup_msg}")
                        
                        # Reload into editor config
                        with open(_user_yaml_path, 'r') as f:
                            config = yaml.safe_load(f) or {}
                        # Re-apply defaults just in case
                        config.setdefault('default_mlff', DEFAULT_FF)
                        config.setdefault('device', DEFAULT_DEVICE)
                        config.setdefault('mlff_directory', '')
                        config.setdefault('models', DEFAULT_MODELS.copy())
                        
                    except Exception as e:
                        show_alert(stdscr, f"Error resetting: {e}")
            elif idx == 6: # Back
                break
        elif key == ord('q') or key == 27: break

def model_file_config_sub_menu(stdscr, config):
    models = config.get('models', {}).copy()
    ffs = ["mace", "sevennet", "allegro", "mattersim", "fairchem", "orb"]
    idx = 0
    default_ff = config.get('default_mlff')
    
    while True:
        height, width = stdscr.getmaxyx()
        stdscr.clear()
        draw_header(stdscr, "Configure Model Files")
        
        for i, ff in enumerate(ffs):
            curr = models.get(ff, "Default")
            # Add * if it matches the default force field
            marker = "*" if ff == default_ff else ""
            display_ff = f"{ff}{marker}"
            
            style = curses.A_REVERSE if i == idx else curses.A_NORMAL
            prefix = " > " if i == idx else "   "
            try: stdscr.addstr(5 + i, 4, f"{prefix}{display_ff:<10}: {curr}", style)
            except curses.error: pass
            
        try: 
            footer = " [Enter] Select Model  [q/ESC] Back "
            stdscr.addstr(height-1, 0, footer.ljust(width - 1), curses.A_REVERSE)
        except curses.error: pass
        
        stdscr.refresh()
        key = stdscr.getch()
        
        if key == curses.KEY_UP: idx = max(0, idx - 1)
        elif key == curses.KEY_DOWN: idx = min(len(ffs) - 1, idx + 1)
        elif key == ord('q') or key == 27: break
        elif key == 10 or key == 13:
            selected_ff = ffs[idx]
            
            # --- New Logic: Show candidates from AVAILABLE_MODELS first ---
            candidates = AVAILABLE_MODELS.get(selected_ff, [])
            installed_files = get_installed_models()
            
            options = []
            for c in candidates:
                # Determine target filename
                source_info = MODEL_SOURCES.get(c)
                target_name = source_info["target"] if source_info else (f"{c}.pth" if selected_ff == "sevennet" else c)
                
                # Check if installed
                # installed_files is a list of filenames
                if target_name in installed_files:
                    status = "[INSTALLED]"
                else:
                    status = "[DOWNLOADABLE]"
                
                # Format: "keyword   [STATUS]"
                options.append(f"{c:<30} {status}")

            options.append("[ Browse Local File ]")
            options.append("[ Cancel ]")
            
            sel = select_option(stdscr, f"Select {selected_ff.upper()} Model Candidate", options, None)
            
            if not sel or sel == "[ Cancel ]":
                continue
                
            if sel == "[ Browse Local File ]":
                search_dir = config.get('mlff_directory') or _model_root
                if not search_dir or not os.path.exists(search_dir):
                    search_dir = _model_root
                    
                sel_file = file_browser(stdscr, search_dir, title=f"Select {selected_ff.upper()} Model File")
                if sel_file and not os.path.isdir(sel_file):
                    models[selected_ff] = os.path.basename(sel_file)
            else:
                # User selected an API keyword from the list
                # e.g. "7net-omni                      [DOWNLOADABLE]"
                # We need to extract the keyword (first part)
                keyword = sel.split()[0] 
                
                # Resolve keyword to actual filename if possible
                source_info = MODEL_SOURCES.get(keyword)
                if source_info:
                    models[selected_ff] = source_info["target"]
                else:
                    # Fallback to keyword if not in sources (e.g. external)
                    models[selected_ff] = keyword
            
            return models
# --- File Browser ---

def file_browser(stdscr, start_dir=".", header_info_func=None, extra_key_handler=None, title=None, instruction=None, settings_func=None, allow_dir_select=False):
    current_dir = os.path.abspath(start_dir)
    curses.curs_set(0)
    stdscr.keypad(True)
    idx = 0
    offset = 0
    last_search = ""
    
    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        if title:
            stdscr.addstr(0, 0, f" {title}", curses.A_REVERSE)
        else:
            draw_header(stdscr, f"Browse: {current_dir}")
            
        current_y = 1 if title else 3
        
        if instruction:
            try:
                stdscr.addstr(current_y, 0, f" Target: {instruction}", curses.A_BOLD)
                current_y += 1
            except curses.error: pass

        try:
            stdscr.addstr(current_y, 0, f" Path: {current_dir}", curses.A_DIM)
            current_y += 2
        except curses.error: pass
        
        if header_info_func:
            info_lines = header_info_func()
            for i, line in enumerate(info_lines):
                try:
                    stdscr.addstr(current_y + i, 2, line)
                except curses.error: pass
            current_y += len(info_lines) + 1
            
        list_start_y = current_y
            
        try:
            footer = " [Enter] Select  [v] View  [/] Search (n/N)  [m] Menu  [u] Utils  [e] Edit  [q/ESC] Back "
            if extra_key_handler or settings_func:
                footer += " [s] Settings "
            stdscr.addstr(height-1, 0, footer.ljust(width - 1), curses.A_REVERSE)
        except curses.error:
            pass
        
        try:
            # Filter out hidden files/directories (starting with '.')
            entries = sorted([e for e in os.listdir(current_dir) if not e.startswith('.')])
        except PermissionError:
            stdscr.addstr(list_start_y + 1, 2, "Permission Denied!", curses.A_BOLD)
            stdscr.getch()
            return None

        items = ["~", ".."]
        if allow_dir_select:
            items.insert(0, ".")
        if settings_func:
            items.insert(0, "[ SETTINGS ]")
        
        items.insert(0, "__MAIN_MENU__")
            
        items += entries
        
        max_rows = height - list_start_y - 1 
        if max_rows < 1: max_rows = 1
        
        if idx < offset:
            offset = idx
        elif idx >= offset + max_rows:
            offset = idx - max_rows + 1
            
        for i in range(max_rows):
            list_idx = offset + i
            if list_idx >= len(items):
                break
            
            item_name = items[list_idx]
            display_name = item_name
            
            if item_name == "__MAIN_MENU__":
                display_name = "[ Go back to Main Menu ]"
                style = curses.A_BOLD | (curses.A_REVERSE if list_idx == idx else curses.A_NORMAL)
                prefix = "> " if list_idx == idx else "  "
            elif item_name == "[ SETTINGS ]":
                style = curses.A_BOLD | (curses.A_REVERSE if list_idx == idx else curses.A_NORMAL)
                prefix = "> " if list_idx == idx else "  "
            elif item_name == ".":
                display_name = "[ Select Current Directory ]"
                style = curses.A_BOLD | (curses.A_REVERSE if list_idx == idx else curses.A_NORMAL)
                prefix = "> " if list_idx == idx else "  "
            elif item_name == "~":
                display_name = "[ Go to Home Directory ]"
                style = curses.A_BOLD | (curses.A_REVERSE if list_idx == idx else curses.A_NORMAL)
                prefix = "> " if list_idx == idx else "  "
            else:
                full_path = os.path.join(current_dir, item_name)
                is_dir = os.path.isdir(full_path)
                if is_dir: display_name += "/"
                style = curses.A_REVERSE if list_idx == idx else curses.A_NORMAL
                prefix = "> " if list_idx == idx else "  "
            
            if len(display_name) > width - 4:
                display_name = display_name[:width-7] + "..."
                
            try:
                stdscr.addstr(list_start_y + i, 2, f"{prefix}{display_name}", style)
                # Highlight search matches in the displayed name
                if last_search and last_search.lower() in display_name.lower():
                    start_pos = display_name.lower().find(last_search.lower())
                    if start_pos != -1:
                        match_text = display_name[start_pos:start_pos + len(last_search)]
                        stdscr.addstr(list_start_y + i, 2 + len(prefix) + start_pos, match_text, style | curses.A_BOLD | curses.A_UNDERLINE)
            except curses.error:
                pass

        stdscr.refresh()
        key = stdscr.getch()
        
        if key == ord('q') or key == 27:
            return None
        elif key == ord('m'): return "__MAIN_MENU__"
        elif key == ord('u'): return "__UTILITIES__"
        elif key == ord('e'): return "__CONFIG_EDITOR__"
        elif key == curses.KEY_UP:
            idx = max(0, idx - 1)
        elif key == curses.KEY_DOWN:
            idx = min(len(items) - 1, idx + 1)
        elif key == ord('/'): # Search feature
            curses.curs_set(1)
            query = ""
            while True:
                try:
                    stdscr.addstr(height-1, 0, ("/" + query).ljust(width - 1), curses.A_REVERSE)
                    stdscr.move(height-1, len(query) + 1)
                except curses.error: pass
                stdscr.refresh()
                
                ch = stdscr.getch()
                if ch in [10, 13]: # Enter
                    if query: last_search = query
                    break
                elif ch == 27: # ESC
                    break
                elif ch in [curses.KEY_BACKSPACE, 127, 8]:
                    query = query[:-1]
                elif 32 <= ch <= 126:
                    query += chr(ch)
                
                # Incremental jump: move idx to first match
                if query:
                    for s_idx, item in enumerate(items):
                        if query.lower() in item.lower():
                            idx = s_idx
                            break
        elif key == ord('n'): # Next match
            if last_search:
                found = False
                for s_idx in range(idx + 1, len(items)):
                    if last_search.lower() in items[s_idx].lower():
                        idx = s_idx
                        found = True
                        break
                if not found: # Wrap around to start
                    for s_idx in range(0, idx + 1):
                        if last_search.lower() in items[s_idx].lower():
                            idx = s_idx
                            break
        elif key == ord('N'): # Previous match
            if last_search:
                found = False
                for s_idx in range(idx - 1, -1, -1):
                    if last_search.lower() in items[s_idx].lower():
                        idx = s_idx
                        found = True
                        break
                if not found: # Wrap around to end
                    for s_idx in range(len(items) - 1, idx - 1, -1):
                        if last_search.lower() in items[s_idx].lower():
                            idx = s_idx
                            break
        elif key == ord('v'): # View
            selected = items[idx]
            if selected in [".", "~", "..", "[ SETTINGS ]", "__MAIN_MENU__"]:
                continue
            full_path = os.path.join(current_dir, selected)
            if os.path.isfile(full_path):
                view_file(stdscr, full_path)
            else:
                show_alert(stdscr, "Cannot view directory.")
        elif key == 10 or key == 13: # Enter
            selected = items[idx]
            if selected == "__MAIN_MENU__":
                return "__MAIN_MENU__"
            if selected == "[ SETTINGS ]":
                if settings_func: settings_func(stdscr)
                continue
            if selected == ".":
                return current_dir
            if selected == "~":
                current_dir = os.path.expanduser("~")
                idx = 0
                offset = 0
                continue
            full_path = os.path.join(current_dir, selected)
            
            if os.path.isdir(full_path):
                current_dir = os.path.abspath(full_path)
                idx = 0
                offset = 0
            else:
                return full_path
        elif key == ord('s'):
            if settings_func: settings_func(stdscr)
        elif extra_key_handler:
            extra_key_handler(stdscr, key)

# --- Settings Menus ---

def select_option(stdscr, title, options, current_val):
    curses.curs_set(0)
    idx = 0
    for i, opt in enumerate(options):
        if opt == current_val:
            idx = i
            break
            
    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        draw_header(stdscr, title)
        try:
            stdscr.addstr(height-1, 0, " [Enter] Select  [q/ESC] Cancel ".ljust(width), curses.A_REVERSE)
        except curses.error:
            pass
        
        for i, opt in enumerate(options):
            style = curses.A_NORMAL
            prefix = "   "
            if i == idx:
                style = curses.A_REVERSE
                prefix = " > "
            
            marker = " (*)" if opt == current_val else ""
            
            try:
                stdscr.addstr(4 + i, 4, f"{prefix}{opt}{marker}", style)
            except curses.error: pass
            
        key = stdscr.getch()
        if key == ord('q') or key == 27:
            return None
        elif key == curses.KEY_UP:
            idx = max(0, idx - 1)
        elif key == curses.KEY_DOWN:
            idx = min(len(options) - 1, idx + 1)
        elif key == 10 or key == 13:
            selected = options[idx]
            if " (Not Installed)" in selected:
                continue
            return selected

def settings_menu(stdscr, current_path="."):
    curses.curs_set(0)
    idx = 0
    options = [
        "Change Active Force Field",
        "Change Compute Device",
        "Configure MLFF Directory (Search Path)",
        "Configure Model File (per FF)",
        "Global Execution Directory (Base)",
        "Global Output Directory (Specific)",
        "Back to Main Menu"
    ]
    
    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        draw_header(stdscr, "Global Settings")
        
        try:
            g_exe = RUNTIME_CONFIG.get('global_execution_dir') or "(Auto: Input Dir)"
            g_out = RUNTIME_CONFIG.get('global_output_dir') or "(Auto: Module Prefix)"
            g_mlff = RUNTIME_CONFIG.get('mlff_directory') or "(Default: macer/mlff-model)"
            stdscr.addstr(4, 4, f"Device: {RUNTIME_CONFIG['device']} | FF: {RUNTIME_CONFIG['ff']}")
            stdscr.addstr(5, 4, f"MLFF Dir  : {g_mlff}")
            stdscr.addstr(6, 4, f"Global Exe: {g_exe}")
            stdscr.addstr(7, 4, f"Global Out: {g_out}")
            stdscr.addstr(9, 4, "Current Model Paths:")
        except curses.error: pass

        row = 10
        for ff_key, model_val in RUNTIME_CONFIG['models'].items():
            model_display = model_val if model_val else "Default"
            try: stdscr.addstr(row, 6, f"- {ff_key}: {model_display}")
            except curses.error: pass
            row += 1
            if row > 14: break
            
        menu_start_y = row + 1
        for i, opt in enumerate(options):
            style = curses.A_REVERSE if i == idx else curses.A_NORMAL
            prefix = " > " if i == idx else "   "
            try: stdscr.addstr(menu_start_y + i, 4, f"{prefix}{opt}", style)
            except curses.error: pass

        try:
            footer = " [Enter] Select  [m] Menu  [u] Utils  [e] Edit Setting  [q] Back "
            stdscr.addstr(height-1, 0, footer.ljust(width - 1), curses.A_REVERSE)
        except curses.error: pass
            
        stdscr.refresh()
        key = stdscr.getch()
        if key == curses.KEY_UP: idx = max(0, idx - 1)
        elif key == curses.KEY_DOWN: idx = min(len(options) - 1, idx + 1)
        elif key == ord('m'): return "__MAIN_MENU__"
        elif key == ord('u'): return "__UTILITIES__"
        elif key == ord('e'): return "__CONFIG_EDITOR__"
        elif key in [ord('q'), 27]: break
        elif key == 10 or key == 13:
            if idx == 0: # Change FF
                installed_ffs = get_available_ffs()
                ff_map = {f"{f}{'' if f in installed_ffs else ' (Not Installed)'}": f for f in ALL_SUPPORTED_FFS}
                sel = select_option(stdscr, "Select Active Force Field", list(ff_map.keys()), next((k for k, v in ff_map.items() if v == RUNTIME_CONFIG['ff']), None))
                if sel:
                    selected_ff = ff_map[sel]
                    if selected_ff in installed_ffs: RUNTIME_CONFIG['ff'] = selected_ff
                    else: show_alert(stdscr, f"Force field '{selected_ff}' is not installed.")
            elif idx == 1: # Change Device
                sel = select_option(stdscr, "Select Compute Device", ["cpu", "mps", "cuda"], RUNTIME_CONFIG['device'])
                if sel: RUNTIME_CONFIG['device'] = sel
            elif idx == 2: # Configure MLFF Directory
                val = file_browser(stdscr, current_path, title="Configure MLFF Directory", instruction="Select Directory for MLFF Models")
                if val: RUNTIME_CONFIG['mlff_directory'] = val if os.path.isdir(val) else os.path.dirname(val)
            elif idx == 3: configure_models_menu(stdscr)
            elif idx == 4: # Global Exe
                val = file_browser(stdscr, current_path, title="Global Execution Directory", instruction="Select Base Workspace", allow_dir_select=True)
                if val: RUNTIME_CONFIG['global_execution_dir'] = val if os.path.isdir(val) else os.path.dirname(val)
            elif idx == 5: # Global Out
                val = input_text(stdscr, "Global Output Directory", "Enter specific directory name (leave empty for Auto):", RUNTIME_CONFIG.get('global_output_dir'))
                RUNTIME_CONFIG['global_output_dir'] = val if val else None
            elif idx == 6: break
        elif key == ord('q') or key == 27: break

def relax_settings_menu(stdscr):
    idx = 0
    options = ["ISIF Mode", "Force Criteria (Fmax)", "Max Iterations", "Optimizer", "Back"]
    while True:
        stdscr.clear()
        draw_header(stdscr, "Relaxation Settings")
        r_isif = RUNTIME_CONFIG.get('isif')
        r_fmax = RUNTIME_CONFIG.get('fmax')
        r_opt = RUNTIME_CONFIG.get('optimizer')
        try: stdscr.addstr(4, 4, f"Current: ISIF={r_isif}, Fmax={r_fmax}, Opt={r_opt}", curses.A_BOLD)
        except: pass
        for i, opt in enumerate(options):
            style = curses.A_REVERSE if i == idx else curses.A_NORMAL
            prefix = " > " if i == idx else "   "
            try: stdscr.addstr(6 + i, 4, f"{prefix}{opt}", style)
            except: pass
        stdscr.refresh()
        key = stdscr.getch()
        if key == curses.KEY_UP: idx = max(0, idx - 1)
        elif key == curses.KEY_DOWN: idx = min(len(options) - 1, idx + 1)
        elif key == 10 or key == 13:
            if idx == 0:
                opts = ["0: Single-point", "2: Ions only", "3: Ions+Shape+Volume", "4: Ions+Shape", "5: Shape", "6: Shape+Volume", "7: Volume only", "8: Ions+Volume"]
                sel = select_option(stdscr, "Select ISIF Mode", opts, next((s for s in opts if s.startswith(str(RUNTIME_CONFIG['isif'])+':')), opts[2]))
                if sel: RUNTIME_CONFIG['isif'] = int(sel.split(':')[0])
            elif idx == 1:
                val = input_text(stdscr, "Force Convergence", "Enter Fmax (eV/A):", RUNTIME_CONFIG['fmax'])
                try: RUNTIME_CONFIG['fmax'] = float(val)
                except: pass
            elif idx == 2:
                val = input_text(stdscr, "Max Iterations", "Enter max steps:", RUNTIME_CONFIG.get('max_steps') or "")
                try: RUNTIME_CONFIG['max_steps'] = int(val) if val else None
                except: pass
            elif idx == 3:
                sel = select_option(stdscr, "Select Optimizer", ["FIRE", "BFGS", "LBFGS", "MDMin", "GPMin", "CG", "QN"], RUNTIME_CONFIG['optimizer'])
                if sel: RUNTIME_CONFIG['optimizer'] = sel
            elif idx == 4: break
        elif key == ord('q') or key == 27: break

def md_settings_menu(stdscr):
    idx = 0
    options = ["Ensemble", "Temperature (K)", "Pressure (GPa)", "Time Step (fs)", "Steps", "Save Interval", "Back"]
    while True:
        stdscr.clear()
        draw_header(stdscr, "MD Settings")
        try: stdscr.addstr(4, 4, f"Current: {RUNTIME_CONFIG['md_ensemble'].upper()} @ {RUNTIME_CONFIG['md_temp']}K, {RUNTIME_CONFIG['md_press']}GPa", curses.A_BOLD)
        except: pass
        for i, opt in enumerate(options):
            style = curses.A_REVERSE if i == idx else curses.A_NORMAL
            prefix = " > " if i == idx else "   "
            try: stdscr.addstr(6 + i, 4, f"{prefix}{opt}", style)
            except: pass
        stdscr.refresh()
        key = stdscr.getch()
        if key == curses.KEY_UP: idx = max(0, idx - 1)
        elif key == curses.KEY_DOWN: idx = min(len(options) - 1, idx + 1)
        elif key == 10 or key == 13:
            if idx == 0:
                sel = select_option(stdscr, "Select Ensemble", ["npt", "nte", "nve"], RUNTIME_CONFIG['md_ensemble'])
                if sel: RUNTIME_CONFIG['md_ensemble'] = sel
            elif idx == 1:
                val = input_text(stdscr, "MD Temperature", "Enter K:", RUNTIME_CONFIG['md_temp'])
                try: RUNTIME_CONFIG['md_temp'] = float(val)
                except: pass
            elif idx == 2:
                val = input_text(stdscr, "MD Pressure", "Enter GPa:", RUNTIME_CONFIG['md_press'])
                try: RUNTIME_CONFIG['md_press'] = float(val)
                except: pass
            elif idx == 3:
                val = input_text(stdscr, "Time Step", "Enter fs:", RUNTIME_CONFIG['md_tstep'])
                try: RUNTIME_CONFIG['md_tstep'] = float(val)
                except: pass
            elif idx == 4:
                val = input_text(stdscr, "Steps", "Enter N:", RUNTIME_CONFIG['md_nsteps'])
                try: RUNTIME_CONFIG['md_nsteps'] = int(val)
                except: pass
            elif idx == 5:
                val = input_text(stdscr, "Save Interval", "Enter N:", RUNTIME_CONFIG['md_save_every'])
                try: RUNTIME_CONFIG['md_save_every'] = int(val)
                except: pass
            elif idx == 6: break
        elif key == ord('q') or key == 27: break

def gibbs_settings_menu(stdscr):
    idx = 0
    options = ["Start Temp (K)", "End Temp (K)", "Temp Step (K)", "MD Steps/T", "Equil Steps/T", "Ensemble", "Supercell Dim", "QHA Reference (Optional)", "Back"]
    while True:
        stdscr.clear()
        draw_header(stdscr, "Gibbs Free Energy Settings")
        try: 
            dim_str = RUNTIME_CONFIG.get('gibbs_dim') or "None"
            qha_str = os.path.basename(RUNTIME_CONFIG['gibbs_qha_ref']) if RUNTIME_CONFIG['gibbs_qha_ref'] else "None"
            stdscr.addstr(4, 4, f"Range: {RUNTIME_CONFIG['gibbs_temp_start']}-{RUNTIME_CONFIG['gibbs_temp_end']}K (d={RUNTIME_CONFIG['gibbs_temp_step']})", curses.A_BOLD)
            stdscr.addstr(5, 4, f"Dim: {dim_str} | QHA Ref: {qha_str}", curses.A_DIM)
        except: pass
        for i, opt in enumerate(options):
            style = curses.A_REVERSE if i == idx else curses.A_NORMAL
            prefix = " > " if i == idx else "   "
            try: stdscr.addstr(7 + i, 4, f"{prefix}{opt}", style)
            except: pass
        stdscr.refresh()
        key = stdscr.getch()
        if key == curses.KEY_UP: idx = max(0, idx - 1)
        elif key == curses.KEY_DOWN: idx = min(len(options) - 1, idx + 1)
        elif key == 10 or key == 13:
            if idx == 0:
                val = input_text(stdscr, "Start Temp", "Enter K:", RUNTIME_CONFIG['gibbs_temp_start'])
                try: RUNTIME_CONFIG['gibbs_temp_start'] = float(val)
                except: pass
            elif idx == 1:
                val = input_text(stdscr, "End Temp", "Enter K:", RUNTIME_CONFIG['gibbs_temp_end'])
                try: RUNTIME_CONFIG['gibbs_temp_end'] = float(val)
                except: pass
            elif idx == 2:
                val = input_text(stdscr, "Temp Step", "Enter K:", RUNTIME_CONFIG['gibbs_temp_step'])
                try: RUNTIME_CONFIG['gibbs_temp_step'] = float(val)
                except: pass
            elif idx == 3:
                val = input_text(stdscr, "MD Steps", "Enter N:", RUNTIME_CONFIG['gibbs_nsteps'])
                try: RUNTIME_CONFIG['gibbs_nsteps'] = int(val)
                except: pass
            elif idx == 4:
                val = input_text(stdscr, "Equil Steps", "Enter N:", RUNTIME_CONFIG['gibbs_equil_steps'])
                try: RUNTIME_CONFIG['gibbs_equil_steps'] = int(val)
                except: pass
            elif idx == 5:
                sel = select_option(stdscr, "Select Ensemble", ["npt", "nvt"], RUNTIME_CONFIG['gibbs_ensemble'])
                if sel: RUNTIME_CONFIG['gibbs_ensemble'] = sel
            elif idx == 6:
                val = input_text(stdscr, "Supercell Dim", "Enter '2 2 2':", RUNTIME_CONFIG['gibbs_dim'])
                if val: RUNTIME_CONFIG['gibbs_dim'] = val
            elif idx == 7:
                # Browse for thermal_properties.yaml
                start_dir = os.path.dirname(RUNTIME_CONFIG.get('global_execution_dir') or ".")
                val = file_browser(stdscr, start_dir, title="Select QHA Reference", instruction="Select thermal_properties.yaml")
                if val and os.path.isfile(val): RUNTIME_CONFIG['gibbs_qha_ref'] = val
                else: RUNTIME_CONFIG['gibbs_qha_ref'] = None
            elif idx == 8: break
        elif key == ord('q') or key == 27: break

def pydefect_settings_menu(stdscr):
    idx = 0
    options = ["Formula", "MP ID", "Doping", "Fmax", "Matrix", "Min Atoms", "Max Atoms", "Symmetry Toggle", "Energy Shift", "Back"]
    while True:
        stdscr.clear()
        draw_header(stdscr, "Pydefect Settings")
        try: stdscr.addstr(4, 4, f"Current: Formula={RUNTIME_CONFIG['pydefect_formula']}, MPID={RUNTIME_CONFIG['pydefect_mpid']}", curses.A_BOLD)
        except: pass
        for i, opt in enumerate(options):
            style = curses.A_REVERSE if i == idx else curses.A_NORMAL
            prefix = " > " if i == idx else "   "
            try: stdscr.addstr(6 + i, 4, f"{prefix}{opt}", style)
            except: pass
        stdscr.refresh()
        key = stdscr.getch()
        if key == curses.KEY_UP: idx = max(0, idx - 1)
        elif key == curses.KEY_DOWN: idx = min(len(options) - 1, idx + 1)
        elif key == 10 or key == 13:
            if idx == 0: RUNTIME_CONFIG['pydefect_formula'] = input_text(stdscr, "Formula", "Enter:", RUNTIME_CONFIG['pydefect_formula'])
            elif idx == 1: RUNTIME_CONFIG['pydefect_mpid'] = input_text(stdscr, "MP ID", "Enter:", RUNTIME_CONFIG['pydefect_mpid'])
            elif idx == 2: RUNTIME_CONFIG['pydefect_doping'] = input_text(stdscr, "Doping", "Enter elements:", RUNTIME_CONFIG['pydefect_doping'])
            elif idx == 3:
                val = input_text(stdscr, "Fmax", "Enter:", RUNTIME_CONFIG['pydefect_fmax'])
                try: RUNTIME_CONFIG['pydefect_fmax'] = float(val)
                except: pass
            elif idx == 4:
                val = input_text(stdscr, "Matrix", "Enter '2 2 2':", "")
                if val: RUNTIME_CONFIG['pydefect_matrix'] = [int(x) for x in val.split()]
            elif idx == 5:
                val = input_text(stdscr, "Min Atoms", "Enter:", RUNTIME_CONFIG['pydefect_min_atoms'])
                try: RUNTIME_CONFIG['pydefect_min_atoms'] = int(val)
                except: pass
            elif idx == 6:
                val = input_text(stdscr, "Max Atoms", "Enter:", RUNTIME_CONFIG['pydefect_max_atoms'])
                try: RUNTIME_CONFIG['pydefect_max_atoms'] = int(val)
                except: pass
            elif idx == 7: RUNTIME_CONFIG['pydefect_analyze_symmetry'] = not RUNTIME_CONFIG['pydefect_analyze_symmetry']
            elif idx == 8:
                val = input_text(stdscr, "Energy Shift", "Enter:", RUNTIME_CONFIG['pydefect_energy_shift_target'])
                try: RUNTIME_CONFIG['pydefect_energy_shift_target'] = float(val)
                except: pass
            elif idx == 9: break
        elif key == ord('q') or key == 27: break

def ft_settings_menu(stdscr):
    idx = 0
    options = ["Temperature (K)", "MD Steps", "Equil Steps", "Time Step (fs)", "Supercell Dim", "MEM Coeffs", "Resolution (THz)", "Back"]
    while True:
        stdscr.clear()
        draw_header(stdscr, "Finite-Temp Phonon Settings")
        try:
            dim_str = RUNTIME_CONFIG.get('ft_dim') or "(Auto)"
            stdscr.addstr(4, 4, f"Current: {RUNTIME_CONFIG['ft_temp']}K | MD: {RUNTIME_CONFIG['ft_md_steps']} (eq {RUNTIME_CONFIG['ft_md_equil']}) | Dim: {dim_str}", curses.A_BOLD)
        except: pass
        for i, opt in enumerate(options):
            style = curses.A_REVERSE if i == idx else curses.A_NORMAL
            prefix = " > " if i == idx else "   "
            try: stdscr.addstr(6 + i, 4, f"{prefix}{opt}", style)
            except: pass
        stdscr.refresh()
        key = stdscr.getch()
        if key == curses.KEY_UP: idx = max(0, idx - 1)
        elif key == curses.KEY_DOWN: idx = min(len(options) - 1, idx + 1)
        elif key == 10 or key == 13:
            if idx == 0:
                val = input_text(stdscr, "Temperature", "Enter K:", RUNTIME_CONFIG['ft_temp'])
                try: RUNTIME_CONFIG['ft_temp'] = float(val)
                except: pass
            elif idx == 1:
                val = input_text(stdscr, "MD Steps", "Enter N:", RUNTIME_CONFIG['ft_md_steps'])
                try: RUNTIME_CONFIG['ft_md_steps'] = int(val)
                except: pass
            elif idx == 2:
                val = input_text(stdscr, "Equil Steps", "Enter N:", RUNTIME_CONFIG['ft_md_equil'])
                try: RUNTIME_CONFIG['ft_md_equil'] = int(val)
                except: pass
            elif idx == 3:
                val = input_text(stdscr, "Time Step", "Enter fs:", RUNTIME_CONFIG['ft_time_step'])
                try: RUNTIME_CONFIG['ft_time_step'] = float(val)
                except: pass
            elif idx == 4:
                val = input_text(stdscr, "Supercell Dim", "Enter '2 2 2' (empty for Auto):", RUNTIME_CONFIG['ft_dim'])
                RUNTIME_CONFIG['ft_dim'] = val if val else None
            elif idx == 5:
                val = input_text(stdscr, "MEM Coeffs", "Enter N:", RUNTIME_CONFIG['ft_mem'])
                try: RUNTIME_CONFIG['ft_mem'] = int(val)
                except: pass
            elif idx == 6:
                val = input_text(stdscr, "Resolution", "Enter THz:", RUNTIME_CONFIG['ft_resolution'])
                try: RUNTIME_CONFIG['ft_resolution'] = float(val)
                except: pass
            elif idx == 7: break
        elif key == ord('q') or key == 27: break

def phonopy_settings_menu(stdscr, current_path="."):
    idx = 0
    options = ["Supercell Dim", "Reciprocal Mesh", "Temperature", "Max Temp", "Tolerance", "Min Length", "TC Method (RTA/LBTE)", "Back"]
    while True:
        stdscr.clear()
        draw_header(stdscr, "Phonopy Settings")
        try: stdscr.addstr(4, 4, f"Current: Dim={RUNTIME_CONFIG['phonopy_dim']}, Mesh={RUNTIME_CONFIG['phonopy_mesh']}, TC={RUNTIME_CONFIG['phonopy_tc_method'].upper()}", curses.A_BOLD)
        except: pass
        for i, opt in enumerate(options):
            style = curses.A_REVERSE if i == idx else curses.A_NORMAL
            prefix = " > " if i == idx else "   "
            try: stdscr.addstr(6 + i, 4, f"{prefix}{opt}", style)
            except: pass
        stdscr.refresh()
        key = stdscr.getch()
        if key == curses.KEY_UP: idx = max(0, idx - 1)
        elif key == curses.KEY_DOWN: idx = min(len(options) - 1, idx + 1)
        elif key == 10 or key == 13:
            if idx == 0: RUNTIME_CONFIG['phonopy_dim'] = input_text(stdscr, "Dim", "Enter '2 2 2':", RUNTIME_CONFIG['phonopy_dim'])
            elif idx == 1: RUNTIME_CONFIG['phonopy_mesh'] = input_text(stdscr, "Mesh", "Enter '20 20 20':", RUNTIME_CONFIG['phonopy_mesh'])
            elif idx == 2:
                val = input_text(stdscr, "Temp", "Enter K:", RUNTIME_CONFIG['phonopy_temp'])
                try: RUNTIME_CONFIG['phonopy_temp'] = float(val)
                except: pass
            elif idx == 3:
                val = input_text(stdscr, "Max Temp", "Enter K:", RUNTIME_CONFIG['phonopy_tmax'])
                try: RUNTIME_CONFIG['phonopy_tmax'] = float(val)
                except: pass
            elif idx == 4:
                val = input_text(stdscr, "Tolerance", "Enter:", RUNTIME_CONFIG['phonopy_tolerance'])
                try: RUNTIME_CONFIG['phonopy_tolerance'] = float(val)
                except: pass
            elif idx == 5:
                val = input_text(stdscr, "Min Length", "Enter A:", RUNTIME_CONFIG['phonopy_min_length'])
                try: RUNTIME_CONFIG['phonopy_min_length'] = float(val)
                except: pass
            elif idx == 6:
                sel = select_option(stdscr, "Select TC Method", ["br (RTA - Fast)", "lbte (Full - Accurate)"], "br" if RUNTIME_CONFIG['phonopy_tc_method'] == "br" else "lbte")
                if sel: RUNTIME_CONFIG['phonopy_tc_method'] = sel.split()[0]
            elif idx == 7: break
        elif key == ord('q') or key == 27: break

def gruneisen_settings_menu(stdscr):
    idx = 0
    options = ["G-min", "G-max", "F-min (THz)", "F-max (THz)", "Outlier Filter Factor", "Back"]
    while True:
        stdscr.clear()
        draw_header(stdscr, "Gruneisen Plot Settings")
        try:
            gmin = RUNTIME_CONFIG.get('gru_gmin')
            gmax = RUNTIME_CONFIG.get('gru_gmax')
            fmin = RUNTIME_CONFIG.get('gru_fmin')
            fmax = RUNTIME_CONFIG.get('gru_fmax')
            stdscr.addstr(4, 4, f"Current: G[{gmin}:{gmax}], F[{fmin}:{fmax}], Filter={RUNTIME_CONFIG['gru_filter']}", curses.A_BOLD)
        except: pass
        for i, opt in enumerate(options):
            style = curses.A_REVERSE if i == idx else curses.A_NORMAL
            prefix = " > " if i == idx else "   "
            try: stdscr.addstr(6 + i, 4, f"{prefix}{opt}", style)
            except: pass
        stdscr.refresh()
        key = stdscr.getch()
        if key == curses.KEY_UP: idx = max(0, idx - 1)
        elif key == curses.KEY_DOWN: idx = min(len(options) - 1, idx + 1)
        elif key == 10 or key == 13:
            if idx == 0:
                val = input_text(stdscr, "G-min", "Enter min value (empty for auto):", RUNTIME_CONFIG['gru_gmin'])
                try: RUNTIME_CONFIG['gru_gmin'] = float(val) if val else None
                except: pass
            elif idx == 1:
                val = input_text(stdscr, "G-max", "Enter max value (empty for auto):", RUNTIME_CONFIG['gru_gmax'])
                try: RUNTIME_CONFIG['gru_gmax'] = float(val) if val else None
                except: pass
            elif idx == 2:
                val = input_text(stdscr, "F-min", "Enter THz (empty for auto):", RUNTIME_CONFIG['gru_fmin'])
                try: RUNTIME_CONFIG['gru_fmin'] = float(val) if val else None
                except: pass
            elif idx == 3:
                val = input_text(stdscr, "F-max", "Enter THz (empty for auto):", RUNTIME_CONFIG['gru_fmax'])
                try: RUNTIME_CONFIG['gru_fmax'] = float(val) if val else None
                except: pass
            elif idx == 4:
                val = input_text(stdscr, "Filter", "Enter IQR factor (default 3.0):", RUNTIME_CONFIG['gru_filter'])
                try: RUNTIME_CONFIG['gru_filter'] = float(val)
                except: pass
            elif idx == 5: break
        elif key == ord('q') or key == 27: break

def configure_models_menu(stdscr):
    ffs = sorted(list(RUNTIME_CONFIG['models'].keys()))
    idx = 0
    while True:
        stdscr.clear()
        draw_header(stdscr, "Select Force Field to Configure Model")
        for i, ff_name in enumerate(ffs):
            current_model = RUNTIME_CONFIG['models'].get(ff_name, "None")
            style = curses.A_REVERSE if i == idx else curses.A_NORMAL
            prefix = " > " if i == idx else "   "
            try:
                stdscr.addstr(4 + i, 4, f"{prefix}{ff_name}: {current_model}", style)
            except curses.error: pass
        stdscr.refresh()
        key = stdscr.getch()
        if key == curses.KEY_UP: idx = max(0, idx - 1)
        elif key == curses.KEY_DOWN: idx = min(len(ffs) - 1, idx + 1)
        elif key == ord('q') or key == 27: break
        elif key == 10 or key == 13:
            selected_ff = ffs[idx]
            
            # --- New Logic: Show candidates from AVAILABLE_MODELS first ---
            candidates = AVAILABLE_MODELS.get(selected_ff, [])
            installed_files = get_installed_models()
            
            options = []
            for c in candidates:
                # Determine target filename
                source_info = MODEL_SOURCES.get(c)
                target_name = source_info["target"] if source_info else (f"{c}.pth" if selected_ff == "sevennet" else c)
                
                # Check if installed
                # installed_files is a list of filenames
                if target_name in installed_files:
                    status = "[INSTALLED]"
                else:
                    status = "[DOWNLOADABLE]"
                
                # Format: "keyword   [STATUS]"
                options.append(f"{c:<30} {status}")

            options.append("[ Browse Local File ]")
            options.append("[ Cancel ]")
            
            sel = select_option(stdscr, f"Select {selected_ff.upper()} Model Candidate", options, None)
            
            if not sel or sel == "[ Cancel ]":
                continue
                
            if sel == "[ Browse Local File ]":
                search_dir = RUNTIME_CONFIG.get('mlff_directory') or _model_root
                if not search_dir or not os.path.exists(search_dir):
                    search_dir = _model_root
                    
                sel_file = file_browser(stdscr, search_dir, title=f"Select {selected_ff.upper()} Model File")
                if sel_file and not os.path.isdir(sel_file):
                    RUNTIME_CONFIG['models'][selected_ff] = os.path.basename(sel_file)
            else:
                # User selected an API keyword from the list
                # e.g. "7net-omni                      [DOWNLOADABLE]"
                # We need to extract the keyword (first part)
                keyword = sel.split()[0] 
                
                # Resolve keyword to actual filename if possible
                source_info = MODEL_SOURCES.get(keyword)
                if source_info:
                    RUNTIME_CONFIG['models'][selected_ff] = source_info["target"]
                else:
                    RUNTIME_CONFIG['models'][selected_ff] = keyword
def utilities_menu(stdscr):
    curses.curs_set(0)
    idx = 0
    options = [
        "--- MD Analysis ---",
        "  Convert Traj to XDATCAR",
        "  MD Statistics Summary",
        "  Ionic Conductivity",
        "--- Model Tools ---",
        "  Convert Model (FP64 -> FP32)",
        "  List Available Models",
        "--- Structure Tools ---",
        "  Convert VASP4 -> VASP5",
        "--- Visualization ---",
        "  Plot MD Log (T, E, P)",
        "  Plot RDF",
        "  Plot Gruneisen (Band/Mode)",
        "Back to Main Menu"
    ]
    action_map = {1: "util_traj2xdatcar", 2: "util_md_summary", 3: "util_conductivity", 5: "util_convert_model", 6: "util_list_models", 8: "util_vasp4to5", 10: "util_plot_md", 11: "util_plot_rdf", 12: "util_plot_gruneisen", 13: "back"}
    
    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        draw_header(stdscr, "Utilities")
        for i, opt in enumerate(options):
            if i in [0, 4, 7, 9]:
                try: stdscr.addstr(4 + i, 4, opt, curses.A_BOLD)
                except curses.error: pass
                continue
            style = curses.A_REVERSE if i == idx else curses.A_NORMAL
            prefix = " > " if i == idx else "   "
            try: stdscr.addstr(4 + i, 4, f"{prefix}{opt.strip()}", style)
            except curses.error: pass

        try:
            footer = " [Enter] Select  [m] Menu  [e] Edit Setting  [s] Global Settings  [q] Back "
            stdscr.addstr(height-1, 0, footer.ljust(width - 1), curses.A_REVERSE)
        except curses.error: pass

        stdscr.refresh()
        key = stdscr.getch()
        if key == curses.KEY_UP:
            idx = max(0, idx - 1)
            if idx in [0, 4, 7, 9]: idx -= 1
        elif key == curses.KEY_DOWN:
            idx = min(len(options) - 1, idx + 1)
            if idx in [0, 4, 7, 9]: idx += 1
        elif key == ord('m'): return "__MAIN_MENU__"
        elif key == ord('e'): return "__CONFIG_EDITOR__"
        elif key == ord('s'): return "__SETTINGS__"
        elif key in [ord('q'), 27]: return None
        elif key == 10 or key == 13:
            action = action_map.get(idx)
            if action == "back": return None
            if action: return action

def phonopy_menu(stdscr, current_path="."):
    curses.curs_set(0)
    idx = 0
    options = ["Calculate Phonon Band (pb)", "Calculate Quasiharmonic Approx (qha)", "Calculate Stochastic SCHA (sscha)", "Calculate Finite-Temp Phonon (ft)", "Calculate Symmetry Refine (sr)", "Calculate Thermal Conductivity (tc)", "Back"]
    while True:
        stdscr.clear()
        draw_header(stdscr, "Phonopy & Phono3py Features")
        for i, opt in enumerate(options):
            style = curses.A_REVERSE if i == idx else curses.A_NORMAL
            prefix = " > " if i == idx else "   "
            try: stdscr.addstr(4 + i, 4, f"{prefix}{opt}", style)
            except curses.error: pass
        stdscr.refresh()
        key = stdscr.getch()
        if key == curses.KEY_UP: idx = max(0, idx - 1)
        elif key == curses.KEY_DOWN: idx = min(len(options) - 1, idx + 1)
        elif key == 10 or key == 13:
            if idx == 0: return "pb"
            elif idx == 1: return "qha"
            elif idx == 2: return "sscha"
            elif idx == 3: return "ft"
            elif idx == 4: return "sr"
            elif idx == 5: return "tc"
            elif idx == 6: return None
        elif key == ord('q') or key == 27: return None

def run_phonopy_logic(tool_name, current_path):
    print(f"\n--- Preparing Phonopy Tool: {tool_name.upper()} ---")
    
    settings_func = phonopy_settings_menu
    if tool_name == "ft":
        settings_func = ft_settings_menu
        
    poscar_path = curses.wrapper(lambda stdscr: file_browser(stdscr, current_path, title=f"Phonopy: {tool_name.upper()}", instruction="Select input structure", settings_func=settings_func))
    if not poscar_path: return None
    if poscar_path in ["__MAIN_MENU__", "__UTILITIES__", "__CONFIG_EDITOR__"]: return poscar_path

    ff = RUNTIME_CONFIG['ff']
    device = RUNTIME_CONFIG['device']
    
    # Common dims
    p_dim = [int(x) for x in RUNTIME_CONFIG['phonopy_dim'].split()] if RUNTIME_CONFIG['phonopy_dim'] else None
    p_mesh = [int(x) for x in RUNTIME_CONFIG['phonopy_mesh'].split()]
    
    # FT specific dims
    ft_dim = [int(x) for x in RUNTIME_CONFIG['ft_dim'].split()] if RUNTIME_CONFIG.get('ft_dim') else None
    
    model_path = None
    configured_model_name = RUNTIME_CONFIG['models'].get(ff)
    if configured_model_name:
        if ff in {"fairchem", "orb", "chgnet", "m3gnet"}: model_path = configured_model_name
        else:
            model_path = resolve_model_path(configured_model_name)

    tool_names_full = {
        "pb": "pb (phonon band)",
        "qha": "qha (quasi-harmonic approx)",
        "sscha": "sscha (stochastic self-consistent harmonic approx)",
        "ft": "ft (finite-temperature phonon)",
        "sr": "sr (symmetry refine / relax unit)",
        "tc": "tc (thermal conductivity)"
    }
    full_name = tool_names_full.get(tool_name, tool_name.upper())

    print(f"\n--- Execution Summary ---")
    print(f"  Tool         : Phonopy {full_name}")
    print(f"  Input POSCAR : {os.path.basename(poscar_path)}")
    print(f"  Force Field  : {ff}")
    print(f"  Device       : {device}")
    print(f"  Execution Dir: {RUNTIME_CONFIG.get('global_execution_dir') or '(Auto: Input Dir)'}")
    print(f"  Output Dir   : {RUNTIME_CONFIG.get('global_output_dir') or '(Auto: Module Prefix)'}")
    
    if tool_name == "ft":
        print(f"  Dimension    : {RUNTIME_CONFIG.get('ft_dim') or '(Auto)'}")
        print(f"  Temperature  : {RUNTIME_CONFIG['ft_temp']} K")
        print(f"  MD Steps     : {RUNTIME_CONFIG['ft_md_steps']} (eq {RUNTIME_CONFIG['ft_md_equil']})")
    else:
        print(f"  Dimension    : {RUNTIME_CONFIG.get('phonopy_dim') or '(Auto)'}")
        print(f"  Mesh         : {RUNTIME_CONFIG['phonopy_mesh']}")
        if tool_name != "pb":
            print(f"  Temperature  : {RUNTIME_CONFIG['phonopy_temp']} K")
            
    print("-" * 35)

    confirm = input(f"Proceed with run? [y/n]: ").strip().lower()
    if confirm == 'n': return

    input_dir = RUNTIME_CONFIG.get('global_execution_dir') or os.path.dirname(poscar_path)
    output_dir_config = RUNTIME_CONFIG.get('global_output_dir')
    
    if output_dir_config:
        base_output_dir = os.path.join(input_dir, output_dir_config) if not os.path.isabs(output_dir_config) else output_dir_config
    else:
        if tool_name == "pb":
            base_output_dir = os.path.join(input_dir, f"phonon_band-{os.path.basename(poscar_path)}-mlff={ff}")
        elif tool_name == "tc":
            base_output_dir = os.path.join(input_dir, f"tc_{os.path.basename(poscar_path)}_mlff={ff}")
        elif tool_name == "ft":
            base_output_dir = os.path.join(input_dir, f"finite-phonon-{os.path.basename(poscar_path)}")
        else:
            base_output_dir = os.path.join(input_dir, f"{tool_name}_{os.path.basename(poscar_path)}-mlff={ff}")
        
    output_dir = base_output_dir
    i = 1
    while os.path.exists(output_dir):
        output_dir = f"{base_output_dir}-NEW{i:02d}"
        i += 1

    from types import SimpleNamespace
    args = SimpleNamespace(
        poscar=poscar_path, cif=None, input_files=[poscar_path], cif_files=[], ff=ff, model=model_path, modal=None, device=device, dim=p_dim, mesh=p_mesh, mass=None, output_dir=output_dir, output_dir_arg=output_dir,
        length=RUNTIME_CONFIG['phonopy_min_length'], amplitude=0.01, is_plusminus=False, is_diagonal=True, symprec=1e-5, yaml=None, out=None, gamma=None, no_defaults=False, atom_names=None, rename=None, tolerance_sr=RUNTIME_CONFIG['phonopy_tolerance'], tolerance_phonopy=1e-5, optimizer="FIRE", fix_axis=None, plot_gruneisen=False, strain=0.01, gmin=None, gmax=None, target_energy=0.001, filter_outliers=1.5, use_relax_unit=False, initial_fmax=0.01, initial_symprec=1e-5, initial_isif=3, irreps=False, qpoint=[0,0,0], tolerance_irreps=1e-5, write_arrow=False, arrow_length=1.0, arrow_min_cutoff=0.0, arrow_qpoint_gamma=False, arrow_qpoint=None, dos=False,
        tmax=RUNTIME_CONFIG['phonopy_tmax'], eos='vinet', num_volumes=11, length_scale=0.05, length_factor_min=None, length_factor_max=None, min_length=RUNTIME_CONFIG['phonopy_min_length'], tolerance_phonopy_qha=1e-5, relax_atom=True, use_force_constants=False, poly_degree=2, poly_points=5, smooth_deg=2, initial_use_symmetry=True, isif=3,
        temperature=RUNTIME_CONFIG['phonopy_temp'], reference_n_samples=2000, reference_method='random', reference_md_nsteps=5000, reference_md_nequil=1000, reference_md_tstep=2.0, md_thermostat='nose-hoover', md_friction=0.002, write_xdatcar=False, xdatcar_step=10, max_iter=20, max_regen=3, ess_collapse_ratio=0.5, save_every=1, fc_mixing_alpha=0.5, free_energy_conv=0.001, read_initial_fc=None, pm=False, nodiag=False, include_third_order=False, optimize_volume=False, max_volume_iter=10, no_save_reference_ensemble=False, seed=None, plot_bands=True, gamma_label=None, reference_ensemble=None,
        output_prefix=None, max_iterations=10, tolerance=RUNTIME_CONFIG['phonopy_tolerance'],
        # TC specific args
        length_fc2=25.0, dim_fc2=None, temp=[RUNTIME_CONFIG['phonopy_temp']], tmin=0, tstep=10, boundary_mfp=None, plot=True, save_hdf5=True,
        method=RUNTIME_CONFIG['phonopy_tc_method'],
        # FT (DynaPhoPy) specific args
        md_steps=RUNTIME_CONFIG['ft_md_steps'], md_equil=RUNTIME_CONFIG['ft_md_equil'], time_step=RUNTIME_CONFIG['ft_time_step'],
        mem=RUNTIME_CONFIG['ft_mem'], resolution=RUNTIME_CONFIG['ft_resolution'], projection_qpoint=None, save_quasiparticles=True,
        thermal_properties=True, power_spectrum=True, no_supercell=False, thermostat='nose-hoover', read_fc=None
    )
    
    # Overwrite dim and temp for FT
    if tool_name == "ft":
        args.dim = ft_dim
        args.temp = [RUNTIME_CONFIG['ft_temp']] # List expected

    try:
        if tool_name == "pb": run_phonon_band_cli(args)
        elif tool_name == "qha": run_qha_workflow(args)
        elif tool_name == "sscha": run_sscha_workflow(args)
        elif tool_name == "ft": run_dynaphopy_workflow(args)
        elif tool_name == "sr": run_relax_unit(args)
        elif tool_name == "tc": run_tc_workflow(args)
        print("\n--- Workflow Completed Successfully ---")
        input("\nPress Enter to return to main menu...")
        return output_dir
    except Exception as e:
        print(f"\nError: {e}")
        traceback.print_exc()
        input("\nPress Enter...")
        return None

def pydefect_menu(stdscr):
    curses.curs_set(0)
    idx = 0
    options = ["Run Full Workflow (cpd+defect)", "Run CPD Workflow", "Run Defect Workflow", "Back"]
    while True:
        stdscr.clear()
        draw_header(stdscr, "Pydefect Features")
        for i, opt in enumerate(options):
            style = curses.A_REVERSE if i == idx else curses.A_NORMAL
            prefix = " > " if i == idx else "   "
            try: stdscr.addstr(4 + i, 4, f"{prefix}{opt}", style)
            except curses.error: pass
        stdscr.refresh()
        key = stdscr.getch()
        if key == curses.KEY_UP: idx = max(0, idx - 1)
        elif key == curses.KEY_DOWN: idx = min(len(options) - 1, idx + 1)
        elif key == 10 or key == 13:
            if idx == 0: return "full"
            elif idx == 1: return "cpd"
            elif idx == 2: return "defect"
            elif idx == 3: return None
        elif key == ord('q') or key == 27: return None

def run_pydefect_logic(tool_name, current_path):

    print(f"\n--- Preparing Pydefect Tool: {tool_name.upper()} ---")

    poscar_path = None

    if tool_name in ["full", "cpd"]:
        if not RUNTIME_CONFIG['pydefect_formula'] and not RUNTIME_CONFIG['pydefect_mpid']:
            poscar_path = curses.wrapper(lambda stdscr: file_browser(stdscr, current_path, title=f"Pydefect: {tool_name.upper()}", instruction="Select input POSCAR or press 'q' to enter MP settings", settings_func=pydefect_settings_menu))
            if not poscar_path:
                print("\nNo POSCAR selected. You can provide Formula or MP ID:")
                choice = input("Enter 'f' for Formula, 'm' for MP ID, or 'q' to cancel: ").strip().lower()
                if choice == 'f':
                    val = input("Enter Formula (e.g. MgO): ").strip()
                    if val: RUNTIME_CONFIG['pydefect_formula'] = val
                elif choice == 'm':
                    val = input("Enter MP ID (e.g. mp-1265): ").strip()
                    if val: RUNTIME_CONFIG['pydefect_mpid'] = val
                else:
                    return None
            if poscar_path in ["__MAIN_MENU__", "__UTILITIES__", "__CONFIG_EDITOR__"]: return poscar_path
    else: # defect tool requires POSCAR
        poscar_path = curses.wrapper(lambda stdscr: file_browser(stdscr, current_path, title=f"Pydefect: {tool_name.upper()}", instruction="Select input POSCAR (unitcell)", settings_func=pydefect_settings_menu))
        if not poscar_path: return None
        if poscar_path in ["__MAIN_MENU__", "__UTILITIES__", "__CONFIG_EDITOR__"]: return poscar_path

    # For defect tool, we also need std_energies and target_vertices if run standalone
    std_energies = None
    target_vertices = None
    if tool_name == "defect":
        std_energies = curses.wrapper(lambda stdscr: file_browser(stdscr, current_path, instruction="Select standard_energies.yaml"))
        if not std_energies: return
        target_vertices = curses.wrapper(lambda stdscr: file_browser(stdscr, current_path, instruction="Select target_vertices.yaml"))
        if not target_vertices: return
    ff = RUNTIME_CONFIG['ff']
    device = RUNTIME_CONFIG['device']
    model_path = None
    if conf_m:
        if ff in {"fairchem", "orb", "chgnet", "m3gnet"}: model_path = conf_m
        else:
            model_path = resolve_model_path(conf_m)

        from types import SimpleNamespace

        doping_list = [x.strip() for x in RUNTIME_CONFIG['pydefect_doping'].split(',') if x.strip()]

        # Determine base workspace
        base_dir = RUNTIME_CONFIG.get('global_execution_dir') or current_path
        output_dir_config = RUNTIME_CONFIG.get('global_output_dir')
        
        if output_dir_config:
            output_dir = os.path.join(base_dir, output_dir_config) if not os.path.isabs(output_dir_config) else output_dir_config
        else:
            # Generate default subfolder name
            if poscar_path:
                prefix = os.path.basename(poscar_path)
            elif RUNTIME_CONFIG['pydefect_formula']:
                prefix = RUNTIME_CONFIG['pydefect_formula']
            elif RUNTIME_CONFIG['pydefect_mpid']:
                prefix = RUNTIME_CONFIG['pydefect_mpid']
            else:
                prefix = "workspace"
            output_dir = os.path.join(base_dir, f"PYDEFECT-{prefix}-mlff={ff}")
        
        # Increment if exists
        base_output_dir = output_dir
        if os.path.exists(output_dir):
            i = 1
            while os.path.exists(output_dir):
                output_dir = f"{base_output_dir}-NEW{i:02d}"
                i += 1

        pd_tool_names = {
            "full": "full (cpd + defect workflow)",
            "cpd": "cpd (chemical potential diagram)",
            "defect": "defect (point defect simulation)"
        }
        pd_full_name = pd_tool_names.get(tool_name, tool_name.upper())

        print(f"\n--- Execution Summary ---")
        print(f"  Tool         : Pydefect {pd_full_name}")
        if poscar_path:
            print(f"  Input POSCAR : {os.path.basename(poscar_path)}")
        else:
            print(f"  Formula      : {RUNTIME_CONFIG['pydefect_formula']}")
            print(f"  MP ID        : {RUNTIME_CONFIG['pydefect_mpid']}")
        print(f"  Force Field  : {ff}")
        print(f"  Device       : {device}")
        print(f"  Execution Dir: {RUNTIME_CONFIG.get('global_execution_dir') or '(Auto: Input Dir)'}")
        print(f"  Output Dir   : {RUNTIME_CONFIG.get('global_output_dir') or '(Auto: Module Prefix)'}")
        print(f"  Fmax         : {RUNTIME_CONFIG['pydefect_fmax']}")
        print("-" * 35)

        args = SimpleNamespace(
            poscar=poscar_path,
            formula=RUNTIME_CONFIG['pydefect_formula'],
            mpid=RUNTIME_CONFIG['pydefect_mpid'],
            doping=doping_list,
            ff=ff,
            model=model_path,
            device=device,
            modal=None,
            fmax=RUNTIME_CONFIG['pydefect_fmax'],
            fmax_cpd=None,
            fmax_defect=None,
            energy_shift_target=RUNTIME_CONFIG['pydefect_energy_shift_target'],
            matrix=RUNTIME_CONFIG['pydefect_matrix'],
            min_atoms=RUNTIME_CONFIG['pydefect_min_atoms'],
            max_atoms=RUNTIME_CONFIG['pydefect_max_atoms'],
            analyze_symmetry=RUNTIME_CONFIG['pydefect_analyze_symmetry'],
            sites_yaml_filename=None,
            std_energies=std_energies,
            target_vertices=target_vertices,
            output_dir=output_dir
        )

    confirm = input(f"Proceed with run? [y/n]: ").strip().lower()

    if confirm == 'n': return
    try:
        if tool_name == "full": run_full_workflow(args)
        elif tool_name == "cpd": run_cpd_workflow(args)
        elif tool_name == "defect": run_defect_workflow(args)
        print("\n--- Workflow Completed Successfully ---")
        input("\nPress Enter to return to main menu...")
    except Exception as e:
        print(f"\nError: {e}")
        traceback.print_exc()
        input("\nPress Enter to continue...")

def run_utility_logic(tool_name, current_path):
    print(f"\n--- Running Utility: {tool_name} ---")
    try:
        if tool_name == "util_traj2xdatcar":
            fname = curses.wrapper(lambda stdscr: file_browser(stdscr, current_path, instruction="Select .traj file"))
            if fname: traj2xdatcar(fname, input("Output [XDATCAR]: ") or "XDATCAR", int(input("Interval [1]: ") or "1"))
        elif tool_name == "util_md_summary":
            fname = curses.wrapper(lambda stdscr: file_browser(stdscr, current_path, instruction="Select md.csv"))
            if fname: md_summary(fname)
        elif tool_name == "util_conductivity":
            fname = curses.wrapper(lambda stdscr: file_browser(stdscr, current_path, instruction=".traj or XDATCAR"))
            if fname: calculate_conductivity(fname, float(input("Temp (K): ")), float(input("dt (fs): ")), int(input("Interval [1]: ") or "1"), input("Charges (e.g. Li:1): "))
        elif tool_name == "util_convert_model":
            fname = curses.wrapper(lambda stdscr: file_browser(stdscr, current_path, instruction="Select model file"))
            if fname: convert_model_precision(fname)
        elif tool_name == "util_list_models": list_models()
        elif tool_name == "util_vasp4to5":
            fname = curses.wrapper(lambda stdscr: file_browser(stdscr, current_path, instruction="Select VASP4 POSCAR"))
            if fname: vasp4to5(fname, input("Elements (e.g. 'Al O'): "))
        elif tool_name == "util_plot_md":
            fname = curses.wrapper(lambda stdscr: file_browser(stdscr, current_path, instruction="Select md.csv"))
            if fname: plot_md_log(fname, input("Prefix [md_plot]: ") or "md_plot")
        elif tool_name == "util_plot_rdf":
            fname = curses.wrapper(lambda stdscr: file_browser(stdscr, current_path, instruction="Select trajectory"))
            if fname: plot_rdf(fname, input("Prefix [rdf_plot]: ") or "rdf_plot", float(input("Rmax [10]: ") or "10"), int(input("Bins [200]: ") or "200"))
        elif tool_name == "util_plot_gruneisen":
            dat_file = curses.wrapper(lambda stdscr: file_browser(stdscr, current_path, title="Select Gruneisen .dat", instruction=".dat file", settings_func=gruneisen_settings_menu))
            if dat_file:
                yaml_file = curses.wrapper(lambda stdscr: file_browser(stdscr, os.path.dirname(dat_file), title="Select labels .yaml (Optional)", instruction="Select .yaml or ESC to skip"))
                
                print(f"\n--- Plot Summary ---")
                print(f"  Data File  : {os.path.basename(dat_file)}")
                print(f"  Labels File: {os.path.basename(yaml_file) if yaml_file else '(Auto/None)'}")
                print(f"  G-Range    : [{RUNTIME_CONFIG['gru_gmin']}:{RUNTIME_CONFIG['gru_gmax']}]")
                print(f"  F-Range    : [{RUNTIME_CONFIG['gru_fmin']}:{RUNTIME_CONFIG['gru_fmax']}]")
                
                confirm = input("\nProceed with plotting? [y/n]: ").strip().lower()
                if confirm != 'y': return

                prefix = input("Output prefix [gruneisen]: ") or "gruneisen"
                plot_gruneisen_band(
                    dat_file, 
                    out_prefix=prefix,
                    fmin=RUNTIME_CONFIG['gru_fmin'],
                    fmax=RUNTIME_CONFIG['gru_fmax'],
                    gmin=RUNTIME_CONFIG['gru_gmin'],
                    gmax=RUNTIME_CONFIG['gru_gmax'],
                    filter_outliers=RUNTIME_CONFIG['gru_filter'],
                    yaml_path=yaml_file
                )
                print("\nPlotting completed successfully.")
    except Exception as e:
        print(f"\nError: {e}")
        traceback.print_exc()
    input("\nPress Enter to continue...")

# --- Main Logic ---

def main_menu(stdscr):
    curses.curs_set(0)
    stdscr.keypad(True)
    options = [
        "Relax Structure", 
        "Run MD Simulation", 
        "Gibbs Free Energy Integration",
        "Phonopy & Phono3py Features", 
        "Pydefect Features", 
        "[ Utilities ]", 
        "[ Settings ]", 
        "[ Default setting editor (~/.macer.yaml) ]",
        "[ Exit ]"
    ]
    idx = 0
    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        draw_header(stdscr, "Main Menu")
        
        try:
            g_exe = RUNTIME_CONFIG.get('global_execution_dir') or "(Auto: Input Dir)"
            g_out = RUNTIME_CONFIG.get('global_output_dir') or "(Auto: Module Prefix)"
            stdscr.addstr(4, 4, f"Device: {RUNTIME_CONFIG['device']} | FF: {RUNTIME_CONFIG['ff']}", curses.A_BOLD)
            stdscr.addstr(5, 4, f"Global Exe: {g_exe}")
            stdscr.addstr(6, 4, f"Global Out: {g_out}")
            stdscr.addstr(7, 4, "-" * 40)
        except curses.error: pass
        
        for i, opt in enumerate(options):
            style = curses.A_REVERSE if i == idx else curses.A_NORMAL
            if i >= 5: # Apply bold to Utilities, Settings, Editor, and Exit
                style |= curses.A_BOLD
            prefix = "> " if i == idx else "  "
            try: stdscr.addstr(9 + i, 4, f"{prefix}{opt}", style)
            except curses.error: pass

        try:
            footer = " [Enter] Select  [u] Utils  [e] Edit Setting  [s] Global Settings  [q] Exit "
            stdscr.addstr(height-1, 0, footer.ljust(width - 1), curses.A_REVERSE)
        except curses.error: pass

        stdscr.refresh()
        key = stdscr.getch()
        if key == curses.KEY_UP: idx = max(0, idx - 1)
        elif key == curses.KEY_DOWN: idx = min(len(options) - 1, idx + 1)
        elif key == ord('u'): return "utils"
        elif key == ord('e'): return "config_editor"
        elif key == ord('s'): return "settings"
        elif key in [ord('q'), 27]: return "exit"
        elif key == 10 or key == 13:
            if idx == 0: return "relax"
            elif idx == 1: return "md"
            elif idx == 2: return "gibbs"
            elif idx == 3: return "phonopy"
            elif idx == 4: return "pydefect"
            elif idx == 5: return "utils"
            elif idx == 6: return "settings"
            elif idx == 7: return "config_editor"
            elif idx == 8: return "exit"

def run_relax_logic(poscar_path):
    print(f"\n--- Preparing Relaxation for: {poscar_path} ---")
    is_cif = str(poscar_path).lower().endswith('.cif')
    try:
        if not is_cif: check_poscar_format(Path(poscar_path))
        else: from ase.io import read; relax_input = read(poscar_path)
    except Exception as e:
        print(f"Error: {e}"); input("Press Enter..."); return
    
    ff = RUNTIME_CONFIG['ff']
    device = RUNTIME_CONFIG['device']
    fmax = RUNTIME_CONFIG.get('fmax', 0.01)
    isif = RUNTIME_CONFIG.get('isif', 3)
    max_steps = RUNTIME_CONFIG.get('max_steps')
    optimizer = RUNTIME_CONFIG.get('optimizer', "FIRE")

    if ff not in get_available_ffs():
        print(f"\n[ERROR] '{ff}' not installed."); input("Press Enter..."); return
    model_path = None
    conf_m = RUNTIME_CONFIG['models'].get(ff)
    if conf_m:
        if ff in {"fairchem", "orb", "chgnet", "m3gnet"}: model_path = conf_m
        else:
            model_path = resolve_model_path(conf_m)

    print(f"\n--- Execution Summary ---")
    print(f"  Tool         : Relaxation (structure optimization)")
    print(f"  Input        : {os.path.basename(poscar_path)}")
    print(f"  Force Field  : {ff}")
    print(f"  Device       : {device}")
    print(f"  Execution Dir: {RUNTIME_CONFIG.get('global_execution_dir') or '(Auto: Input Dir)'}")
    print(f"  Output Dir   : {RUNTIME_CONFIG.get('global_output_dir') or '(Auto: Module Prefix)'}")
    print(f"  ISIF Mode    : {isif}")
    print(f"  Fmax         : {fmax} eV/A")
    print(f"  Optimizer    : {optimizer}")
    print("-" * 35)

    confirm = input("Proceed? [y/n]: ").strip().lower()
    if confirm == 'n': return
    try:
        # Output directory setup
        input_dir = RUNTIME_CONFIG.get('global_execution_dir') or os.path.dirname(poscar_path)
        output_dir_config = RUNTIME_CONFIG.get('global_output_dir')
        
        if output_dir_config:
            base_output_dir = os.path.join(input_dir, output_dir_config) if not os.path.isabs(output_dir_config) else output_dir_config
            output_dir = base_output_dir
            if os.path.exists(output_dir):
                i = 1
                while os.path.exists(output_dir):
                    output_dir = f"{base_output_dir}-NEW{i:02d}"
                    i += 1
        else:
            prefix = os.path.basename(poscar_path)
            base_dir_name = f"RELAX-INTERACTIVE-{prefix}-mlff={ff}"
            output_dir = os.path.join(input_dir, base_dir_name)
            
            i = 1
            while os.path.exists(output_dir):
                output_dir = os.path.join(input_dir, f"{base_dir_name}-NEW{i:02d}")
                i += 1
                
        os.makedirs(output_dir, exist_ok=True)
        print(f"Created output directory: {output_dir}")
        
        log_name = os.path.join(output_dir, "relax.log")
        print(f"Logging to: {log_name}")
        
        # Run Relaxation
        original_stdout = sys.stdout
        try:
            with Logger(log_name) as lg:
                sys.stdout = lg
                relax_structure(
                    input_file=poscar_path,
                    fmax=fmax,
                    device=device,
                    isif=isif,
                    output_dir_override=output_dir,
                    ff=ff,
                    model_path=model_path,
                    quiet=False, # Show output
                    make_pdf=True,
                    contcar_name=os.path.join(output_dir, "CONTCAR"),
                    outcar_name=os.path.join(output_dir, "OUTCAR"),
                    xml_name=os.path.join(output_dir, "vasprun.xml"),
                    max_steps=max_steps,
                    optimizer_name=optimizer
                )
        finally:
            sys.stdout = original_stdout
            
        print("\n--- Calculation Completed Successfully ---")
        print(f"Results in: {output_dir}")
        print("Generated files:")
        for f in sorted(os.listdir(output_dir)):
            print(f" - {f}")
            
        input("\nPress Enter to return to main menu...")
        return output_dir

    except ValueError as ve:
        if "Unsupported force field" in str(ve):
            print(f"\n[ERROR] The force field '{ff}' could not be loaded.")
            print(f"        It might not be installed in this environment.")
            print(f"        Try: pip install 'macer[{ff}]'")
        else:
            print(f"\nValueError: {ve}")
            traceback.print_exc()
            
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        traceback.print_exc()
        
    input("\nPress Enter to return to main menu...")
    return None

def run_md_logic(poscar_path):
    print(f"\n--- Preparing MD for: {poscar_path} ---")
    ff = RUNTIME_CONFIG['ff']
    if ff not in get_available_ffs():
        print(f"\n[ERROR] '{ff}' not installed."); input("Press Enter..."); return
    model_path = None
    conf_m = RUNTIME_CONFIG['models'].get(ff)
    if conf_m:
        if ff in {"fairchem", "orb", "chgnet", "m3gnet"}: model_path = conf_m
        else:
            model_path = resolve_model_path(conf_m)

    print(f"\n--- Execution Summary ---")
    print(f"  Tool         : MD Simulation (molecular dynamics)")
    print(f"  Input        : {os.path.basename(poscar_path)}")
    print(f"  Force Field  : {ff}")
    print(f"  Device       : {RUNTIME_CONFIG['device']}")
    print(f"  Execution Dir: {RUNTIME_CONFIG.get('global_execution_dir') or '(Auto: Input Dir)'}")
    print(f"  Output Dir   : {RUNTIME_CONFIG.get('global_output_dir') or '(Auto: Module Prefix)'}")
    print(f"  Ensemble     : {RUNTIME_CONFIG['md_ensemble'].upper()}")
    print(f"  Temperature  : {RUNTIME_CONFIG['md_temp']} K")
    print(f"  Steps        : {RUNTIME_CONFIG['md_nsteps']}")
    print("-" * 35)

    confirm = input("Proceed? [y/n]: ").strip().lower()
    if confirm == 'n': return
    
    input_dir = RUNTIME_CONFIG.get('global_execution_dir') or os.path.dirname(poscar_path)
    md_out_config = RUNTIME_CONFIG.get('global_output_dir')
    
    if md_out_config:
        base_dir = os.path.join(input_dir, md_out_config) if not os.path.isabs(md_out_config) else md_out_config
    else:
        base_dir = os.path.join(input_dir, f"MD-{os.path.basename(poscar_path)}-mlff={ff}")
        
    output_dir, i = base_dir, 1
    while os.path.exists(output_dir): output_dir = f"{base_dir}-NEW{i:02d}"; i += 1
    from types import SimpleNamespace
    args = SimpleNamespace(poscar=poscar_path if not poscar_path.endswith('.cif') else None, cif=poscar_path if poscar_path.endswith('.cif') else None, ff=ff, model=model_path, modal=None, device=RUNTIME_CONFIG['device'], ensemble=RUNTIME_CONFIG['md_ensemble'], temp=RUNTIME_CONFIG['md_temp'], press=RUNTIME_CONFIG['md_press'], tstep=RUNTIME_CONFIG['md_tstep'], nsteps=RUNTIME_CONFIG['md_nsteps'], ttau=100.0, ptau=1000.0, seed=None, mass=None, output_dir=output_dir, save_every=RUNTIME_CONFIG['md_save_every'], xdat_every=1, print_every=1, csv="md.csv", xdatcar="XDATCAR", traj="md.traj", log="md.log", initial_relax=False, initial_relax_optimizer="FIRE", initial_relax_fmax=0.01, initial_relax_smax=0.001, initial_relax_symprec=1e-5, initial_relax_use_symmetry=True)
    try:
        run_md_simulation(args)
        print(f"\nDone. Results in: {output_dir}"); input("\nPress Enter...")
        return output_dir
    except Exception as e:
        print(f"\nError: {e}"); traceback.print_exc(); input("\nPress Enter...")

def run_gibbs_logic(poscar_path):
    print(f"\n--- Preparing Gibbs Integration for: {poscar_path} ---")
    ff = RUNTIME_CONFIG['ff']
    if ff not in get_available_ffs():
        print(f"\n[ERROR] '{ff}' not installed."); input("Press Enter..."); return
    model_path = None
    conf_m = RUNTIME_CONFIG['models'].get(ff)
    if conf_m:
        if ff in {"fairchem", "orb", "chgnet", "m3gnet"}: model_path = conf_m
        else:
            model_path = resolve_model_path(conf_m)

    g_dim = [int(x) for x in RUNTIME_CONFIG['gibbs_dim'].split()] if RUNTIME_CONFIG['gibbs_dim'] else None
    
    print(f"\n--- Execution Summary ---")
    print(f"  Tool         : Gibbs Integration (Temperature Integration)")
    print(f"  Input        : {os.path.basename(poscar_path)}")
    print(f"  Force Field  : {ff}")
    print(f"  Device       : {RUNTIME_CONFIG['device']}")
    print(f"  Ensemble     : {RUNTIME_CONFIG['gibbs_ensemble'].upper()}")
    print(f"  Range        : {RUNTIME_CONFIG['gibbs_temp_start']} - {RUNTIME_CONFIG['gibbs_temp_end']} K (step {RUNTIME_CONFIG['gibbs_temp_step']})")
    print(f"  Steps/T      : {RUNTIME_CONFIG['gibbs_nsteps']} (Equil: {RUNTIME_CONFIG['gibbs_equil_steps']})")
    print(f"  Supercell    : {g_dim}")
    print(f"  QHA Ref      : {os.path.basename(RUNTIME_CONFIG['gibbs_qha_ref']) if RUNTIME_CONFIG['gibbs_qha_ref'] else 'None'}")
    print("-" * 35)

    confirm = input("Proceed? [y/n]: ").strip().lower()
    if confirm == 'n': return
    
    input_dir = RUNTIME_CONFIG.get('global_execution_dir') or os.path.dirname(poscar_path)
    out_config = RUNTIME_CONFIG.get('global_output_dir')
    
    if out_config:
        base_dir = os.path.join(input_dir, out_config) if not os.path.isabs(out_config) else out_config
    else:
        base_dir = os.path.join(input_dir, f"gibbs_{os.path.basename(poscar_path)}_mlff={ff}")
        
    output_dir, i = base_dir, 1
    while os.path.exists(output_dir): output_dir = f"{base_dir}-NEW{i:02d}"; i += 1
    os.makedirs(output_dir, exist_ok=True)
    
    from types import SimpleNamespace
    args = SimpleNamespace(
        poscar=poscar_path, 
        qha_ref=RUNTIME_CONFIG['gibbs_qha_ref'],
        temp_start=RUNTIME_CONFIG['gibbs_temp_start'],
        temp_end=RUNTIME_CONFIG['gibbs_temp_end'],
        temp_step=RUNTIME_CONFIG['gibbs_temp_step'],
        temps=None,
        nsteps=RUNTIME_CONFIG['gibbs_nsteps'],
        equil_steps=RUNTIME_CONFIG['gibbs_equil_steps'],
        tstep=RUNTIME_CONFIG.get('md_tstep', 1.0), # Re-use MD tstep setting or add specific? Using MD default for now. Actually plan-implementation said default 1.0. Let's use 1.0 or user setting if we added it. We didn't add specific tstep to gibbs menu yet, so hardcode 1.0 or use MD setting. Let's use 1.0 as safe default.
        ensemble=RUNTIME_CONFIG['gibbs_ensemble'],
        press=0.0,
        thermostat='langevin',
        ttau=100.0,
        ptau=1000.0,
        friction=1.0,
        dim=g_dim,
        ff=ff,
        model=model_path,
        device=RUNTIME_CONFIG['device'],
        output_dir=output_dir,
        prefix="gibbs"
    )
    
    try:
        run_gibbs_workflow(args)
        print(f"\nDone. Results in: {output_dir}"); input("\nPress Enter...")
        return output_dir
    except Exception as e:
        print(f"\nError: {e}"); traceback.print_exc(); input("\nPress Enter...")

def run_interactive(start_ff=None):
    init_runtime_config(start_ff)
    try: curses.wrapper(show_intro)
    except: pass
    os.system("clear")
    current_path = os.getcwd()
    
    next_action = None
    
    while True:
        if next_action:
            action = next_action
            next_action = None
        else:
            action = curses.wrapper(main_menu)
            
        if action == "exit": break
        elif action == "settings": curses.wrapper(settings_menu, current_path)
        elif action == "relax":
            f = curses.wrapper(lambda s: file_browser(s, current_path, title="Relax", instruction="Select structure", settings_func=relax_settings_menu))
            if not f or f == "__MAIN_MENU__": continue
            if f == "__UTILITIES__": next_action = "utils"; continue
            if f == "__CONFIG_EDITOR__": next_action = "config_editor"; continue
            
            current_path = os.path.dirname(os.path.abspath(f))
            out = run_relax_logic(f)
            if out: 
                current_path = os.path.abspath(out)
                curses.wrapper(lambda s: file_browser(s, out, title="Results", instruction="View output"))
        elif action == "md":
            f = curses.wrapper(lambda s: file_browser(s, current_path, title="MD Simulation", instruction="Select structure", settings_func=md_settings_menu))
            if not f or f == "__MAIN_MENU__": continue
            if f == "__UTILITIES__": next_action = "utils"; continue
            if f == "__CONFIG_EDITOR__": next_action = "config_editor"; continue
            
            current_path = os.path.dirname(os.path.abspath(f))
            out = run_md_logic(f)
            if out:
                current_path = os.path.abspath(out)
                curses.wrapper(lambda s: file_browser(s, out, title="Results", instruction="View output"))
        elif action == "gibbs":
            f = curses.wrapper(lambda s: file_browser(s, current_path, title="Gibbs Integration", instruction="Select structure", settings_func=gibbs_settings_menu))
            if not f or f == "__MAIN_MENU__": continue
            if f == "__UTILITIES__": next_action = "utils"; continue
            if f == "__CONFIG_EDITOR__": next_action = "config_editor"; continue
            
            current_path = os.path.dirname(os.path.abspath(f))
            out = run_gibbs_logic(f)
            if out:
                current_path = os.path.abspath(out)
                curses.wrapper(lambda s: file_browser(s, out, title="Results", instruction="View output"))
        elif action == "phonopy":
            while True:
                tool = curses.wrapper(lambda s: phonopy_menu(s, current_path))
                if tool:
                    out = run_phonopy_logic(tool, current_path)
                    if out == "__MAIN_MENU__": break
                    if out in ["__UTILITIES__", "__CONFIG_EDITOR__"]:
                        next_action = "utils" if out == "__UTILITIES__" else "config_editor"
                        break
                    if out:
                        current_path = os.path.abspath(out)
                        curses.wrapper(lambda s: file_browser(s, out, title=f"Phonopy: {tool.upper()}", instruction="View output"))
                else:
                    break
        elif action == "pydefect":
            tool = curses.wrapper(pydefect_menu)
            if tool:
                res = run_pydefect_logic(tool, current_path)
                if res in ["__UTILITIES__", "__CONFIG_EDITOR__"]:
                    next_action = "utils" if res == "__UTILITIES__" else "config_editor"
        elif action == "utils":
            tool = curses.wrapper(utilities_menu)
            if tool == "__MAIN_MENU__": continue
            if tool == "__CONFIG_EDITOR__": next_action = "config_editor"; continue
            if tool == "__SETTINGS__": next_action = "settings"; continue
            if tool: run_utility_logic(tool, current_path)
        elif action == "config_editor":
            curses.wrapper(user_config_editor)