import cairo
from flatlib import const

from borders import iterate_borders
from model.sf import SoulFormulaWithBorders
from view.sf_cairo import SimpleFormulaDrawer
from view.sf_layout import DefaultLayoutMaker
from view.sf_printer import PDFPrinter


class FormulaStorage:

    def __init__(self, search_function) -> None:
        self.formulas = []
        self.search_function = search_function

    def process_formula(self, formula, from_day, to_day):
        if self.search_function(formula, from_day, to_day):
            self.formulas.append(SoulFormulaWithBorders(formula, from_day, to_day))


def all_in_center(formula, from_day, to_day):
    return len(formula.center_set) == 10


def mercury_in_exclusion_zone(formula, from_day, to_day):
    to_mercury_links = formula.reverse_links.get(const.MERCURY, [])
    if const.MERCURY in formula.retro and \
            const.MERCURY in formula.center_set and \
            len(to_mercury_links) == 1 and \
            to_mercury_links[0] == const.MERCURY:  # Меркурий должен ссылаться на себя
        print(from_day, '–', to_day)
        print(formula)
        return True
    return False


def mars_in_exclusion_zone(formula, from_day, to_day):
    to_mars_links = formula.reverse_links.get(const.MARS, [])
    if const.MARS in formula.retro and \
            const.MARS in formula.center_set and \
            len(to_mars_links) == 1 and \
            to_mars_links[0] == const.MARS:  # Марс должен ссылаться на себя
        print(from_day, '–', to_day)
        print(formula)
        return True
    return False


class ExclusionZoneFinder:

    def __init__(self, planet) -> None:
        self.planet = planet

    def search_function(self, formula, from_day, to_day):
        to_planet_links = formula.reverse_links.get(self.planet, [])
        if self.planet in formula.retro and \
                self.planet in formula.center_set and \
                len(to_planet_links) == 1 and \
                to_planet_links[0] == self.planet:  # планета должна ссылаться на себя
            return True
        return False


class HolidaysZoneFinder:

    def __init__(self, planet) -> None:
        self.planet = planet

    def search_function(self, formula, from_day, to_day):
        to_planet_links = formula.reverse_links.get(self.planet, [])
        if self.planet not in formula.retro and \
                self.planet in formula.center_set and \
                len(to_planet_links) == 1 and \
                to_planet_links[0] == self.planet:  # планета должна ссылаться на себя
            return True
        return False


class PlanetInOrbitFinder:

    def __init__(self, planet, orbit_num) -> None:
        self.planet = planet
        self.orbit_num = orbit_num

    def search_function(self, formula, from_day, to_day):
        return self.planet in formula.orbits.get(self.orbit_num, [])


def all_in_center_circle(formula, from_day, to_day):
    if len(formula.center) == 1 and len(formula.center_set) == 10:
        # print(from_day, '–', to_day)
        # print(formula)
        return True
    return False


def all_in_first_orbit(formula, from_day, to_day):
    if len(formula.orbits.get(1, [])) + len(formula.center_set) == 10 \
            and len(formula.center_set) <= 3:
        print(from_day, '–', to_day)
        print(formula)
        return True
    return False


def max_in_second_orbit(formula, from_day, to_day):
    if len(formula.orbits.get(2, [])) >= 6:
        print(from_day, '–', to_day)
        print(formula)
        return True
    return False


def max_in_third_orbit(formula, from_day, to_day):
    if len(formula.orbits.get(3, [])) >= 5:
        print(from_day, '–', to_day)
        print(formula)
        return True
    return False


def max_in_fourth_orbit(formula, from_day, to_day):
    if len(formula.orbits.get(4, [])) >= 5:
        print(from_day, '–', to_day)
        print(formula)
        return True
    return False


def max_in_fifth_orbit(formula, from_day, to_day):
    if len(formula.orbits.get(5, [])) >= 5:
        print(from_day, '–', to_day)
        print(formula)
        return True
    return False


def max_in_sixth_orbit(formula, from_day, to_day):
    if len(formula.orbits.get(6, [])) >= 4:
        print(from_day, '–', to_day)
        print(formula)
        return True
    return False


def max_in_seventh_orbit(formula, from_day, to_day):
    if len(formula.orbits.get(7, [])) >= 2:
        print(from_day, '–', to_day)
        print(formula)
        return True
    return False


def max_personal_score(formula, from_day, to_day):
    planets = [const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS]
    score = 0
    for planet in planets:
        score += formula.planet_power[planet]
    if score >= 29:
        print(formula)
        return True
    return False


def do_search(out_path, title, search_foo):
    print(f'Запускаю поиск «{title}», результаты будут в {out_path}.')

    storage = FormulaStorage(search_foo)

    # iterate_borders('data/borders_1900_2100.csv', storage.process_formula)
    # full_title = f'{title}, с 1900 по 2100 гг'

    iterate_borders('data/borders_1300_2999.csv', storage.process_formula)
    full_title = f'{title}, с 1300 по 2999 гг'

    printer = PDFPrinter(out_path, title=full_title, date_as_interval=True)

    for formula in storage.formulas:
        printer.formulas.append(formula)

    printer.print_formulas()


if __name__ == '__main__':

    # do_search('pic/out_mercury_in_exclusion_zone.pdf', 'Меркурий в зоне отчуждения', mercury_in_exclusion_zone)
    # do_search('pic/out_mars_in_exclusion_zone.pdf', 'Марс в зоне отчуждения', mars_in_exclusion_zone)
    # do_search('pic/out_all_in_center.pdf', 'Все планеты в центре', all_in_center)
    do_search('pic/out_all_in_center_circle.pdf', 'Все планеты в центре и образуют цикл', all_in_center_circle)
    # do_search('pic/out_orbit1_max.pdf', 'Только первая орбита, в центре <= 3 планет', all_in_first_orbit)
    # do_search('pic/out_orbit2_max.pdf', 'На второй орбите 6 и более планет', max_in_second_orbit)
    # do_search('pic/out_orbit3_max.pdf', 'На третьей орбите 5 и более планет', max_in_third_orbit)
    # do_search('pic/out_orbit4_max.pdf', 'На четвёртой орбите 5 и более планет', max_in_fourth_orbit)
    # do_search('pic/out_orbit5_max.pdf', 'На пятой орбите 5 и более планет', max_in_fifth_orbit)
    # do_search('pic/out_orbit6_max.pdf', 'На шестой орбите 4 и более планет', max_in_sixth_orbit)
    # do_search('pic/out_orbit7_max.pdf', 'На седьмой орбите 2 и более планет', max_in_seventh_orbit)

    # do_search('pic/personal_score_max.pdf', 'Cумма баллов по личным планетам >= 29', max_personal_score)
