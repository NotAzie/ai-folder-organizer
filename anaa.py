import os
import shutil
import json
import time
import requests
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import tkinter as tk
from tkinter import filedialog, ttk
from tkinter import simpledialog, messagebox
from tqdm import tqdm
import re

# ========================= CONFIG =========================
API_URL = "https://apifreellm.com/api/v1/chat"
API_KEY = None  # Must be set via environment variable  # Your ApiFreeLLM key
LOG_FILE = "organizer_log.json"
ROLLBACK_MANIFEST = "organizer_rollback_manifest.json"
RATE_LIMIT_SECONDS = 6  # free tier: 1 request every 5 seconds

# Folders to exclude from scanning (app/system folders)
EXCLUDE_PATTERNS = {
    'appdata', 'isolatedstorage', 'temp', 'tmp', 'cache',
    '.git', '.vscode', '__pycache__', 'node_modules', '.env',
    'venv', 'env', '.pytest_cache', 'dist', 'build', '.next',
    'launchdarkly', 'system volume information', '$recycle.bin'
}
# =========================================================

def should_exclude(path_str: str) -> bool:
    """Check if a path should be excluded from scanning."""
    normalized = path_str.lower().replace('\\', '/')
    for pattern in EXCLUDE_PATTERNS:
        if pattern in normalized:
            return True
    return False

def select_root_folder():
    root = tk.Tk()
    root.withdraw()
    folder = filedialog.askdirectory(title="Select root folder to organize")
    if not folder:
        folder = input("Enter full path to root folder: ").strip()
    return Path(folder).resolve()

