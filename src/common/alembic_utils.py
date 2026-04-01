from importlib import import_module
from pathlib import Path
from sqlalchemy.orm import configure_mappers


def load_models():
    base_dir = Path(__file__).parent.parent  # points to src/

    for path in base_dir.rglob("models.py"):
        module_path = path.relative_to(base_dir).with_suffix("")
        module_name = ".".join(module_path.parts)

        # 🔥 prepend "src"
        full_module_name = f"src.{module_name}"

        print(f"Importing: {full_module_name}")
        import_module(full_module_name)

    configure_mappers()


if __name__ == "__main__":
    load_models()
