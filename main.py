# import de406
from flatlib import const
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
# from jplephem import Ephemeris
# from skyfield.api import load
# from astropy import units as u

from datetime import datetime, timedelta

from borders import iterate_borders
from chess_players import load_chess_players_men, load_chess_players_women
from model.sf_flatlib import FlatlibBuilder


def iterate_dates(chart_foo, from_date='1900/01/01', to_date='2030/12/31', step_in_hours=12):
    cur_day = datetime.strptime(from_date, '%Y/%m/%d')
    result = set()
    builder = FlatlibBuilder()
    while cur_day.strftime('%Y/%m/%d') != to_date:
        formula = builder.build_formula(cur_day)
        formula_id = formula.get_id()
        if chart_foo(formula) and formula_id not in result:
            result.add(formula_id)
            print(f'Нашёл!!! => {cur_day.strftime("%Y/%m/%d")}')
            print(formula)
        cur_day += timedelta(hours=step_in_hours)


def print_formula(from_day, to_day):
    builder = FlatlibBuilder()
    formula = builder.build_formula(from_day)
    print(from_day.strftime("%Y-%m-%d %H:%M"), '–', to_day.strftime("%Y-%m-%d %H:%M"))
    print(f'id={formula.get_id()}')
    print(formula)


class FormulaHistogram:

    def __init__(self) -> None:
        self.formula_to_dates = {}

    def foo(self, formula, from_day, to_day):
        formula_id = formula.get_id()
        if self.formula_to_dates.get(formula_id) is None:
            self.formula_to_dates[formula_id] = []
        self.formula_to_dates[formula_id].append((from_day, to_day))

    def print_result(self):
        results = []
        for formula_id, formula_dates in self.formula_to_dates.items():
            minutes_cnt = 0
            for fr, to in formula_dates:
                minutes_cnt += (to - fr).total_seconds() / 60.0
            results.append((minutes_cnt, formula_dates))
        results.sort(key=lambda x: x[0])
        for results_i in results[:100] + results[-10:]:
            minutes, dates = results_i
            print(f'Встретилось {minutes} мин:')
            for date_from, date_to in dates:
                print_formula(date_from, date_to)


def extract_patterns(dates):
    builder = FlatlibBuilder()
    pattern_to_cnt = {}
    for dt in dates:
        formula = builder.build_formula(dt)
        for pattern in formula.get_patterns():
            cnt = pattern_to_cnt.get(pattern, 0)
            pattern_to_cnt[pattern] = cnt + 1
    return pattern_to_cnt


class AllPeoplePatternExtractor:

    def __init__(self, min_day, max_day) -> None:
        self.max_day = max_day
        self.min_day = min_day
        self.pattern_to_cnt = {}
        self.formulas_cnt = 0

    def extract_pattern(self, formula, from_day, to_day):
        if from_day >= self.min_day and to_day <= self.max_day:
            self.formulas_cnt += 1
            for pattern in formula.get_patterns():
                cnt = self.pattern_to_cnt.get(pattern, 0)
                self.pattern_to_cnt[pattern] = cnt + 1

    def get_percent(self, pattern):
        return self.pattern_to_cnt.get(pattern, 0) * 100 // self.formulas_cnt


