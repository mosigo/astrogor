import math
import time
from abc import abstractmethod
from datetime import datetime

import cairo
import pytz
import qrcode
from flatlib import const

from model.sf import SoulFormulaWithBorders, Cosmogram, NumericInfo
from view.sf_cairo import SimpleFormulaDrawer, DFormula, CirclePosition, OrbitPosition, DrawProfile
from view.sf_cosmogram import DefaultCosmogramDrawer
from view.sf_geometry import rotate_point
from view.sf_layout import DefaultLayoutMaker, RectangleFormulaCutter, CircleFormulaCutter
from view.sf_numeric import NumericDrawer


class SoulFormulaPrinter:
    @abstractmethod
    def print_formulas(self):
        pass


class PDFPrinter(SoulFormulaPrinter):
    def __init__(self, out_path, title='', rows=2, cols=2,
                 width=210, height=297, border_offset=5, cell_offset=5,
                 title_height=10, formula_title_height=5, date_as_interval=False,
                 draw_profile=DrawProfile.DEFAULT) -> None:
        self.date_as_interval = date_as_interval
        self.formula_title_height = formula_title_height
        self.title_height = title_height
        self.cell_offset = cell_offset
        self.border_offset = border_offset
        self.height = height
        self.width = width
        self.out_path = out_path
        self.title = title
        self.rows = rows
        self.cols = cols
        self.formulas = []
        self.draw_profile = draw_profile

    def _add_text(self, cr0: cairo.Context, font_size, x, y, max_width, text):
        cr0.move_to(x, y)
        cr0.set_font_size(font_size)
        te = cr0.text_extents(text)
        while te.width > max_width:
            font_size *= 0.99
            cr0.set_font_size(font_size)
            te = cr0.text_extents(text)
        cr0.show_text(text)
        cr0.stroke()

    def __print_title(self, cr, title_x, title_y, cur_page, all_page):

        cr.set_source_rgb(0, 0, 0)
        title_text = f'{self.title} (стр {cur_page} из {all_page})'
        cr.select_font_face(self.draw_profile.font_header, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_source_rgb(0, 0, 0)
        self._add_text(cr, 0.04, title_x, title_y, 0.9, title_text)

    def print_formulas(self):
        formula_width = int((self.width - 2 * self.border_offset - (self.rows - 1) * self.cell_offset) / self.rows)
        formula_height = int((self.height - 2 * self.border_offset - self.cols * (
                self.cell_offset + self.formula_title_height) - self.title_height) / self.cols)

        layout_maker = DefaultLayoutMaker(RectangleFormulaCutter(formula_width, formula_height))
        drawer = SimpleFormulaDrawer()

        surface_pdf = cairo.PDFSurface(self.out_path, self.width, self.height)
        surface_pdf.set_device_offset(self.border_offset, self.border_offset)
        cr0 = cairo.Context(surface_pdf)
        cr0.scale(self.width, self.width)  # TODO: нужно ли тут учитывать поля документа, которые выставлены глобально?

        pages_cnt = math.ceil(len(self.formulas) / (self.rows * self.cols))
        page_num = 1

        title_x = 0
        title_y = self.title_height
        title_x = title_x / (self.width - 2 * self.border_offset)
        title_y = title_y / (self.height - 2 * self.border_offset)
        self.__print_title(cr0, title_x, title_y, page_num, pages_cnt)
        f_title_y = self.title_height + self.cell_offset + self.formula_title_height

        x1 = 0
        y1 = f_title_y
        formulas_cnt = 0
        for formula in self.formulas:
            cr0.select_font_face(self.draw_profile.font_text, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            xt, yt = cr0.device_to_user(x1, y1 - 1)
            # cr0.set_font_size(0.01)
            cr0.set_source_rgb(0, 0, 0)
            # cr0.move_to(xt, yt)
            label = formula.formula.dt.strftime('%Y-%m-%d %H:%M')
            if self.date_as_interval:
                label = formula.from_dt.strftime('%Y-%m-%d %H:%M')
                label += ' — '
                label += formula.to_dt.strftime('%Y-%m-%d %H:%M')
            max_width, _ = cr0.device_to_user_distance(formula_width, 0)
            self._add_text(cr0, 0.03, xt, yt, max_width, label)
            # cr0.show_text(label)
            # cr0.stroke()

            cr = cairo.Context(surface_pdf.create_for_rectangle(x1, y1, formula_width, formula_height))
            cr.scale(formula_width, formula_width)
            start_time = time.time()
            print(f'Начинаю рендеринг формулы {formula.formula}...')
            d_formula = layout_maker.make_layout(formula.formula)
            final_time_spend = time.time() - start_time
            print(f'Рендеринг завершён за {round(final_time_spend)} сек ({round(final_time_spend / 60.0, 1)} мин)')
            drawer.draw_formula(d_formula, cr)

            xf, yf = cr0.device_to_user(x1, y1)
            wf, hf = cr0.device_to_user_distance(formula_width, formula_height)
            cr0.set_line_width(0.001)
            cr0.rectangle(xf, yf, wf, hf)
            cr0.stroke()

            formulas_cnt += 1

            if x1 < self.width - 2 * self.border_offset - formula_width - self.cell_offset:
                x1 += formula_width + self.cell_offset
            else:
                x1 = 0
                y1 += formula_height + self.cell_offset + self.formula_title_height

            if formulas_cnt % (self.rows * self.cols) == 0 and page_num < pages_cnt:
                x1 = 0
                y1 = f_title_y
                surface_pdf.show_page()
                page_num += 1
                self.__print_title(cr0, title_x, title_y, page_num, pages_cnt)

        surface_pdf.finish()


class TwoCirclePrinter:

    def __init__(self, width=297, height=210, border_offset=5, inner_offset=5,
                 title_height=10, subtitle_height=10, add_info_radius=15, add_info_overlap=4,
                 draw_profile=DrawProfile.DEFAULT) -> None:
        self.add_info_overlap = add_info_overlap
        self.add_info_radius = add_info_radius
        self.subtitle_height = subtitle_height
        self.title_height = title_height
        self.inner_offset = inner_offset
        self.border_offset = border_offset
        self.height = height - 2 * border_offset
        self.width = width - 2 * border_offset

        self.draw_profile = draw_profile

        self.circle_radius = int((self.width - self.inner_offset) / 4)
        space = 0.85 * (self.height - self.title_height - self.subtitle_height - 2 * self.circle_radius) / 2
        self.x1, self.y1 = self.circle_radius, self.circle_radius + self.title_height + self.subtitle_height + space
        self.x2, self.y2 = self.circle_radius * 3 + self.inner_offset, self.y1

        alpha = math.acos((self.circle_radius - self.add_info_radius) / (self.circle_radius + self.add_info_radius))
        add_info_x2, add_info_y2 = self.x2, self.y2 - self.circle_radius - self.add_info_radius
        add_info_x2, add_info_y2 = rotate_point(self.x2, self.y2, add_info_x2, add_info_y2, math.pi / 2 - alpha)
        self.add_info_x2 = add_info_x2 - self.add_info_overlap * math.cos(alpha)
        self.add_info_y2 = add_info_y2 + self.add_info_overlap * math.sin(alpha)
        self.add_info_alpha = \
            2 * math.asin(self.add_info_radius / (self.circle_radius + self.add_info_radius - self.add_info_overlap)) \
            - 0.5 * math.pi / 180
        add_info_x1, add_info_y1 = self.x1, self.y1 + self.circle_radius + self.add_info_radius
        add_info_x1, add_info_y1 = rotate_point(self.x1, self.y1, add_info_x1, add_info_y1, math.pi / 2 - alpha)
        self.add_info_x1 = add_info_x1 + self.add_info_overlap * math.cos(alpha)
        self.add_info_y1 = add_info_y1 - self.add_info_overlap * math.sin(alpha)

        self.title_x, self.title_y = 0, self.title_height
        self.subtitle_x, self.subtitle_y = 0, self.title_height + self.subtitle_height

    def draw_add_info(self, idx: int, cr: cairo.Context, draw_function, place='right', shape='circle'):
        r, _ = cr.device_to_user_distance(self.add_info_radius, 0)
        if place == 'right':
            x, y = rotate_point(self.x2, self.y2, self.add_info_x2, self.add_info_y2, -self.add_info_alpha * idx)
        else:
            x, y = rotate_point(self.x1, self.y1, self.add_info_x1, self.add_info_y1, -self.add_info_alpha * idx)
        x, y = cr.device_to_user(x, y)

        if shape == 'rectangle':
            corner_size = 0.5 * r
            x1, y1 = x - r, y - r * 0.8
            x2, y2 = x + r, y + r * 0.8
            cr.set_source_rgb(1, 1, 1)
            cr.move_to(x1 + corner_size, y1)
            cr.line_to(x2 - corner_size, y1)
            cr.arc(x2 - corner_size, y1 + corner_size, corner_size, -math.pi / 2, 0)
            cr.line_to(x2, y2 - corner_size)
            cr.arc(x2 - corner_size, y2 - corner_size, corner_size, 0, math.pi / 2)
            cr.line_to(x1 + corner_size, y2)
            cr.arc(x1 + corner_size, y2 - corner_size, corner_size, math.pi / 2, math.pi)
            cr.line_to(x1, y1 + corner_size)
            cr.arc(x1 + corner_size, y1 + corner_size, corner_size, math.pi, 3 * math.pi / 2)
            cr.fill()

            cr.set_source_rgb(0, 0, 0)
            cr.move_to(x1 + corner_size, y1)
            cr.line_to(x2 - corner_size, y1)
            cr.arc(x2 - corner_size, y1 + corner_size, corner_size, -math.pi / 2, 0)
            cr.line_to(x2, y2 - corner_size)
            cr.arc(x2 - corner_size, y2 - corner_size, corner_size, 0, math.pi / 2)
            cr.line_to(x1 + corner_size, y2)
            cr.arc(x1 + corner_size, y2 - corner_size, corner_size, math.pi / 2, math.pi)
            cr.line_to(x1, y1 + corner_size)
            cr.arc(x1 + corner_size, y1 + corner_size, corner_size, math.pi, 3 * math.pi / 2)
            cr.stroke()

        else:
            cr.set_source_rgb(1, 1, 1)
            cr.arc(x, y, r, 0, 2 * math.pi)
            cr.fill()
            cr.set_source_rgb(0, 0, 0)
            cr.arc(x, y, r, 0, 2 * math.pi)
            cr.stroke()

        cr.save()
        cr.translate(x - r, y - r)
        cr.scale(2 * r, 2 * r)
        draw_function(cr)
        cr.restore()

    def print_info(self, out_path, fio: str, city: str,
                   formula: SoulFormulaWithBorders, cosmogram: Cosmogram, numeric_info: NumericInfo):
        surface_pdf = cairo.PDFSurface(
            out_path, self.width + 2 * self.border_offset, self.height + 2 * self.border_offset)
        surface_pdf.set_device_offset(self.border_offset, self.border_offset)
        cr0 = cairo.Context(surface_pdf)
        cr0.scale(self.width, self.width)

        x, y = cr0.device_to_user(self.title_x, self.title_y)
        cr0.move_to(x, y)
        cr0.set_font_size(0.035)
        cr0.select_font_face(self.draw_profile.font_header, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr0.set_source_rgb(0, 0, 0)
        cr0.show_text(f'{fio.upper()}')
        cr0.select_font_face(self.draw_profile.font_text, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        x, y = cr0.device_to_user(self.subtitle_x, self.subtitle_y)
        cr0.move_to(x, y)
        cr0.set_font_size(0.027)
        user_dates = formula.formula.dt.strftime("%d.%m.%Y %H:%M")
        if cosmogram.death_dt:
            user_dates += ' — ' + cosmogram.death_dt.strftime("%d.%m.%Y %H:%M")
        cr0.show_text(user_dates)
        x, y = cr0.device_to_user(self.subtitle_x, self.subtitle_y + self.subtitle_height * 0.7)
        cr0.move_to(x, y)
        cr0.set_font_size(0.013)
        cr0.show_text(city)
        cr0.stroke()

        # self.__draw_numeric_data(cr0, numeric_info)

        cr = cairo.Context(surface_pdf.create_for_rectangle(
            self.x1 - self.circle_radius, self.y1 - self.circle_radius, self.circle_radius * 2, self.circle_radius * 2))
        cr.scale(self.circle_radius * 2, self.circle_radius * 2)

        drawer = DefaultCosmogramDrawer()
        drawer.draw_cosmogram(cosmogram, cr)

        layout_maker = DefaultLayoutMaker(CircleFormulaCutter(self.circle_radius))
        drawer = SimpleFormulaDrawer()

        cr = cairo.Context(surface_pdf.create_for_rectangle(
            self.x2 - self.circle_radius, self.y2 - self.circle_radius, self.circle_radius * 2, self.circle_radius * 2))
        cr.scale(self.circle_radius * 2, self.circle_radius * 2)

        d_formula = layout_maker.make_layout(formula.formula)
        cr.arc(0.5, 0.5, 0.5, 0, 2 * math.pi)
        cr.clip()
        drawer.draw_formula(d_formula, cr)
        cr.reset_clip()

        cr0.set_line_width(0.0002)
        xf, yf = cr0.device_to_user(self.x2, self.y2)
        wf, _ = cr0.device_to_user_distance(self.circle_radius, 0)
        cr0.arc(xf, yf, wf, 0, 2 * math.pi)
        cr0.stroke()

        def foo(cr: cairo.Context):
            drawer.draw_formula_duration(formula, cr)

        def foo2(cr: cairo.Context):
            drawer.draw_power_points(formula.formula, cr)

        self.draw_add_info(0, cr0, foo2, shape='rectangle')
        self.draw_add_info(1, cr0, foo, shape='rectangle')

        def aspect(aspect: int):
            def foo_res(cr: cairo.Context):
                drawer = DefaultCosmogramDrawer()
                drawer.draw_aspect(cosmogram, cr, aspect)

            return foo_res

        i = 0
        for a in cosmogram.aspects:
            self.draw_add_info(i, cr0, aspect(a), place='left')
            i += 1

        surface_pdf.finish()

    def __draw_numeric_data(self, cr0: cairo.Context, numeric_info: NumericInfo):
        numeric_drawer = NumericDrawer()
        numeric_width = 12
        x, y = cr0.device_to_user(self.width - 2 * numeric_width, 0)
        r, _ = cr0.device_to_user_distance(numeric_width, 0)
        cr0.save()
        cr0.translate(x, y)
        cr0.scale(r, r)
        numeric_drawer.draw_soul_number(numeric_info.soul_number, cr0)
        cr0.restore()
        cr0.stroke()

        x, y = cr0.device_to_user(self.width - numeric_width, 0)
        r, _ = cr0.device_to_user_distance(numeric_width, 0)
        cr0.save()
        cr0.translate(x, y)
        cr0.scale(r, r)
        numeric_drawer.draw_fate_number(numeric_info.fate_number, cr0)
        cr0.restore()
        cr0.stroke()


class OneCirclePrinter:

    # def __init__(self, width=210, height=297, border_offset=5,
    #              title_height=10, subtitle_height=10, add_info_radius=18, add_info_overlap=2.5, qr_width=14) -> None:
    def __init__(self, width=210, height=297, border_offset=5,
                 title_height=8, subtitle_height=4, text_offset=2,
                 add_info_radius=18, add_info_overlap=2.5, qr_width=25, age_units='days') -> None:
        self.age_units = age_units
        self.add_info_overlap = add_info_overlap
        self.add_info_radius = add_info_radius
        self.subtitle_height = subtitle_height
        self.title_height = title_height
        self.text_offset = text_offset
        self.border_offset = border_offset
        self.height = height - 2 * border_offset
        self.width = width - 2 * border_offset
        self.qr_width = qr_width

        self.circle_radius = int(self.width / 2)
        space = self.add_info_radius * 1.7
        self.x, self.y = self.circle_radius, self.circle_radius + \
                         self.title_height + self.subtitle_height * 3 + self.text_offset * 3 + space

        alpha = math.acos((self.circle_radius - self.add_info_radius) / (self.circle_radius + self.add_info_radius))
        add_info_x2, add_info_y2 = self.x, self.y - self.circle_radius - self.add_info_radius
        add_info_x2, add_info_y2 = rotate_point(self.x, self.y, add_info_x2, add_info_y2, math.pi / 2 - alpha)
        self.add_info_x2 = add_info_x2 - self.add_info_overlap * math.cos(alpha)
        self.add_info_y2 = add_info_y2 + self.add_info_overlap * math.sin(alpha)
        self.add_info_alpha = \
            2 * math.asin(self.add_info_radius / (self.circle_radius + self.add_info_radius - self.add_info_overlap)) \
            - 0.5 * math.pi / 180
        add_info_x1, add_info_y1 = self.x, self.y + self.circle_radius + self.add_info_radius
        add_info_x1, add_info_y1 = rotate_point(self.x, self.y, add_info_x1, add_info_y1, math.pi / 2 - alpha)
        self.add_info_x1 = add_info_x1 + self.add_info_overlap * math.cos(alpha)
        self.add_info_y1 = add_info_y1 - self.add_info_overlap * math.sin(alpha)

        self.title_x, self.title_y = 0, self.title_height
        self.subtitle1_x, self.subtitle1_y = 0, self.title_y + self.text_offset + self.subtitle_height
        self.subtitle2_x, self.subtitle2_y = 0, self.subtitle1_y + self.text_offset * 2 + self.subtitle_height
        self.subtitle3_x, self.subtitle3_y = 0, self.subtitle2_y + self.text_offset + self.subtitle_height
        self.subtitle4_x, self.subtitle4_y = 0, self.subtitle3_y + self.text_offset * 2 + self.subtitle_height

    def draw_add_info(self, idx: int, cr: cairo.Context, draw_function, place='right', shape='circle'):
        r, _ = cr.device_to_user_distance(self.add_info_radius, 0)
        if place == 'right':
            x, y = rotate_point(self.x, self.y, self.add_info_x2, self.add_info_y2, -self.add_info_alpha * idx)
        else:
            x, y = rotate_point(self.x, self.y, self.add_info_x1, self.add_info_y1, -self.add_info_alpha * idx)
        x, y = cr.device_to_user(x, y)

        cr.set_line_width(0.0005)

        if shape == 'rectangle':
            corner_size = 0.5 * r
            x1, y1 = x - r, y - r * 0.8
            x2, y2 = x + r, y + r * 0.8
            cr.set_source_rgb(1, 1, 1)
            cr.move_to(x1 + corner_size, y1)
            cr.line_to(x2 - corner_size, y1)
            cr.arc(x2 - corner_size, y1 + corner_size, corner_size, -math.pi / 2, 0)
            cr.line_to(x2, y2 - corner_size)
            cr.arc(x2 - corner_size, y2 - corner_size, corner_size, 0, math.pi / 2)
            cr.line_to(x1 + corner_size, y2)
            cr.arc(x1 + corner_size, y2 - corner_size, corner_size, math.pi / 2, math.pi)
            cr.line_to(x1, y1 + corner_size)
            cr.arc(x1 + corner_size, y1 + corner_size, corner_size, math.pi, 3 * math.pi / 2)
            cr.fill()

            cr.set_source_rgb(0, 0, 0)
            cr.move_to(x1 + corner_size, y1)
            cr.line_to(x2 - corner_size, y1)
            cr.arc(x2 - corner_size, y1 + corner_size, corner_size, -math.pi / 2, 0)
            cr.line_to(x2, y2 - corner_size)
            cr.arc(x2 - corner_size, y2 - corner_size, corner_size, 0, math.pi / 2)
            cr.line_to(x1 + corner_size, y2)
            cr.arc(x1 + corner_size, y2 - corner_size, corner_size, math.pi / 2, math.pi)
            cr.line_to(x1, y1 + corner_size)
            cr.arc(x1 + corner_size, y1 + corner_size, corner_size, math.pi, 3 * math.pi / 2)
            cr.stroke()

        else:
            cr.set_source_rgb(1, 1, 1)
            cr.arc(x, y, r, 0, 2 * math.pi)
            cr.fill()
            cr.set_source_rgb(0, 0, 0)
            cr.arc(x, y, r, 0, 2 * math.pi)
            cr.stroke()

        cr.save()
        cr.translate(x - r, y - r)
        cr.scale(2 * r, 2 * r)
        draw_function(cr)
        cr.restore()

    def _add_text(self, cr0: cairo.Context, font_size, x, y, max_width, text):
        cr0.move_to(x, y)
        cr0.set_font_size(font_size)
        te = cr0.text_extents(text)
        while te.width > max_width:
            font_size *= 0.99
            cr0.set_font_size(font_size)
            te = cr0.text_extents(text)
        cr0.show_text(text)
        cr0.stroke()

    def _print_titles(self, cr0: cairo.Context,
                      cosmogram: Cosmogram, formula: SoulFormulaWithBorders, fio: str, city: str):
        x, y = cr0.device_to_user(self.title_x, self.title_y)
        cr0.move_to(x, y)
        cr0.set_font_size(self.title_height / self.width)
        cr0.select_font_face("Montserrat-Medium", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr0.set_source_rgb(0, 0, 0)

        title = 'Космограмма и Формула Души'.upper()
        title_te = cr0.text_extents(title)
        cr0.show_text(title)
        cr0.stroke()

        cr0.select_font_face("Montserrat-Light", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr0.set_font_size(self.subtitle_height / self.width)

        x, y = cr0.device_to_user(self.subtitle1_x, self.subtitle1_y)
        cr0.move_to(x, y)
        cr0.show_text('Авторский метод Александра Астрогора')
        cr0.stroke()

        cr0.set_line_width(0.001)
        line_y = y + self.text_offset * 2 / self.width / 1.5
        cr0.move_to(0, line_y)
        cr0.line_to(title_te.width, line_y)
        cr0.stroke()

        x, y = cr0.device_to_user(self.subtitle2_x, self.subtitle2_y)
        cr0.move_to(x, y)
        cr0.select_font_face('Montserrat-Light', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        user_dates = 'Дата: ' if not cosmogram.death_dt else 'Годы жизни: '
        cr0.show_text(user_dates)
        x += cr0.text_extents(user_dates).width + self.text_offset / self.width
        user_dates = formula.formula.dt.strftime("%d.%m.%Y %H:%M")
        if cosmogram.death_dt:
            user_dates += ' — ' + cosmogram.death_dt.strftime("%d.%m.%Y %H:%M")
        cr0.select_font_face("Montserrat-Light", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr0.show_text(user_dates)

        x, y = cr0.device_to_user(self.subtitle3_x, self.subtitle3_y)
        cr0.move_to(x, y)
        cr0.select_font_face('Montserrat-Light', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr0.show_text('Место: ')
        x += cr0.text_extents('Место: ').width + self.text_offset / self.width
        cr0.select_font_face("Montserrat-Light", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        self._add_text(cr0, self.subtitle_height / self.width, x, y, title_te.width, city)

        x, y = cr0.device_to_user(self.subtitle4_x, self.subtitle4_y)
        cr0.move_to(x, y)
        cr0.select_font_face("Montserrat-Medium", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        fio_font_size = (self.title_height + self.subtitle_height) / 2 / self.width
        self._add_text(cr0, fio_font_size, x, y, title_te.width, fio.upper())
        te = cr0.text_extents(fio.upper())
        cr0.set_line_width(0.001)
        cr0.set_source_rgb(0.9, 0.9, 0.9)
        space_x, space_y = 0.005, te.height * 0.3
        cr0.rectangle(x - space_x, y - te.height - space_y, te.width + space_x * 2, te.height + space_y * 2.5)
        cr0.fill()

        cr0.set_source_rgb(0, 0, 0)
        cr0.move_to(x, y)
        cr0.show_text(fio.upper())
        cr0.stroke()

        qr_x2 = self.width - self.qr_width
        self.__draw_qr_code(cr0, "https://astrogor.online/fd", qr_x2, 0)

        qr_font_size = 0.017
        cr0.select_font_face("Montserrat-Light", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr0.set_font_size(qr_font_size)
        x, y = cr0.device_to_user(qr_x2, self.qr_width + qr_font_size * self.width)
        cr0.move_to(x, y)
        cr0.show_text('astrogor.online')
        cr0.stroke()

    def print_info(self, fio: str, city: str, formula: SoulFormulaWithBorders, cosmogram: Cosmogram,
                   surface: cairo.Surface):
        surface.set_device_offset(self.border_offset, self.border_offset)
        cr0 = cairo.Context(surface)
        cr0.scale(self.width, self.width)

        self._print_titles(cr0, cosmogram, formula, fio, city)

        cr = cairo.Context(surface.create_for_rectangle(
            self.x - self.circle_radius, self.y - self.circle_radius, self.circle_radius * 2, self.circle_radius * 2))
        cr.scale(self.circle_radius * 2, self.circle_radius * 2)

        c_drawer = DefaultCosmogramDrawer(planet_ruler_place='in_sign')
        c_drawer.draw_cosmogram(cosmogram, cr)

        formula_radius = self.circle_radius * 0.65
        layout_maker = DefaultLayoutMaker(CircleFormulaCutter(formula_radius))
        drawer = SimpleFormulaDrawer()

        cr = cairo.Context(surface.create_for_rectangle(
            self.x - formula_radius, self.y - formula_radius, formula_radius * 2, formula_radius * 2))
        cr.scale(formula_radius * 2, formula_radius * 2)

        d_formula = layout_maker.make_layout(formula.formula)
        cr.arc(0.5, 0.5, 0.5, 0, 2 * math.pi)
        cr.clip()
        # cr.arc(0.5, 0.5, 0.5, 0, 2 * math.pi)
        # cr.stroke()
        drawer.draw_formula(d_formula, cr)
        cr.reset_clip()

        def foo(cr: cairo.Context):
            drawer.draw_formula_duration(formula, cr)

        def foo2(cr: cairo.Context):
            drawer.draw_power_points(formula.formula, cr)

        def foo3(cr: cairo.Context):
            cur_dt = datetime.now(pytz.timezone("Europe/Moscow"))
            drawer = DefaultCosmogramDrawer()
            drawer.draw_current_day(cur_dt, cosmogram, cr, age_units=self.age_units)

        self.draw_add_info(0, cr0, foo2, shape='rectangle')
        self.draw_add_info(1, cr0, foo, shape='rectangle')
        self.draw_add_info(5, cr0, foo3, shape='rectangle')

        def aspect_shape(cr1: cairo.Context):
            drawer = DefaultCosmogramDrawer()
            drawer.draw_aspect_shape(cosmogram, cr1)

        self.draw_add_info(0, cr0, aspect_shape, place='left')

        def aspect(aspect: int):
            def foo_res(cr1: cairo.Context):
                drawer = DefaultCosmogramDrawer()
                drawer.draw_aspect(cosmogram, cr1, aspect)

            return foo_res

        i = 1
        for a in cosmogram.aspects:
            self.draw_add_info(i, cr0, aspect(a), place='left')
            i += 1

    def __draw_qr_code(self, cr0: cairo.Context, url: str, x: float, y: float):
        qr = qrcode.QRCode(border=0)
        qr.add_data(url)
        m = qr.get_matrix()
        qr_size = len(m)
        x0, y0 = cr0.device_to_user(x, y)
        cell_width, _ = cr0.device_to_user_distance(self.qr_width / qr_size, 0)
        x, y = x0, y0
        cr0.move_to(x, y)
        for i in range(len(m)):
            for j in range(len(m[0])):
                if m[i][j]:
                    cr0.rectangle(x, y, cell_width, cell_width)
                    cr0.fill()
                x += cell_width
            x = x0
            y += cell_width

    def __draw_numeric_data(self, cr0: cairo.Context, numeric_info: NumericInfo):
        numeric_drawer = NumericDrawer()
        numeric_width = 12
        x, y = cr0.device_to_user(self.width - 2 * numeric_width, 0)
        r, _ = cr0.device_to_user_distance(numeric_width, 0)
        cr0.save()
        cr0.translate(x, y)
        cr0.scale(r, r)
        numeric_drawer.draw_soul_number(numeric_info.soul_number, cr0)
        cr0.restore()
        cr0.stroke()

        x, y = cr0.device_to_user(self.width - numeric_width, 0)
        r, _ = cr0.device_to_user_distance(numeric_width, 0)
        cr0.save()
        cr0.translate(x, y)
        cr0.scale(r, r)
        numeric_drawer.draw_fate_number(numeric_info.fate_number, cr0)
        cr0.restore()
        cr0.stroke()
