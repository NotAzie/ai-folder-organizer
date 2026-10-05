"""
Graphical user interface for AI Folder Organizer.

Provides a full-featured GUI with:
- Visual tree preview
- Action review and approval
- Speech recognition support (optional)
- Emoji assistance for folder naming
"""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from typing import Optional

# Optional speech recognition
try:
    import speech_recognition as sr
    SPEECH_AVAILABLE = True
except ImportError:
    sr = None
    SPEECH_AVAILABLE = False

from organiser.config import Config, load_config
from organiser.scanner import scan_folder, FolderStructure
from organiser.llm_client import create_client, LLMClient
from organiser.proposal import build_prompt, parseproposal, Proposal, Action
from organiser.executor import execute_actions, rollback, ActionExecutor


# Emoji mapping for folder/type suggestions
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
    'tests': '🧪',
    'create_folder': '📁',
    'move': '📂',
    'rename': '✏️',
}


def emoji_for_name(name: str) -> str:
    """Get emoji for a folder/file name."""
    name_lower = name.lower()
    for key, emoji in EMOJI_MAP.items():
        if key in name_lower:
            return emoji
    return ''


def emoji_for_type(action_type: str) -> str:
    """Get emoji for an action type."""
    return EMOJI_MAP.get(action_type, '')


class FolderOrganizerGUI:
    """
    Main GUI application for folder organization.

    Provides tabs for:
    - Folder selection and scanning
    - AI suggestion generation
    - Action review and approval
    - Execution and rollback
    """

    def __init__(self, root: Optional[Path] = None, config: Optional[Config] = None):
        self.root_path = root
        self.config = config or load_config()
        self.scanned_structure: Optional[FolderStructure] = None
        self.proposal: Optional[Proposal] = None
        self.approved_actions: list[dict] = []
        self.executor: Optional[ActionExecutor] = None

        self.app = tk.Tk()
        self.app.title("AI Folder Organizer")
        self.app.geometry("1000x700")

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the main UI components."""
        # Notebook for tabs
        notebook = ttk.Notebook(self.app)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)

        # Scan tab
        scan_frame = ttk.Frame(notebook)
        notebook.add(scan_frame, text="1. Scan Folder")
        self._setup_scan_tab(scan_frame)

        # Suggest tab
        suggest_frame = ttk.Frame(notebook)
        notebook.add(suggest_frame, text="2. AI Suggestions")
        self._setup_suggest_tab(suggest_frame)

        # Review tab
        review_frame = ttk.Frame(notebook)
        notebook.add(review_frame, text="3. Review & Approve")
        self._setup_review_tab(review_frame)

        # Execute tab
        execute_frame = ttk.Frame(notebook)
        notebook.add(execute_frame, text="4. Execute & Rollback")
        self._setup_execute_tab(execute_frame)

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(
            self.app,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _setup_scan_tab(self, frame: ttk.Frame) -> None:
        """Set up the scan tab."""
        # Folder selection
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=8)

        ttk.Button(
            btn_frame,
            text="Select Folder",
            command=self._select_folder,
        ).pack(side="left", padx=4)

        ttk.Button(
            btn_frame,
            text="Scan",
            command=self._scan_folder,
        ).pack(side="left", padx=4)

        # Scan info
        self.info_text = tk.Text(frame, height=10, wrap="word")
        self.info_text.pack(fill="both", expand=True, padx=8, pady=4)

        # Treeview for structure
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill="both", expand=True, padx=8, pady=4)

        self.tree = ttk.Treeview(tree_frame)
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(
            tree_frame, orient="vertical", command=self.tree.yview
        )
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Summary
        self.summary_label = ttk.Label(frame, text="", justify="left")
        self.summary_label.pack(pady=4)

    def _setup_suggest_tab(self, frame: ttk.Frame) -> None:
        """Set up the suggest tab."""
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=8)

        ttk.Button(
            btn_frame,
            text="Generate AI Suggestions",
            command=self._generate_suggestions,
        ).pack(side="left", padx=4)

        # Progress
        self.progress = ttk.Progressbar(frame, mode="indeterminate")
        self.progress.pack(fill="x", padx=8, pady=4)

        # Suggestions display
        self.suggest_text = tk.Text(frame, height=20, wrap="word")
        self.suggest_text.pack(fill="both", expand=True, padx=8, pady=4)

    def _setup_review_tab(self, frame: ttk.Frame) -> None:
        """Set up the review tab."""
        # Action list
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill="both", expand=True, padx=8, pady=4)

        self.action_listbox = tk.Listbox(list_frame, font=(None, 10))
        self.action_listbox.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(
            list_frame, orient="vertical", command=self.action_listbox.yview
        )
        scrollbar.pack(side="right", fill="y")
        self.action_listbox.configure(yscrollcommand=scrollbar.set)

        # Edit area
        edit_frame = ttk.Frame(frame)
        edit_frame.pack(fill="x", padx=8, pady=4)

        ttk.Label(edit_frame, text="Destination / New Name:").pack(side="left")
        self.edit_entry = ttk.Entry(edit_frame, width=60)
        self.edit_entry.pack(side="left", fill="x", expand=True, padx=4)

        # Emoji button
        ttk.Button(
            edit_frame,
            text="Add Emoji",
            command=self._add_emoji,
        ).pack(side="left", padx=4)

        # Speech button
        if SPEECH_AVAILABLE:
            ttk.Button(
                edit_frame,
                text="Speech Input",
                command=self._speech_input,
            ).pack(side="left", padx=4)

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=8)

        ttk.Button(
            btn_frame,
            text="Approve Selected",
            command=self._approve_selected,
        ).pack(side="left", padx=4)

        ttk.Button(
            btn_frame,
            text="Approve All",
            command=self._approve_all,
        ).pack(side="left", padx=4)

        ttk.Button(
            btn_frame,
            text="Done Reviewing",
            command=self._done_reviewing,
        ).pack(side="left", padx=4)

        self.review_status = ttk.Label(frame, text="")
        self.review_status.pack()

    def _setup_execute_tab(self, frame: ttk.Frame) -> None:
        """Set up the execute tab."""
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=8)

        ttk.Button(
            btn_frame,
            text="Dry Run (Simulate)",
            command=self._dry_run,
        ).pack(side="left", padx=4)

        ttk.Button(
            btn_frame,
            text="Execute Changes",
            command=self._execute,
        ).pack(side="left", padx=4)

        ttk.Button(
            btn_frame,
            text="Rollback",
            command=self._rollback,
        ).pack(side="left", padx=4)

        # Execution log
        self.log_text = tk.Text(frame, height=20, wrap="word")
        self.log_text.pack(fill="both", expand=True, padx=8, pady=4)

    def _select_folder(self) -> None:
        """Handle folder selection."""
        folder = filedialog.askdirectory(title="Select folder to organize")
        if folder:
            self.root_path = Path(folder).resolve()
            self.status_var.set(f"Selected: {self.root_path}")
            self.info_text.delete("1.0", tk.END)
            self.info_text.insert("1.0", f"Folder: {self.root_path}\n")
            self._update_tree()

    def _update_tree(self) -> None:
        """Update the tree view with current folder structure."""
        self.tree.delete(*self.tree.get_children())
        if not self.root_path or not self.root_path.exists():
            return

        try:
            for item in self.root_path.iterdir():
                if item.is_dir():
                    self.tree.insert("", "end", text=item.name, values=("Folder",))
                else:
                    self.tree.insert("", "end", text=item.name, values=("File",))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read folder: {e}")

    def _scan_folder(self) -> None:
        """Handle folder scan."""
        if not self.root_path:
            messagebox.showwarning("Warning", "Please select a folder first")
            return

        self.status_var.set("Scanning...")
        try:
            self.scanned_structure = scan_folder(
                self.root_path, self.config.exclude_patterns
            )
            self._update_info()
            self._update_tree()
            self.status_var.set(
                f"Scanned: {self.scanned_structure.total_files} files, "
                f"{len(self.scanned_structure.potential_projects)} projects"
            )
        except Exception as e:
            messagebox.showerror("Error", f"Scan failed: {e}")
            self.status_var.set("Scan failed")

    def _update_info(self) -> None:
        """Update info text with scan results."""
        if not self.scanned_structure:
            return

        self.info_text.delete("1.0", tk.END)
        self.info_text.insert("1.0", f"Root: {self.root_path}\n\n")

        self.info_text.insert("end", f"Total files: {self.scanned_structure.total_files}\n")
        self.info_text.insert("end", f"Potential projects: {len(self.scanned_structure.potential_projects)}\n")
        self.info_text.insert("end", f"Top-level folders: {len(self.scanned_structure.top_level_summary)}\n\n")

        self.info_text.insert("end", "File types:\n")
        for ext, count in sorted(
            self.scanned_structure.file_counts.items(),
            key=lambda x: -x[1]
        )[:10]:
            self.info_text.insert("end", f"  {ext or '(no ext)'}: {count}\n")

        if self.scanned_structure.potential_projects:
            self.info_text.insert("end", "\nDetected projects:\n")
            for proj in self.scanned_structure.potential_projects[:10]:
                self.info_text.insert("end", f"  - {proj}\n")

        # Summary
        summary_parts = []
        summary_parts.append(f"Total: {self.scanned_structure.total_files} files")
        summary_parts.append(f"Projects: {len(self.scanned_structure.potential_projects)}")
        self.summary_label.config(text=" | ".join(summary_parts))

    def _generate_suggestions(self) -> None:
        """Generate AI suggestions."""
        if not self.scanned_structure:
            messagebox.showwarning("Warning", "Please scan a folder first")
            return

        self.status_var.set("Generating suggestions...")
        self.suggest_text.delete("1.0", tk.END)
        self.progress.start()

        try:
            # Build summary
            summary = {
                "total_files": self.scanned_structure.total_files,
                "file_type_counts": dict(
                    sorted(self.scanned_structure.file_counts.items(),
                           key=lambda x: -x[1])[:20]
                ),
                "loose_files_in_root": [f.name for f in self.scanned_structure.loose_files[:50]],
                "detected_projects": self.scanned_structure.potential_projects[:30],
                "top_level_folders": self.scanned_structure.top_level_summary,
            }

            # Get AI response
            client = create_client("apifreellm", self.config)
            prompt = build_prompt(summary, self.root_path.name)
            ai_text = client.generate_response(prompt)

            # Parse proposal
            self.proposal = parseproposal(ai_text)

            # Display
            self.suggest_text.delete("1.0", tk.END)
            self.suggest_text.insert("1.0", "PROPOSED STRUCTURE:\n")
            self.suggest_text.insert("end", str(self.proposal.proposed_hierarchy))
            self.suggest_text.insert("end", "\n\nACTIONS:\n")
            for action in self.proposal.actions:
                dest = action.destination or action.new_name
                conf = self.proposal.get_action_confidence(action.id)
                self.suggest_text.insert("end", f"[{action.id}] {action.type}: {action.source} -> {dest} ({conf})\n")

            self.status_var.set(f"Suggestions ready: {len(self.proposal.actions)} actions")
            self._populate_action_list()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate suggestions: {e}")
            self.status_var.set("Failed to generate suggestions")
        finally:
            self.progress.stop()

    def _populate_action_list(self) -> None:
        """Populate the action listbox."""
        self.action_listbox.delete(0, tk.END)
        if not self.proposal:
            return

        for action in self.proposal.actions:
            dest = action.destination or action.new_name
            emoji = emoji_for_type(action.type) or emoji_for_name(dest)
            prefix = f"{emoji} " if emoji else ""
            self.action_listbox.insert(
                tk.END,
                f"{prefix}[{action.id}] {action.type}: {action.source} -> {dest}",
            )

        if self.proposal.actions:
            self.action_listbox.selection_set(0)
            self._on_select_action()

    def _on_select_action(self, event=None) -> None:
        """Handle action selection."""
        selection = self.action_listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        action = self.proposal.actions[idx]

        self.edit_entry.delete(0, tk.END)
        dest = action.destination or action.new_name
        self.edit_entry.insert(0, dest)

        emoji = emoji_for_name(dest) or emoji_for_type(action.type)
        self.emoji_preview.config(text=emoji)

    def _add_emoji(self) -> None:
        """Add emoji to current entry."""
        current = self.edit_entry.get()
        emoji = emoji_for_name(current)
        if emoji and not current.startswith(emoji):
            self.edit_entry.delete(0, tk.END)
            self.edit_entry.insert(0, f"{emoji} {current}")
            self.emoji_preview.config(text=emoji)

    def _speech_input(self) -> None:
        """Handle speech input."""
        if not SPEECH_AVAILABLE:
            messagebox.showerror("Error", "Speech recognition not available")
            return

        try:
            recognizer = sr.Recognizer()
            with sr.Microphone() as mic:
                self.status_var.set("Listening...")
                audio = recognizer.listen(mic, timeout=5)

            text = recognizer.recognize_google(audio)
            self.edit_entry.delete(0, tk.END)
            self.edit_entry.insert(0, text)
            self.status_var.set(f"Recognized: {text}")

        except Exception as e:
            messagebox.showerror("Speech Error", str(e))
            self.status_var.set("Speech recognition failed")

    def _approve_selected(self) -> None:
        """Approve selected action."""
        selection = self.action_listbox.curselection()
        if not selection:
            messagebox.showinfo("Select", "Select an action to approve")
            return

        idx = selection[0]
        action = self.proposal.actions[idx]
        action_dict = action.__dict__.copy()

        edited = self.edit_entry.get().strip()
        if edited:
            if "destination" in action_dict:
                action_dict["destination"] = edited
            elif "new_name" in action_dict:
                action_dict["new_name"] = edited

        self.approved_actions.append(action_dict)
        self.action_listbox.delete(idx)
        self.review_status.config(text=f"Approved: {len(self.approved_actions)} actions")

        if not self.action_listbox.size():
            self._done_reviewing()

    def _approve_all(self) -> None:
        """Approve all actions."""
        if not self.proposal:
            return

        self.approved_actions = [a.__dict__ for a in self.proposal.actions]
        self.action_listbox.delete(0, tk.END)
        self.review_status.config(text=f"Approved all: {len(self.approved_actions)} actions")
        self._done_reviewing()

    def _done_reviewing(self) -> None:
        """Finish reviewing."""
        self.status_var.set(f"Review complete: {len(self.approved_actions)} actions approved")
        self.review_status.config(text=f"Ready to execute: {len(self.approved_actions)} actions")

    def _dry_run(self) -> None:
        """Execute dry run."""
        if not self.approved_actions:
            messagebox.showwarning("Warning", "No actions to execute")
            return

        self.status_var.set("Running dry run...")
        self.log_text.delete("1.0", tk.END)

        try:
            self.executor = ActionExecutor(self.root_path, self.config, dry_run=True)
            logs = self.executor.execute_proposal(Proposal.from_dict({"actions": self.approved_actions}))

            success = sum(1 for log in logs if log.status in ("success", "simulated"))
            self.log_text.insert("1.0", f"Dry run complete: {success}/{len(logs)} actions\n\n")
            for log in logs:
                status_icon = "✓" if log.status in ("success", "simulated") else "✗"
                self.log_text.insert("end", f"{status_icon} {log.action_type}: {log.source} -> {log.destination}\n")

            self.status_var.set(f"Dry run: {success}/{len(logs)} actions")

        except Exception as e:
            messagebox.showerror("Error", f"Dry run failed: {e}")
            self.status_var.set("Dry run failed")

    def _execute(self) -> None:
        """Execute actual changes."""
        if not self.approved_actions:
            messagebox.showwarning("Warning", "No actions to execute")
            return

        if not messagebox.askyesno(
            "Confirm",
            f"About to execute {len(self.approved_actions)} file operations.\n\n"
            "This will move/rename files. A rollback manifest will be created.\n\n"
            "Continue?",
        ):
            return

        self.status_var.set("Executing...")
        self.log_text.delete("1.0", tk.END)

        try:
            self.executor = ActionExecutor(self.root_path, self.config, dry_run=False)
            logs = self.executor.execute_proposal(Proposal.from_dict({"actions": self.approved_actions}))

            success = sum(1 for log in logs if log.status == "success")
            errors = sum(1 for log in logs if log.status == "error")

            self.log_text.insert("1.0", f"Execution complete: {success} succeeded, {errors} failed\n\n")
            for log in logs:
                status_icon = "✓" if log.status == "success" else "✗"
                error_info = f" ({log.error_message})" if log.error_message else ""
                self.log_text.insert(
                    "end",
                    f"{status_icon} {log.action_type}: {log.source} -> {log.destination}{error_info}\n",
                )

            if self.root_path and self.config.rollback_manifest:
                self.log_text.insert(
                    "end",
                    f"\nRollback manifest: {self.root_path / self.config.rollback_manifest}",
                )

            self.status_var.set(f"Executed: {success} succeeded, {errors} failed")

        except Exception as e:
            messagebox.showerror("Error", f"Execution failed: {e}")
            self.status_var.set("Execution failed")

    def _rollback(self) -> None:
        """Perform rollback."""
        if not self.root_path:
            messagebox.showwarning("Warning", "No folder selected")
            return

        if not messagebox.askyesno(
            "Confirm Rollback",
            "This will undo all file operations using the rollback manifest.\n\n"
            "Continue?",
        ):
            return

        self.status_var.set("Rolling back...")
        try:
            success = rollback(self.root_path, self.config)
            if success:
                self.log_text.insert("1.0", "Rollback complete\n")
                self.status_var.set("Rollback complete")
            else:
                self.log_text.insert("1.0", "No rollback manifest found\n")
                self.status_var.set("No manifest found")
        except Exception as e:
            messagebox.showerror("Error", f"Rollback failed: {e}")
            self.status_var.set("Rollback failed")

    def run(self) -> None:
        """Run the GUI application."""
        self.app.mainloop()


def run_gui(config: Optional[Config] = None, root_path: Optional[Path] = None) -> None:
    """
    Run the GUI application.

    Args:
        config: Optional configuration.
        root_path: Optional initial root path.
    """
    app = FolderOrganizerGUI(root=root_path, config=config)
    app.run()


def gui_main() -> None:
    """Entry point for GUI mode."""
    run_gui()