def iterate_specialization(birthdays):
    builder = FlatlibBuilder()

    min_birthday = min(birthdays)
    max_birthday = max(birthdays)
    print(f'Дни рождения распределены от {min_birthday.strftime("%Y/%m/%d")} до {max_birthday.strftime("%Y/%m/%d")}.')
    pattern_extractor = AllPeoplePatternExtractor(min_birthday, max_birthday)
    iterate_borders('data/borders_1900_2100.csv', pattern_extractor.extract_pattern)
    print(f'Извлечены паттерны из всех возможных формул за данный период, '
          f'их получилось {len(pattern_extractor.pattern_to_cnt)}, '
          f'всего рассмотрено формул {pattern_extractor.formulas_cnt}.')

    patterns = extract_patterns(birthdays)
    all_cnt = len(birthdays)
    print(f'Извлечены паттерны конкретных людей, их получилось {len(patterns)}, рассмотрено формул {all_cnt}.')
    patterns_list = [a for a in patterns.items()]
    # patterns_list.sort(key=lambda a: abs(a[1] * 100 // all_cnt - pattern_extractor.get_percent(a[0])), reverse=True)
    patterns_list.sort(key=lambda a: a[1] * 100 // all_cnt - pattern_extractor.get_percent(a[0]), reverse=True)  # паттерны, которые выделяют нашу группу на фоне всех
    # patterns_list.sort(key=lambda a: a[1] * (-100) // all_cnt + pattern_extractor.get_percent(a[0]), reverse=True)  # паттерны, которые наоборот не встречаются у нашей группы
    i = 1
    for pattern, cnt in patterns_list[:30]:
        specialization_percent = cnt * 100 // all_cnt
        general_percent = pattern_extractor.get_percent(pattern)
        print(f'{i}) {pattern} {specialization_percent}% / {general_percent}% ({specialization_percent - general_percent}%)')
        i += 1

    best_patterns_cnt = 10
    best_patterns = [a[0] for a in patterns_list[:best_patterns_cnt]]
    max_cnt = 0
    for birthday in birthdays:
        formula = builder.build_formula(birthday + timedelta(hours=12, minutes=2))
        formula_patterns = set(formula.get_patterns())
        patterns_from_best = []
        for pattern in best_patterns:
            if pattern in formula_patterns:
                patterns_from_best.append(pattern)
        if max_cnt < len(patterns_from_best):
            max_cnt = len(patterns_from_best)

    print(f'Пример формул, в которых встречается {max_cnt} паттернов из топ-{best_patterns_cnt}:')
    for birthday in birthdays:
        formula = builder.build_formula(birthday + timedelta(hours=12, minutes=2))
        formula_patterns = set(formula.get_patterns())
        patterns_from_best = []
        for pattern in best_patterns:
            if pattern in formula_patterns:
                patterns_from_best.append(pattern)
        if len(patterns_from_best) == max_cnt:
            print(birthday.strftime('%Y/%m/%d'))
            print(formula)
            print(f'Лучшие паттерны: {patterns_from_best}')
            print()


if __name__ == '__main__':
    # eph = Ephemeris(de406)
    # x, y, z = eph.position('mars', 2444391.5)  # 1980.06.01
    # print(x, y, z)

    ####################

    # # Create a timescale and ask the current time.
    # ts = load.timescale()
    # t = ts.now()
    #
    # # Load the JPL ephemeris DE421 (covers 1900-2050).
    # planets = load('de406.bsp')
    # earth, mars, sun = planets['earth'], planets['mars'], planets['sun']
    #
    # # What's the position of Mars, viewed from Earth?
    # astrometric = sun.at(t).observe(mars)
    # ra, dec, distance = astrometric.radec()
    #
    # print(ra)
    # print(dec)
    # print(distance)
    #
    # xyz = astrometric.position.to(u.au)
    # print(xyz, type(xyz))
    #
    # print(xyz[0])

    ##########

    # iterate_dates(mercury_in_exclusion_zone)
    # iterate_dates(all_in_center)
    # iterate_dates(all_in_center, from_date='2496/01/01', to_date='2500/12/31', step_in_hours=1)

    pass

    # iterate_specialization(load_chess_players_women() + load_chess_players_men())


    # setPath('/Users/mosigo/Yandex.Disk.localized/Documents/PycharmProjects/Astrogor/de406.bsp')

    # hist = FormulaHistogram()
    # iterate_borders('data/borders_1900_2100.csv', hist.foo)
    # hist.print_result()

    # print_formula(datetime.strptime('1356-10-25 17:23', '%Y-%m-%d %H:%M'),
    #               datetime.strptime('1356-10-27 21:52', '%Y-%m-%d %H:%M'))

    # print(chart.get(const.SUN))
    # print(chart.get(const.MOON))
    # print(chart.get(const.MERCURY))
    # print(chart.get(const.VENUS))
    # print(chart.get(const.MARS))
    # print(chart.get(const.JUPITER))
    # print(chart.get(const.SATURN))
    # print(chart.get(const.URANUS))
    # print(chart.get(const.NEPTUNE))
    # print(chart.get(const.PLUTO))
    # print()
    #
    # print(chart.get(const.HOUSE1))
    # print(chart.get(const.HOUSE2))
    # print(chart.get(const.HOUSE3))

    # print(chart.get(const.PARS_FORTUNA))
    # print(chart.get(const.CHIRON))
