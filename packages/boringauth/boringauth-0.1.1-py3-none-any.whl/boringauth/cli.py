from pathlib import Path

BASE_DIR = Path(__file__).parent
PRESETS_DIR = BASE_DIR / "presets"


def generate_preset(preset: str = "basic"):
    preset_dir = PRESETS_DIR / preset
    if not preset_dir.exists():
        print(f"Preset '{preset}' not found")
        return

    target = Path.cwd() / "auth"
    target.mkdir(exist_ok=True)

    for file in preset_dir.iterdir():
        if file.name == "__init__.py":
            continue
        (target / file.name).write_text(file.read_text())

    (target / "__init__.py").touch(exist_ok=True)

    print(f"'{preset}' auth preset generated in ./auth")


def main():
    # for now: no args, always basic
    generate_preset("basic")


if __name__ == "__main__":
    main()
