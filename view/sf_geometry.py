import math


def rotate_point(x0: float, y0: float, x: float, y: float, alpha: float) -> (float, float):
    x1, y1 = x - x0, y - y0
    xr = math.cos(alpha) * x1 - math.sin(alpha) * y1
    yr = math.sin(alpha) * x1 + math.cos(alpha) * y1
    return xr + x0, yr + y0
