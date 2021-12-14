import time

from datetime import datetime, timedelta

from model.sf_flatlib import FlatlibBuilder


def iterate_borders(borders_file_name, formula_foo):
    builder = FlatlibBuilder()
    with open(borders_file_name) as f:
        prev_day = None
        for line in f:
            cur_day = datetime.strptime(line.strip(), '%Y-%m-%d %H:%M')
            if prev_day is None:
                prev_day = cur_day

            formula = builder.build_formula(cur_day)
            formula_foo(formula, prev_day, cur_day)
            prev_day = cur_day + timedelta(minutes=1)


def make_borders(out_file, from_date='1900/01/01', to_date='2030/12/31'):
    builder = FlatlibBuilder()
    cur_day = datetime.strptime(from_date, '%Y/%m/%d')
    formula = builder.build_formula(cur_day)
    last_formula_id = formula.get_id()
    with open(out_file, 'w') as f:
        f.write(cur_day.strftime("%Y-%m-%d %H:%M"))
        f.write('\n')
        f.flush()
        __iterate(f, last_formula_id, cur_day, to_date, step_in_minutes=1440)


def __iterate(f, last_formula_id, last_formula_date, to_date, step_in_minutes):
    builder = FlatlibBuilder()
    while last_formula_date.strftime('%Y/%m/%d') != to_date:
        cur_date = last_formula_date + timedelta(minutes=step_in_minutes)
        formula = builder.build_formula(cur_date)
        formula_id = formula.get_id()

        if formula_id == last_formula_id:
            last_formula_id = formula_id
            last_formula_date = cur_date
            step_in_minutes = 1440
        else:
            if step_in_minutes == 1:
                f.write(last_formula_date.strftime("%Y-%m-%d %H:%M"))
                f.write('\n')
                f.flush()

                last_formula_id = formula_id
                last_formula_date = cur_date
                step_in_minutes = 1440
            else:
                step_in_minutes //= 2


if __name__ == '__main__':
    start_time = time.time()
    # Выполнено за 17782 сек (296.4 мин)
    make_borders('/Users/mosigo/Yandex.Disk.localized/Documents/PycharmProjects/Astrogor/borders.csv',
                 from_date='1300/01/01', to_date='2999/12/31')
    final_time_spend = time.time() - start_time
    print(f'Выполнено за {round(final_time_spend)} сек ({round(final_time_spend / 60.0, 1)} мин)')
