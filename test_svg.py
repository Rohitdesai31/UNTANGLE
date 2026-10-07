from m3_simplify.svg_generator import generate_svg
import os

graph = {
    "nodes": [
        {
            "id": "A",
            "tag": "TK-101",
            "type": "tank",
            "layout": {"x": 150, "y": 150},
        },
        {
            "id": "B",
            "tag": "P-101",
            "type": "pump",
            "layout": {"x": 370, "y": 150},
        },
    ],
    "edges": [
        {
            "id": "E1",
            "source": "A",
            "target": "B",
            "route": [
                [150, 150],
                [260, 150],
                [260, 150],
                [370, 150],
            ],
        }
    ],
}

path = "fixtures/test_sketch.svg"

generate_svg(graph, path)

assert os.path.exists(path)

with open(path, "r", encoding="utf-8") as file:
    content = file.read()

assert content.startswith("<?xml")
assert "<svg" in content
assert "TK-101" in content
assert "P-101" in content
assert "marker-end=" in content

print("SVG GENERATION TEST PASSED")
print("Output:", path)