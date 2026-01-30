import argparse
from scaffold.generator import create_structure_from_txt


def main():
    parser = argparse.ArgumentParser(
        description="Generate files and folders from a tree-style text file"
    )
    parser.add_argument("structure_file", help="Path to folder structure text file")
    parser.add_argument("-o", "--output", default=".", help="Output directory")
    parser.add_argument("--dry-run", action="store_true", help="Preview only")

    args = parser.parse_args()

    create_structure_from_txt(
        txt_file=args.structure_file,
        base_path=args.output,
        dry_run=args.dry_run
    )

    if not args.dry_run:
        print("✅ Folder structure created successfully!")


if __name__ == "__main__":
    main()
