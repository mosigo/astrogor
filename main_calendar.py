from datetime import datetime, timedelta

from model.sf import SoulFormulaWithBorders
from model.sf_flatlib import FlatlibBuilder
from view.sf_printer import PDFPrinter

if __name__ == '__main__':
    builder = FlatlibBuilder()
    printer = PDFPrinter('pic/calendar.pdf', rows=3, cols=3)
    printer.title = 'Календарь'

    dt = datetime.strptime('2021-11-04 12:00', '%Y-%m-%d %H:%M')
    dt_end = datetime.strptime('2022-01-10 12:00', '%Y-%m-%d %H:%M')
    prev_id = ''
    while dt <= dt_end:
        print(dt)

        formula = builder.build_formula(dt)
        id = formula.get_id()
        if id != prev_id:
            printer.formulas.append(SoulFormulaWithBorders(formula, dt, dt))

        prev_id = id
        dt += timedelta(days=1)

    printer.print_formulas()
