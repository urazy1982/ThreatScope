Place completed label files here before running the analysis:

- `A.xlsx` / `B.xlsx` (or `.csv` with columns `item_id,relevant`): one file per annotator
- `adjudication.csv`: `item_id,relevant` for every disagreement after joint review

Only commit the `item_id` and `relevant` columns. Do not commit sheets that
contain sentence text (`context_before`, `TARGET_sentence`). Export with:

```bash
python3 -c "import csv,openpyxl,sys;ws=openpyxl.load_workbook(sys.argv[1])['label_here'];w=csv.writer(open(sys.argv[2],'w',newline=''));w.writerow(['item_id','relevant']);[w.writerow([r[0],r[5]]) for r in ws.iter_rows(min_row=2,values_only=True)]" A.xlsx A.csv
```
