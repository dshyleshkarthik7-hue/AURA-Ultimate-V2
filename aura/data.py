from pathlib import Path

IMAGE_EXTENSIONS={".jpg", ".jpeg", ".png"}

def image_files(root):
    root=Path(root)
    return sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS)

def validate_dataset(root, labels, minimum):
    root=Path(root); problems=[]; mapping={}
    for label in labels:
        files=image_files(root/label); mapping[label]=files
        if len(files)<minimum: problems.append(f"{label}: {len(files)} < {minimum}")
    unexpected=[p.name for p in root.iterdir() if p.is_dir() and p.name not in labels]
    if unexpected: problems.append("unexpected labels: "+", ".join(unexpected))
    if problems: raise ValueError("Dataset contract failed: "+"; ".join(problems))
    return mapping
