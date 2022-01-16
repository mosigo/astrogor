import csv
from datetime import datetime, timedelta

import cairo
from transliterate import translit

from model.sf_flatlib import FlatlibBuilder
from view.sf_cairo import SimpleFormulaDrawer
from view.sf_layout import DefaultLayoutMaker, RectangleFormulaCutter
from view.sf_layout_angles import AnglesLayoutMaker, RectangleCutPolicy


class Person:

    def __init__(self, name: str, birthday: datetime, pages: [int], work: str) -> None:
        self.work = work
        self.pages = pages
        self.birthday = birthday
        self.name = name

    def __str__(self) -> str:
        s = self.name
        s += '\n  ' + str(self.birthday)
        s += '\n  ' + str(self.pages)
        s += '\n  ' + self.work
        return s

    def __repr__(self) -> str:
        return self.__str__()


def parse_person(row) -> Person:
    birthday = datetime.strptime(row['birthday'], '%d.%m.%Y')
    pages = [int(a.strip()) for a in row['page'].split(',') if a]
    name = row['name'].strip()
    work = row['work'].strip()
    return Person(name, birthday, pages, work)


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


if __name__ == '__main__':
    # path_to_csv = '/Users/mosigo/Yandex.Disk.localized/Documents/Формула Души/формулы_из_учебника_small.csv'
    path_to_csv = '/Users/mosigo/Yandex.Disk.localized/Documents/Формула Души/формулы_из_учебника.csv'
    out_dir = '/Users/mosigo/Yandex.Disk.localized/Documents/Формула Души/pics'

    formula_width = 100
    formula_height = 70
    title_height = 15

    title_font_size = 0.04
    subtitle_font_size = 0.03

    width = formula_width
    height = formula_height + title_height

    builder = FlatlibBuilder()
    # layout_maker = DefaultLayoutMaker(RectangleFormulaCutter(formula_width, formula_height))
    layout_maker = AnglesLayoutMaker()
    drawer = SimpleFormulaDrawer()

    rows = read_csv_file(path_to_csv)
    for row in rows:
        person = parse_person(row)
        print(person)

        name_tr = translit(person.name, "ru", reversed=True)
        name_tr = name_tr.replace(' ', '_').replace('\'', '').replace('.', '_').lower()
        name_tr += '.pdf'

        out_path = out_dir + '/' + name_tr
        print(f'Сохраняю формулу в файл {name_tr}...')

        surface_pdf = cairo.PDFSurface(out_path, width, height)
        cr0 = cairo.Context(surface_pdf)
        cr0.scale(formula_width, formula_width)

        cr = cairo.Context(surface_pdf.create_for_rectangle(0, title_height, formula_width, formula_height))
        cr.scale(formula_width, formula_width)

        formula = builder.build_formula(person.birthday + timedelta(hours=12))

        cut_policy = RectangleCutPolicy(formula_width, formula_height)
        d_formula = layout_maker.make_layout(formula, formula_width, formula_height, cut_policy=cut_policy)
        drawer.draw_formula(d_formula, cr)

        diff = title_height * 0.3
        xr, yr = width - title_height - 2 * diff, -1.5 * diff
        wr, hr = title_height + 2 * diff, title_height + 2 * diff
        cr1 = cairo.Context(surface_pdf.create_for_rectangle(xr, yr, wr, hr))
        cr1.scale(title_height + 2 * diff, title_height + 2 * diff)
        drawer.draw_power_points(formula, cr1)

        cr0.set_line_width(0.001)
        cr0.set_source_rgb(0, 0, 0)
        x, y = 0, 0
        w, h = formula_width / width, title_height / width
        cr0.rectangle(x, y, w, h)
        cr0.stroke()

        x, y = 0, title_height / width
        w, h = formula_width / width, formula_height / width
        cr0.rectangle(x, y, w, h)
        cr0.stroke()

        cr0.set_font_size(title_font_size)
        space = (title_height / width) * 0.1
        cr0.select_font_face("Montserrat Light", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        x1, y1 = 0 + space, title_height / width / 3
        cr0.move_to(x1, y1)
        cr0.show_text(person.name)
        cr0.stroke()
        cr0.set_font_size(subtitle_font_size)
        x2, y2 = 0 + space, 2 * title_height / width / 3 - space
        cr0.move_to(x2, y2)
        cr0.show_text(person.work[0:1].lower() + person.work[1:])
        cr0.stroke()
        cr0.set_font_size(title_font_size)
        x3, y3 = 0 + space, title_height / width - space
        cr0.move_to(x3, y3)
        cr0.show_text(person.birthday.strftime('%d.%m.%Y'))
        cr0.stroke()

        surface_pdf.finish()

