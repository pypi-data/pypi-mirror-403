import os
import re


def get_indent_level(line: str) -> int:
    """
    Calculate indentation level based on tree prefix.
    Each "│   " or "    " counts as 1 level.
    """
    prefix = re.match(r"^(?:│   |    )*", line).group()
    return prefix.count("│   ") + prefix.count("    ")


def create_structure_from_txt(txt_file, base_path=".", dry_run=False):
    stack = []
    root_created = False

    with open(txt_file, "r", encoding="utf-8") as file:
        for raw_line in file:
            line = raw_line.rstrip()
            if not line:
                continue

            indent = get_indent_level(line)
            name = line.split("──")[-1].strip()
            clean_name = name.rstrip("/")

            # If root folder not created yet
            if not root_created and name.endswith("/"):
                root_created = True
                stack = [clean_name]
                current_path = os.path.join(base_path, clean_name)

                if dry_run:
                    print(f"[DIR ] {current_path}")
                else:
                    os.makedirs(current_path, exist_ok=True)
                continue

            # For lines after root: treat indent 0 as level 1
            if root_created and indent == 0:
                level = 1
            else:
                level = indent + 1

            # Adjust stack depth
            while len(stack) > level:
                stack.pop()

            current_path = os.path.join(base_path, *stack, clean_name)

            if name.endswith("/"):
                if dry_run:
                    print(f"[DIR ] {current_path}")
                else:
                    os.makedirs(current_path, exist_ok=True)
                stack.append(clean_name)
            else:
                if dry_run:
                    print(f"[FILE] {current_path}")
                else:
                    os.makedirs(os.path.dirname(current_path), exist_ok=True)
                    open(current_path, "w", encoding="utf-8").close()
