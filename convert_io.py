import pandas as pd

input_file = r"samples\simple_io_list.xlsx.csv"
output_file = r"samples\simple_io_list.xlsx"

df = pd.read_csv(input_file)

df.to_excel(
    output_file,
    index=False,
    sheet_name="IO_List",
)

print("Excel file created successfully:")
print(output_file)