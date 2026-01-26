from pathlib import Path
content = Path("hello.txt").read_text()
assert content == "Hello, world!\n", f"Got: {content!r}"
print("OK")
