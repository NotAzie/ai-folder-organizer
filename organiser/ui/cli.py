"""
Command-line interface for AI Folder Organizer.

Provides interactive CLI mode with multiple approval options:
- Approve all actions
- Review individually
- GUI review
- Abort
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import tkinter as tk
from tkinter import filedialog

from organiser.config import Config, load_config
from organiser.scanner import scan_folder, FolderStructure
from organiser.llm_client import create_client, LLMClient
from organiser.proposal import build_prompt, parseproposal, Proposal
from organiser.executor import execute_actions, rollback, ActionExecutor
from organiser.ui.gui import FolderOrganizerGUI


def select_root_folder(headless: bool = False) -> Optional[Path]:
    """
    Prompt user to select a root folder.

    Args:
        headless: If True, use command-line input instead of GUI dialog.

    Returns:
        Selected folder path, or None if cancelled.
    """
    if headless:
        folder = input("Enter full path to root folder: ").strip()
        if not folder:
            return None
        return Path(folder).resolve()

    # GUI dialog
    try:
        root = tk.Tk()
        root.withdraw()  # Hide main window
        folder = filedialog.askdirectory(title="Select root folder to organize")
        root.destroy()
        if not folder:
            folder = input("Enter full path to root folder: ").strip()
        return Path(folder).resolve() if folder else None
    except Exception:
        # Fallback to CLI if GUI fails
        folder = input("Enter full path to root folder: ").strip()
        return Path(folder).resolve() if folder else None


def display_suggestions(proposal: Proposal) -> None:
    """
    Display proposal suggestions in the terminal.

    Args:
        proposal: Proposal to display.
    """
    print("\n" + "=" * 80)
    print("AI-PROPOSED REORGANIZATION")
    print("=" * 80)
    print("\nPROPOSED STRUCTURE:")
    print(proposal.proposed_hierarchy)

    print("\n" + "-" * 80)
    print("ACTIONS:")
    print("-" * 80)

    for action in proposal.actions:
        confidence = proposal.get_action_confidence(action.id)
        explanation = proposal.get_action_explanation(action.id)

        destination = action.destination or action.new_name
        print(f"\n[{action.id}] {action.type.upper()} | Confidence: {confidence}")
        print(f"   {action.source} -> {destination}")
        if explanation:
            print(f"   Reason: {explanation}")


def get_user_approval(proposal: Proposal) -> list[dict] | None:
    """
    Get user approval for proposed actions.

    Args:
        proposal: Proposal to get approval for.

    Returns:
        List of approved actions, or None if aborted.
    """
    while True:
        print("\n" + "-" * 80)
        choice = input(
            "\nApprove all (a), review individually (r), "
            "GUI review (g), or abort (q)? "
        ).lower().strip()

        if choice == 'a':
            return [action.__dict__ for action in proposal.actions]
        elif choice == 'q':
            return None
        elif choice == 'g':
            try:
                return preview_and_review_gui(proposal)
            except Exception as e:
                print(f"GUI review failed: {e}")
                continue
        elif choice == 'r':
            return review_individually(proposal)
        else:
            print("Invalid choice. Please enter 'a', 'r', 'g', or 'q'.")


def review_individually(proposal: Proposal) -> list[dict]:
    """
    Review and approve actions one by one.

    Args:
        proposal: Proposal to review.

    Returns:
        List of approved actions.
    """
    approved = []
    for action in proposal.actions:
        destination = action.destination or action.new_name
        print(f"\nAction {action.id}: {action.type} {action.source} -> {destination}")
        print(f"  Confidence: {proposal.get_action_confidence(action.id)}")
        if proposal.get_action_explanation(action.id):
            print(f"  Reason: {proposal.get_action_explanation(action.id)}")

        ans = input("Approve? (y/n/skip) ").lower().strip()
        if ans == 'y':
            approved.append(action.__dict__)

    return approved


def preview_and_review_gui(proposal: Proposal) -> list[dict]:
    """
    Show GUI preview and collect approvals.

    Args:
        proposal: Proposal to review.

    Returns:
        List of approved actions.
    """
    approved = []

    def approve_selected():
        """Handle approve button click."""
        selection = listbox.curselection()
        if not selection:
            status_label.config(text="Select an action to approve")
            return

        idx = selection[0]
        action_dict = proposal.actions[idx].__dict__.copy()

        # Get edited destination from entry
        edited_dest = entry.get().strip()
        if edited_dest:
            if "destination" in action_dict:
                action_dict["destination"] = edited_dest
            elif "new_name" in action_dict:
                action_dict["new_name"] = edited_dest

        approved.append(action_dict)
        listbox.delete(idx)
        status_label.config(text=f"Approved: {len(approved)} actions")

        if not listbox.size():
            finish()

    def finish():
        """Close the window."""
        root.destroy()

    # Create GUI
    root = tk.Tk()
    root.title("Review AI Actions")
    root.geometry("900x600")

    # Listbox for actions
    listbox = tk.Listbox(root, width=100, font=(None, 10))
    listbox.grid(row=0, column=0, columnspan=4, padx=8, pady=8, sticky="nsew")

    # Populate listbox
    for idx, action in enumerate(proposal.actions):
        destination = action.destination or action.new_name
        listbox.insert(
            tk.END,
            f"[{action.id}] {action.type}: {action.source} -> {destination}",
        )

    # Entry for editing destination
    tk.Label(root, text="Edit destination / new name:").grid(
        row=1, column=0, padx=8, sticky="w"
    )
    entry = tk.Entry(root, width=80)
    entry.grid(row=1, column=1, columnspan=3, padx=8, pady=4)

    # Status label
    status_label = tk.Label(root, text="", fg="green")
    status_label.grid(row=2, column=0, columnspan=4, pady=4)

    # Buttons
    btn_frame = tk.Frame(root)
    btn_frame.grid(row=3, column=0, columnspan=4, pady=8)

    tk.Button(
        btn_frame,
        text="Approve Selected",
        command=approve_selected,
    ).pack(side="left", padx=6)

    tk.Button(btn_frame, text="Done", command=finish).pack(side="left", padx=6)

    # Bind selection event
    listbox.bind("<<ListboxSelect>>", lambda e: (
        entry.delete(0, tk.END),
        entry.insert(0, proposal.actions[listbox.curselection()[0]].destination or
                    proposal.actions[listbox.curselection()[0]].new_name)
    ) if listbox.curselection() else None)

    # Preselect first item
    if proposal.actions:
        listbox.selection_set(0)
        entry.delete(0, tk.END)
        entry.insert(0, proposal.actions[0].destination or proposal.actions[0].new_name)

    root.mainloop()
    return approved


def run_cli(config: Optional[Config] = None, headless: bool = False) -> int:
    """
    Run the main CLI application.

    Args:
        config: Optional configuration. If None, loads from environment.
        headless: If True, use CLI for folder selection instead of GUI dialog.

    Returns:
        Exit code (0 for success, 1 for error/cancel).
    """
    if config is None:
        config = load_config()

    print("=" * 80)
    print("AI Folder Organizer - Safe & Reversible")
    print("=" * 80)

    # Select folder
    root = select_root_folder(headless=headless)
    if not root:
        print("No folder selected. Exiting.")
        return 1

    if not root.exists():
        print(f"Error: Folder does not exist: {root}")
        return 1

    print(f"\nScanning {root}...")
    structure = scan_folder(root, config.exclude_patterns)
    summary = {
        "total_files": structure.total_files,
        "file_type_counts": dict(
            sorted(structure.file_counts.items(), key=lambda x: -x[1])[:20]
        ),
        "loose_files_in_root": [f.name for f in structure.loose_files[:50]],
        "detected_projects": structure.potential_projects[:30],
        "top_level_folders": structure.top_level_summary,
    }

    print(f"Found {structure.total_files} files, "
          f"{len(structure.potential_projects)} potential projects")

    # Create LLM client and get suggestions
    print("\nGenerating organization suggestions...")
    try:
        client = create_client("apifreellm", config)
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Set AI_FOLDER_ORG_API_KEY environment variable to use AI suggestions.")
        print("Running in manual mode without AI...")
        return 1

    prompt = build_prompt(summary, root.name)
    try:
        ai_text = client.generate_response(prompt)
    except Exception as e:
        print(f"Failed to get AI suggestions: {e}")
        return 1

    # Parse proposal
    try:
        proposal = parseproposal(ai_text)
    except Exception as e:
        print(f"Failed to parse AI response: {e}")
        print("Raw response:")
        print(ai_text[:1000])
        return 1

    # Display and get approval
    display_suggestions(proposal)

    print("\nOpening visual preview...")
    # Show preview in GUI
    preview_gui = FolderOrganizerGUI(root=root, config=config)
    preview_gui.proposal = proposal
    preview_gui._populate_action_list()
    preview_gui.app.title("Preview: Proposed Reorganization")
    preview_gui.app.mainloop()

    approved_actions = get_user_approval(proposal)
    if not approved_actions:
        print("Aborted by user.")
        return 1

    # Dry run
    print("\n" + "=" * 80)
    print("DRY RUN (no changes applied):")
    print("=" * 80)
    executor = ActionExecutor(root, config, dry_run=True)
    logs = executor.execute_proposal(Proposal.from_dict({"actions": approved_actions}))

    success_count = sum(1 for log in logs if log.status in ("success", "simulated"))
    print(f"\nSimulation complete: {success_count}/{len(logs)} actions would execute")

    # Ask to apply
    if input("\nApply changes for real? (yes/no): ").lower() == "yes":
        print("\nExecuting changes...")
        executor = ActionExecutor(root, config, dry_run=False)
        logs = executor.execute_proposal(Proposal.from_dict({"actions": approved_actions}))

        success_count = sum(1 for log in logs if log.status == "success")
        error_count = sum(1 for log in logs if log.status == "error")

        print(f"\nExecution complete: {success_count} succeeded, {error_count} failed")
        print(f"Rollback manifest: {root / config.rollback_manifest}")

        # Ask about rollback
        if input("\nRollback now? (only if something went wrong) (yes/no): ").lower() == "yes":
            rollback(root, config)
    else:
        print("Changes not applied.")

    return 0


def cli_main() -> None:
    """Entry point for CLI mode."""
    sys.exit(run_cli(headless="--headless" in sys.argv))
