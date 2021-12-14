from datetime import datetime

from model.sf import SoulFormulaWithBorders
from model.sf_flatlib import FlatlibBuilder
from view.sf_printer import PDFPrinter

if __name__ == '__main__':
    builder = FlatlibBuilder()
    printer = PDFPrinter('pic/out.pdf', rows=2, cols=2)
    # printer.title = 'Дни рождения Тани'
    # for formula_date in ['2017-10-14 12:00', '2018-10-14 12:00', '2019-10-14 12:00',
    #                      '2020-10-14 12:00', '2021-10-14 12:00', '2022-10-14 12:00']:

    printer.title = 'Дни Рождения Сириус.Курсов'
    for formula_date in ['2019-03-15 12:00',
                         '2020-03-15 12:00', '2021-03-15 12:00', '2022-03-15 12:00',
                         '1356-10-25 17:22', '2496-07-18 01:53']:

    # printer.title = 'Алёна и Денис'
    # for formula_date in ['1984-06-15 12:00', '1983-12-11 12:00']:

    # printer.title = 'Богдан Олегович'
    # for formula_date in ['1993-01-30 12:00']:

    # for formula_date in ['1753-04-18 12:02', '1986-07-14 12:02', '2016-12-30 12:02', '1901-06-07 12:02',
    #                      '1939-01-28 12:02', '1821-08-13 12:02', '1956-05-20 12:02', '1987-12-04 12:02',
    #                      '1987-12-24 12:02', '1987-01-10 12:02', '1992-03-19 12:02', '1990-12-13 12:02',
    #                      '1993-12-29 12:02', '1996-12-17 12:02', '1993-09-08 12:02']:
    # for formula_date in ['1821-08-13 12:02', '1987-01-10 12:02', '1992-03-19 12:02',
    #                      '1993-12-29 12:02', '1996-12-17 12:02', '1993-09-08 12:02',
    #                      '1753-04-18 12:02', '1986-07-14 12:02', '2016-12-30 12:02']:
        dt = datetime.strptime(formula_date, '%Y-%m-%d %H:%M')
        formula = builder.build_formula(dt)
        printer.formulas.append(SoulFormulaWithBorders(formula, dt, dt))

    printer.print_formulas()
