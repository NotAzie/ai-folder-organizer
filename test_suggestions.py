from anaa import display_suggestions, get_user_approval
import builtins

samples = []

# 1: expected dict-of-dicts
samples.append({
    "proposed_hierarchy": {"Projects": ["projA"]},
    "actions": [{"id": 1, "type": "move", "source": "a.txt", "destination": "Projects/projA/a.txt"}],
    "confidences": {"1": "high"},
    "explanations": {"1": "Clearly a project file."}
})

# 2: confidences as list aligned by index
samples.append({
    "proposed_hierarchy": {"Misc": []},
    "actions": [{"id": "x", "type": "rename", "source": "b.txt", "new_name": "b_old.txt"}],
    "confidences": ["low"],
    "explanations": ["Probably user file."]
})

# 3: confidences as list of dicts with id
samples.append({
    "proposed_hierarchy": {},
    "actions": [{"id": 42, "type": "create_folder", "destination": "New"}],
    "confidences": [{"id": 42, "confidence": "medium"}],
    "explanations": [{"id": 42, "explanation": "Grouping related files."}]
})

# Auto-approve by monkeypatching input
orig_input = builtins.input
builtins.input = lambda prompt='': 'a'

for idx, s in enumerate(samples, 1):
    print('\n--- SAMPLE', idx, '---')
    display_suggestions(s)
    approved = get_user_approval(s)
    print('Approved:', approved)

# Restore input
builtins.input = orig_input
print('\nAll tests completed')
