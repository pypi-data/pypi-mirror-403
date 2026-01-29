import os

def hashing():
    _read_file("Hashing.txt")

def linked_list():
    _read_file("LL.txt")

def queue_linked_list():
    _read_file("QueueLL.txt")

def searching():
    _read_file("Searching.txt")

def sorting():
    _read_file("Sorting.txt")

def stack_linked_list():
    _read_file("StackLL.txt")

def all():
    files = [
        "Hashing.txt",
        "LL.txt",
        "QueueLL.txt",
        "Searching.txt",
        "Sorting.txt",
        "StackLL.txt"
    ]

    for file in files:
        print(f"\n----- {file.replace('.txt','')} -----\n")
        _read_file(file)

def _read_file(filename):
    base_path = os.path.dirname(__file__)
    file_path = os.path.join(base_path, filename)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            print(f.read())
    except FileNotFoundError:
        print(f"{filename} not found.")
