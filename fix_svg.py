from __future__ import annotations

with open("static/images/samson.svg") as f:
    lines = f.readlines()

# Find all path elements and keep only non-black ones
output_lines = []
in_path = False
path_content = []
is_black = False

for line in lines:
    if "<path" in line:
        in_path = True
        path_content = [line]
        is_black = 'fill="#000000"' in line
    elif in_path:
        path_content.append(line)
        if "</path>" in line:
            if not is_black:
                output_lines.extend(path_content)
            in_path = False
            path_content = []
    else:
        output_lines.append(line)

with open("static/images/samson.svg", "w") as f:
    f.writelines(output_lines)

print("Black paths removed")