def scan_folder(root: Path):
    structure = {
        "files": [],
        "file_counts": defaultdict(int),
        "potential_projects": [],
        "loose_files": [],
        "top_level_summary": {}
    }

    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = Path(dirpath).relative_to(root)
        rel_str = str(rel_dir) if rel_dir != Path('.') else ""
        
        # Skip excluded folders
        if should_exclude(rel_str):
            dirnames[:] = []  # prevent recursion
            continue
        

        # Detect projects
        indicators = {'requirements.txt', 'package.json', 'pom.xml', 'setup.py',
                      'Cargo.toml', 'pyproject.toml', '.git', 'src', 'lib', 'tests', 'docs'}
        is_project = any(ind in filenames or ind in dirnames for ind in indicators)
        if is_project and rel_str:
            structure["potential_projects"].append(rel_str)

        for f in filenames:
            if f.startswith('.') and f != '.git':
                continue
            full_path = Path(dirpath) / f
            rel_path = rel_dir / f if rel_dir != Path('.') else Path(f)
            try:
                stat = full_path.stat()
            except Exception:
                # Skip files we can't stat (deleted/moved/permission issues)
                continue
            ext = full_path.suffix.lower()
            structure["file_counts"][ext] += 1
            file_info = {
                "rel_path": str(rel_path),
                "name": f,
                "ext": ext,
                "size_bytes": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
            structure["files"].append(file_info)
            if not rel_dir.parts:
                structure["loose_files"].append(file_info)

        if len(rel_dir.parts) <= 1:
            key = rel_str or "ROOT"
            structure["top_level_summary"][key] = {
                "file_count": len(filenames),
                "subfolders": len(dirnames),
                "is_project": is_project
            }

    return structure

def build_summary(structure):
    return {
        "total_files": len(structure["files"]),
        "file_type_counts": dict(sorted(structure["file_counts"].items(), key=lambda x: -x[1])[:20]),
        "loose_files_in_root": [f["name"] for f in structure["loose_files"][:50]],
        "detected_projects": structure["potential_projects"][:30],
        "top_level_folders": structure["top_level_summary"]
    }

def build_prompt(summary, root_name):
    prompt = f"""
You are an expert file system organizer.

Current folder: {root_name}
Summary:
{json.dumps(summary, indent=2)}

Rules (STRICT):
- NEVER split code projects. Folders in "detected_projects" move as a unit.
- PRESERVE original folder names where possible. Organize BY CATEGORY inside existing folders or minimal nesting.
- Max 3 levels deep in new structure.
- Do NOT create a single "Documents" bucket. Respect the existing top-level folder structure.
- Logical categories for organization: Projects, Code, Documents, Media (Images/Videos/Audio), Archives, Config, Misc.
- Clean messy names only when HIGH confidence.
- Preserve all files; do not delete anything unless instructed.
- Provide interactive plan for user approval.

Output Requirements:
- JSON object ONLY (no markdown, no extra text)
- Keys: "proposed_hierarchy", "actions", "explanations", "confidences"
- Actions must include: id, type (create_folder/move/rename), source, destination/new_name
- Confidence levels: high, medium, low
- Proposed hierarchy should show HOW the folder structure will look after changes.

Respond with structured JSON ONLY.
"""
    return prompt

def call_ai(prompt: str, api_key: str, max_retries=3):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    data = {"message": prompt, "model": "apifreellm"}
    for attempt in range(max_retries):
        try:
            resp = requests.post(API_URL, headers=headers, json=data, timeout=120)
            resp.raise_for_status()
            result = resp.json()
            if "response" in result:
                return result["response"]
            elif "message" in result:
                return result["message"]
            else:
                return str(result)
        except Exception as e:
            print(f"API error (attempt {attempt+1}): {e}")
            time.sleep(RATE_LIMIT_SECONDS)
    raise Exception("Failed to get response from ApiFreeLLM after retries.")

def extract_json(text: str):
    text = text.strip()
    try:
        return json.loads(text)
    except:
        pass
    match = re.search(r'```(?:json)?\s*(.+?)\s*```', text, re.DOTALL)
    if match:
        try: return json.loads(match.group(1))
        except: pass
    match = re.search(r'(\{.*\})', text, re.DOTALL)
    if match:
        try: return json.loads(match.group(1))
        except: pass
    raise ValueError("Could not parse JSON from AI response.")

def preview_folder_tree(suggestions, root_path: Path):
    """Show a visual preview of the proposed reorganization."""
    root = tk.Tk()
    root.title('Preview: Proposed Reorganization')
    root.geometry('900x600')

    # Left: treeview of proposed hierarchy
    left_frame = tk.Frame(root)
    left_frame.pack(side='left', fill='both', expand=True, padx=8, pady=8)
    
    tk.Label(left_frame, text='Proposed Structure:', font=('Arial', 10, 'bold')).pack(anchor='w')
    tree = tk.ttk.Treeview(left_frame, height=20)
    tree.pack(fill='both', expand=True)
    
    def build_tree(data, parent=''):
        if isinstance(data, dict):
            for k, v in data.items():
                node = tree.insert(parent, 'end', text=str(k), open=False)
                if isinstance(v, (dict, list)):
                    build_tree(v, node)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, str):
                    tree.insert(parent, 'end', text=item)
                else:
                    build_tree(item, parent)
    
    hierarchy = suggestions.get('proposed_hierarchy', {})
    build_tree(hierarchy)
    
    # Right: file preview (show current vs proposed for selected items)
    right_frame = tk.Frame(root)
    right_frame.pack(side='right', fill='both', expand=True, padx=8, pady=8)
    
    tk.Label(right_frame, text='Actions Summary:', font=('Arial', 10, 'bold')).pack(anchor='w')
    actions_text = tk.Text(right_frame, height=25, width=40, wrap='word')
    actions_text.pack(fill='both', expand=True)
    
    # Populate actions
    actions = suggestions.get('actions', [])
    text_content = f"Total Actions: {len(actions)}\n\n"
    for a in actions:
        aid = a.get('id')
        typ = a.get('type', '')
        src = a.get('source', '')
        dst = a.get('destination') or a.get('new_name', '')
        text_content += f"[{aid}] {typ.upper()}\n  {src} -> {dst}\n\n"
    
    actions_text.insert('1.0', text_content)
    actions_text.config(state='disabled')
    
    btn_close = tk.Button(right_frame, text='Close & Continue', command=root.destroy)
    btn_close.pack(pady=8)
    
    root.mainloop()

def display_suggestions(suggestions):
    print("\n" + "="*80)
    print("AI-PROPOSED REORGANIZATION")
    print("="*80)
    print(json.dumps(suggestions.get("proposed_hierarchy", {}), indent=2))
    print("\nACTIONS:")

    def _meta_value(sugg, meta_key, aid, default):
        meta = sugg.get(meta_key, {})
        if isinstance(meta, dict):
            return meta.get(str(aid), meta.get(aid, default))
        if isinstance(meta, list):
            # try list of dicts with id
            for item in meta:
                if isinstance(item, dict) and (item.get("id") == aid or item.get("id") == str(aid)):
                    for k in ("confidence", "conf", "value", "level", "explanation", "reason"):
                        if k in item:
                            return item[k]
                    for k, v in item.items():
                        if k != "id":
                            return v
            # try to align by action index
            actions = sugg.get("actions", [])
            for idx, act in enumerate(actions):
                if act.get("id") == aid or str(act.get("id")) == str(aid):
                    if idx < len(meta):
                        return meta[idx]
        return default

    for action in suggestions.get("actions", []):
        aid = action.get("id")
        typ = action.get("type", "")
        src = action.get("source", "")
        dst = action.get("destination") or action.get("new_name", "")
        conf = _meta_value(suggestions, "confidences", aid, "medium")
        expl = _meta_value(suggestions, "explanations", aid, "")
        print(f"\n[{aid}] {typ.upper()} | Confidence: {conf}")
        print(f"   {src} -> {dst}")
        print(f"   Reason: {expl}")

