"""Create a symlink-only TUM RGB-D subset from the first N RGB/depth entries."""
import argparse
from pathlib import Path


def entries(path: Path, count: int) -> list[str]:
    lines = [line for line in path.read_text().splitlines() if line and not line.startswith("#")]
    if len(lines) < count:
        raise ValueError(f"{path} has only {len(lines)} entries; requested {count}")
    return lines[:count]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="extracted full TUM scene directory")
    parser.add_argument("target", type=Path, help="new small scene directory")
    parser.add_argument("--count", type=int, default=80)
    args = parser.parse_args()
    source, target = args.source.resolve(), args.target.resolve()
    if target.exists():
        raise FileExistsError(f"target already exists: {target}")
    if args.count < 1:
        raise ValueError("count must be positive")
    selected = {kind: entries(source / f"{kind}.txt", args.count) for kind in ("rgb", "depth")}
    for kind, lines in selected.items():
        for line in lines:
            relative = Path(line.split()[1])
            if relative.parts[0] != kind or not (source / relative).is_file():
                raise ValueError(f"invalid {kind} entry: {line}")
    target.mkdir(parents=True)
    for kind, lines in selected.items():
        (target / kind).mkdir()
        (target / f"{kind}.txt").write_text("\n".join(lines) + "\n")
        for line in lines:
            relative = Path(line.split()[1])
            (target / relative).symlink_to(source / relative)
    (target / "groundtruth.txt").symlink_to(source / "groundtruth.txt")
    print(f"Created {target} with {args.count} RGB and depth entries")


if __name__ == "__main__":
    main()
