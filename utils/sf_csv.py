import csv


def read_csv_file(from_path):
    encodings = ['utf-8', 'cp1251']
    delimiters = [';', ',']

    for f_delimiter in delimiters:
        for enc in encodings:
            try:
                rows = []
                with open(from_path, encoding=enc) as f:
                    reader = csv.DictReader(f, delimiter=f_delimiter)
                    for row in reader:
                        rows.append(dict(row))
                if len(rows) > 0:
                    first_row = rows[0]
                    keys = first_row.keys()
                    if len(keys) > 1:
                        return rows
            except:
                pass
    raise ValueError(f'Не удалось прочитать данные из CSV файла {from_path}')
