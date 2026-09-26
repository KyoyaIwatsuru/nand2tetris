import argparse
import glob

from .compilation_engine import CompilationEngine


def main():
    parser = argparse.ArgumentParser(
        description="Compile a Jack file (or directory of Jack files) "
        "into XML."
    )
    parser.add_argument(
        "path", help="path to a .jack file or a directory of .jack files"
    )

    args = parser.parse_args()
    path = args.path

    if path.endswith(".jack"):
        compile(path)

    else:
        if path.endswith("/"):
            path = path[:-1]
        files = glob.glob(f"{path}/*")
        for filepath in files:
            if filepath.endswith(".jack"):
                compile(filepath)


def compile(filepath):
    with CompilationEngine(filepath) as ce:
        print(f"compiling {filepath} ...")
        ce.compileClass()


if __name__ == "__main__":
    main()
