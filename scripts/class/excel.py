import pandas as pd
import json

sheet_url = "https://docs.google.com/spreadsheets/d/1cma0J7eTugMeRtG8VCHbYiHb5RlJ6TLK_SPYUoxfDFA/edit#gid=0"

csv_url = sheet_url.replace("/edit#gid=", "/export?format=csv&gid=")

df = pd.read_csv(csv_url)
print(df)

alltasks = {}
for row_idx in range(len(df)):
	if row_idx == 0:
		continue
	g = df.iat[row_idx, 0]
	tasks = []
	for col_idx in range(1,len(df.columns)):
		cell_value = df.iat[row_idx, col_idx]
		t =  [df.iat[0, col_idx], cell_value];
		tasks.append(t)
		print(f"Row {row_idx}, Col {col_idx} -> {cell_value}")
	alltasks[g] = tasks;


json_data = json.dumps(
    alltasks,
    ensure_ascii=False,  # keep accents (ò, è, í, etc.)
    indent=2
)

print(json_data)