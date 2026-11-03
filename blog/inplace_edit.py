"""Replace one exact string in a file IN PLACE (same inode), so hard links (e.g. the Obsidian copy) stay linked.
Usage: python -I inplace_edit.py <file> <old_text_file> <new_text_file>"""
import sys
path, old, new = sys.argv[1], open(sys.argv[2]).read(), open(sys.argv[3]).read()
with open(path, "r+") as f:
    s = f.read()
    assert s.count(old) == 1, f"old text found {s.count(old)} times"
    f.seek(0); f.write(s.replace(old, new)); f.truncate()