def get_user_approval(suggestions):
    while True:
        choice = input("\nApprove all (a), review individually (r), GUI review (g), or abort (q)? ").lower().strip()
        if choice == 'a':
            return suggestions.get("actions", [])
        elif choice == 'q':
            return None
        elif choice == 'g':
            try:
                return gui_review_actions(suggestions)
            except Exception as e:
                print(f"GUI review failed: {e}")
                continue
        elif choice == 'r':
            approved = []
            for action in suggestions.get("actions", []):
                aid = action.get("id")
                print(f"\nAction {aid}: {action.get('type','')} {action.get('source','')} → {action.get('destination','')}")
                ans = input("Approve? (y/n/skip) ").lower()
                if ans == 'y':
                    approved.append(action)
            return approved


### GUI review + speech-to-text support ###
try:
    import speech_recognition as sr
except Exception:
    sr = None

EMOJI_MAP = {
    'projects': '🗂️',
    'project': '🗂️',
    'code': '💻',
    'python': '🐍',
    'notebook': '📓',
    'documents': '📄',
    'doc': '📄',
    'pdf': '📄',
    'spreadsheet': '📊',
    'images': '🖼️',
    'image': '🖼️',
    'photo': '🖼️',
    'screenshot': '📸',
    'screenshots': '📸',
    'videos': '🎬',
    'video': '🎬',
    'audio': '🎧',
    'music': '🎵',
    'archives': '📦',
    'zip': '🗜️',
    'tar': '🗜️',
    'misc': '🧩',
    'logs': '📜',
    'config': '⚙️',
    'tests': '🧪'
}

def emoji_for_name(name: str):
    n = name.lower()
    for k, v in EMOJI_MAP.items():
        if k in n:
            return v
    return ''

def _recognize_speech_to_string():
    if sr is None:
        raise RuntimeError('speech_recognition package not installed')
    r = sr.Recognizer()
    with sr.Microphone() as mic:
        print('Listening... speak now')
        audio = r.listen(mic, timeout=5)
    try:
        text = r.recognize_google(audio)
        return text
    except Exception as e:
        raise RuntimeError(f'Speech recognition failed: {e}')

def gui_review_actions(suggestions):
    actions = suggestions.get('actions', [])
    root = tk.Tk()
    root.title('Review AI Actions')
    approved = []

    listbox = tk.Listbox(root, width=100, font=(None, 10))
    for a in actions:
        aid = a.get('id')
        typ = a.get('type','')
        src = a.get('source','')
        dst = a.get('destination') or a.get('new_name','')
        em = emoji_for_name(dst) or emoji_for_name(typ) or ''
        prefix = f"{em} " if em else ''
        listbox.insert(tk.END, f"{prefix}[{aid}] {typ} : {src} -> {dst}")
    listbox.grid(row=0, column=0, columnspan=4, padx=8, pady=8)

    edit_label = tk.Label(root, text='Edit destination / new name:')
    edit_label.grid(row=1, column=0, padx=8, sticky='w')
    entry = tk.Entry(root, width=80)
    entry.grid(row=1, column=1, columnspan=3, padx=8, pady=4)

    def on_select(evt=None):
        sel = listbox.curselection()
        if not sel: return
        idx = sel[0]
        a = actions[idx]
        dst = a.get('destination') or a.get('new_name','')
        entry.delete(0, tk.END)
        entry.insert(0, dst)
        # update emoji preview
        em = emoji_for_name(dst) or emoji_for_name(a.get('type',''))
        emoji_preview.config(text=em)

    def do_speak():
        try:
            text = _recognize_speech_to_string()
        except Exception as e:
            messagebox.showerror('Speech Error', str(e))
            return
        # insert into entry for user to edit
        entry.delete(0, tk.END)
        entry.insert(0, text)

    def add_emoji_to_entry():
        cur = entry.get()
        emoji = emoji_for_name(cur)
        if emoji and not cur.startswith(emoji):
            entry.delete(0, tk.END)
            entry.insert(0, f"{emoji} {cur}")
            emoji_preview.config(text=emoji)

    def approve_selected():
        sel = listbox.curselection()
        if not sel:
            messagebox.showinfo('Select', 'Select an action to approve')
            return
        idx = sel[0]
        a = actions[idx].copy()
        val = entry.get().strip()
        if 'destination' in a:
            a['destination'] = val
        elif 'new_name' in a:
            a['new_name'] = val
        else:
            a['destination'] = val
        approved.append(a)
        listbox.delete(idx)

    def finish():
        root.destroy()

    speak_btn = tk.Button(root, text='Speak', command=do_speak)
    # button frame for cleaner layout
    btn_frame = tk.Frame(root)
    btn_frame.grid(row=2, column=0, columnspan=4, pady=8)
    speak_btn.pack(in_=btn_frame, side='left', padx=6)
    emoji_btn = tk.Button(btn_frame, text='Add Emoji', command=add_emoji_to_entry)
    emoji_btn.pack(side='left', padx=6)
    approve_btn = tk.Button(btn_frame, text='Approve Selected', command=approve_selected)
    approve_btn.pack(side='left', padx=6)
    done_btn = tk.Button(btn_frame, text='Done', command=finish)
    done_btn.pack(side='left', padx=6)

    # emoji preview label
    emoji_preview = tk.Label(root, text='', font=(None, 20))
    emoji_preview.grid(row=1, column=0, sticky='w', padx=8)

    listbox.bind('<<ListboxSelect>>', on_select)
    # preselect first
    if actions:
        listbox.selection_set(0)
        on_select()

    root.mainloop()
    return approved


