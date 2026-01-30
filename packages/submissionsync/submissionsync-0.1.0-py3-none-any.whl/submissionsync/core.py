from pathlib import Path
import seedir as sd
import win32com.client
from .shortcuts import create_shortcut

shell = None
try:
    shell = win32com.client.Dispatch("WScript.Shell")
except Exception:
    print("  ✗ pywin32 not installed; shortcuts will not be created")
    exit()

def mask(x):
    if x.is_dir() and ("Student Work" in str(x)):
        if "Enrichment" in str(x) or "Club" in str(x):
            return False
        if len(x.parts) > 5:
            if "Submitted files" in str(x):
                if len(x.parts) > 8:
                    if "Version" in str(x):
                        version_num = int(x.parts[-1].split(" ")[1]) + 1
                        next_folder = (x.parents[0] /
                                       ("Version " + str(version_num)))
                        return not next_folder.exists()
                    else:
                        return False
                else:
                    return True
            return False
        else:
            return True
    return False


def get_latest_mtime(path: Path) -> float:
    """Return the most recent modification time under a path."""
    if not path.exists():
        return 0.0
    latest = path.stat().st_mtime
    for p in path.rglob("*"):
        try:
            latest = max(latest, p.stat().st_mtime)
        except FileNotFoundError:
            continue
    return latest


def iter_latest_versions(base_path, cutoff_mtime=None, dbg=lambda *args, **kwargs: None):
    """Yield only latest version folders (optionally filtered by mtime)."""
    for folder in base_path.rglob("Version *"):
        if cutoff_mtime is not None:
            try:
                if folder.stat().st_mtime <= cutoff_mtime:
                    dbg(f"  - Skipping (not newer than cutoff): {folder}")
                    continue
            except FileNotFoundError:
                continue
        if mask(folder):
            yield folder


def create_symlink_structure(base_path, output_path, debug: bool = False, show_tree: bool = False, force: bool = False):
    """Create a directory structure with shortcuts to latest submitted versions."""
    
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    dbg = print if debug else (lambda *args, **kwargs: None)

    if show_tree:
        tree = sd.seedir(base_path, depthlimit=5, mask=mask, printout=False)
        g = sd.fakedir_fromstring(tree)
        g.seedir()

    dbg(f"Scanning for folders in: {base_path}")
    dbg(f"Output directory: {output_path}\n")
    dbg(f"Force rebuild: {force}")

    # Per-course mtime cache: {course_name: (src_latest, out_latest)}
    course_mtime_cache = {}

    processed = 0
    for folder in iter_latest_versions(base_path, cutoff_mtime=None, dbg=dbg):
        processed += 1
        dbg(f"\nProcessing: {folder}")
        dbg(f"  Parts: {folder.parts}")
        
        if "Version" in folder.parts[-1]:
            dbg(f"  ✓ Contains 'Version' in last part: {folder.parts[-1]}")
            
            # Check if the version folder has any files or subdirectories
            has_content = any(folder.iterdir())
            if not has_content:
                dbg(f"  ✗ Skipping - folder is empty (no submitted work)")
                continue
            
            dbg(f"  ✓ Folder has content")
            
            # Extract the relevant parts of folder.parts
            parts = folder.parts

            # Find the indices for the structure we want
            student_work_idx = next(i for i, p in enumerate(parts) if "Student Work" in p)
            dbg(f"  Student Work index: {student_work_idx}")

            # Build the relative path: Subject / Assignment / Student Name (Version X)
            relative_parts = parts[student_work_idx + 1:]  # Skip "Student Work"
            dbg(f"  Relative parts: {relative_parts}")

            # Find submitted files index to get student name
            submitted_idx = next((i for i, p in enumerate(relative_parts) if "Submitted files" in p), None)
            dbg(f"  Submitted files index: {submitted_idx}")

            if submitted_idx is not None and submitted_idx >= 0:
                # The structure is: Course - Student Work / Submitted files / Student Name / Assignment / Version X
                # We want: Course / Assignment / Student Name
                
                # Get the course name (before "- Student Work") from the full parts (not relative_parts)
                course_with_suffix = parts[student_work_idx]  # e.g., "Cyber EPQ 2025-26 Extended A - Student Work"
                course_name = course_with_suffix.replace(" - Student Work", "").strip()
                
                # Get student name (after "Submitted files")
                student_name = relative_parts[submitted_idx + 1]
                
                # Get assignment name (between student name and Version folder)
                assignment_parts = relative_parts[submitted_idx + 2:-1]  # Exclude the Version folder
                assignment_name = " - ".join(assignment_parts) if assignment_parts else "General"
                
                version_num = folder.parts[-1]
                
                dbg(f"  Course: {course_name}")
                dbg(f"  Assignment: {assignment_name}")
                dbg(f"  Student name: {student_name}")
                dbg(f"  Version: {version_num}")

                # Per-course mtime check (early exit before any shortcut work)
                if course_name not in course_mtime_cache:
                    source_course_path = Path(*parts[:student_work_idx + 1])  # includes "... - Student Work"
                    output_course_path = output_path / course_name
                    src_mtime = get_latest_mtime(source_course_path)
                    out_mtime = get_latest_mtime(output_course_path)
                    course_mtime_cache[course_name] = (src_mtime, out_mtime)
                    dbg(f"  Course mtime src={src_mtime}, out={out_mtime}")
                else:
                    src_mtime, out_mtime = course_mtime_cache[course_name]

                if not force and out_mtime >= src_mtime:
                    dbg(f"  - Course '{course_name}' up to date; skipping")
                    continue

                # Create output path: course/assignment/student
                target_dir = output_path / course_name / assignment_name
                shortcut_path = target_dir / (student_name + ".lnk")
                dbg(f"  Shortcut path: {shortcut_path}")

                shortcut_path.parent.mkdir(parents=True, exist_ok=True)

                # If force is True, always recreate; otherwise, skip if up to date
                if shortcut_path.exists() and not force:
                    try:
                        existing_target = Path(shell.CreateShortCut(str(shortcut_path)).Targetpath)
                        if existing_target.resolve() == Path(folder).resolve():
                            dbg("  - Shortcut already up to date; skipping")
                            continue
                        else:
                            dbg(f"  - Shortcut exists but points to {existing_target}; replacing")
                            shortcut_path.unlink(missing_ok=True)
                    except Exception as e:
                        dbg(f"  - Could not read existing shortcut (will recreate): {e}")
                elif shortcut_path.exists() and force:
                    dbg("  - Force enabled; recreating shortcut")
                    shortcut_path.unlink(missing_ok=True)

                try:
                    shortcut = shell.CreateShortCut(str(shortcut_path))
                    shortcut.Targetpath = str(folder)
                    shortcut.WorkingDirectory = str(folder.parent)
                    shortcut.save()
                    dbg(f"  ✓ Shortcut created/updated (points to {version_num})")
                    if not shortcut_path.exists():
                        raise Exception("Shortcut creation failed - file does not exist after save()")
                except Exception as e:
                    print(f"  ✗ Error creating shortcut: {e}")
                    print(f"\nStopping execution for debugging.")
                    raise
            else:
                dbg(f"  ✗ Submitted index is None or <= 0")
        else:
            dbg(f"  ✗ No 'Version' in last part")

    dbg(f"\nProcessed latest version folders: {processed}")