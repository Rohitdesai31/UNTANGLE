import json

from m1_vision.line_detector import associate_lines_with_symbols


SYMBOLS_PATH = "output/m1_test/symbols.json"
LINES_PATH = "output/m1_test/lines.json"
OUTPUT_PATH = "output/m1_test/associations.json"


# Load symbols
with open(SYMBOLS_PATH, "r", encoding="utf-8") as file:
    all_symbols = json.load(file)

symbols = [
    symbol
    for symbol in all_symbols
    if symbol["page"] == 2
]


# Load lines
with open(LINES_PATH, "r", encoding="utf-8") as file:
    lines = json.load(file)


# Associate line endpoints with symbols
associations = associate_lines_with_symbols(
    lines,
    symbols
)


# Save associations
with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
    json.dump(associations, file, indent=2)


print("Association test complete.")
print(f"Page 2 symbols: {len(symbols)}")
print(f"Lines: {len(lines)}")
print(f"Associations: {len(associations)}")
print(f"Saved: {OUTPUT_PATH}")

print("\nAssociations:")
for association in associations:
    print(association)