def execute_actions(root: Path, actions, dry_run=True):
    manifest, log = [], []
    for action in tqdm(actions, desc="Executing" if not dry_run else "Simulating"):
        typ = action["type"]
        if typ == "create_folder":
            target = root / action.get("destination", action.get("path", ""))
            if not dry_run: target.mkdir(parents=True, exist_ok=True)
            log.append({"type": "create", "path": str(target.relative_to(root))})
        elif typ in ("move", "rename"):
            source = root / action["source"]
            if not source.exists(): continue
            target = root / (action.get("destination") or (Path(action["source"]).parent / action.get("new_name", Path(action["source"]).name)))
            if not dry_run:
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists():
                    stem, suffix, counter = target.stem, target.suffix, 1
                    while target.exists():
                        target = target.with_name(f"{stem}_{counter}{suffix}")
                        counter += 1
                shutil.move(str(source), str(target))
            manifest.append({"original": str(source.relative_to(root)), "new": str(target.relative_to(root))})
            log.append({"type": typ, "from": str(source.relative_to(root)), "to": str(target.relative_to(root))})
    with open(root / LOG_FILE, "w") as f: json.dump(log, f, indent=2)
    with open(root / ROLLBACK_MANIFEST, "w") as f: json.dump(manifest, f, indent=2)
    print(f"\n{'Simulation' if dry_run else 'Execution'} complete. Log saved.")

def rollback(root: Path):
    manifest_path = root / ROLLBACK_MANIFEST
    if not manifest_path.exists(): return print("No rollback manifest found.")
    with open(manifest_path) as f: manifest = json.load(f)
    print("Rolling back...")
    for entry in reversed(manifest):
        original = root / entry["original"]
        new = root / entry["new"]
        if new.exists(): shutil.move(str(new), str(original))
    print("Rollback complete.")

def main():
    print("AI Folder Organizer (Safe & Reversible)")
    root = select_root_folder()
    print(f"Scanning {root}...")
    structure = scan_folder(root)
    summary = build_summary(structure)

    print("Calling AI for reorganization suggestions...")
    prompt = build_prompt(summary, root.name)
    ai_text = call_ai(prompt, API_KEY)

    try: suggestions = extract_json(ai_text)
    except Exception as e:
        print("Failed to parse AI response:")
        print(ai_text[:1000])
        return

    display_suggestions(suggestions)
    
    # Show visual preview before approval
    print("\nOpening visual preview...")
    preview_folder_tree(suggestions, root)
    
    approved_actions = get_user_approval(suggestions)
    if not approved_actions:
        print("Aborted by user."); return

    print("\nDRY RUN (no changes applied):")
    execute_actions(root, approved_actions, dry_run=True)

    if input("\nApply changes for real? (yes/no): ").lower() == "yes":
        execute_actions(root, approved_actions, dry_run=False)
        print(f"\nOrganization complete! Rollback manifest: {root / ROLLBACK_MANIFEST}")
    else:
        print("Changes not applied.")

    if input("\nRollback now? (only if something went wrong) (yes/no): ").lower() == "yes":
        rollback(root)

if __name__ == "__main__":
    main()
