import numpy as np
from scipy.optimize import curve_fit

#реализация корреляционной функции для референсного ряда
#ищем приблизительно одинаковые параболы

# Define a quadratic (parabolic) function
def parabola(x, a, b, c):
    return a * x ** 2 + b * x + c


# Function to fit a parabola to a histogram
def fit_parabola(hist):
    x_values = np.arange(len(hist))  # Bin indices
    y_values = hist.flatten()  # Histogram counts

    # Fit parabola
    params, _ = curve_fit(parabola, x_values, y_values)

    return params  # Returns (a, b, c)

def ref_corel_calculate_old(hist1, hist2):
    # Fit parabolas to both histograms
    params1 = fit_parabola(hist1)
    params2 = fit_parabola(hist2)
    a1 = abs(params1[0])
    a2 = abs(params2[0])
    #интересует ширина параболы
    if a1<a2:
        return a1/a2
    return a2/a1

def get_left_right_index(hist):
    # Find indices where histogram is non-zero
    non_zero_indices = np.where(hist > 0)[0]
    # Get the lowest non-zero index
    low_non_zero_index = non_zero_indices[0] if non_zero_indices.size > 0 else None
    high_non_zero_index = non_zero_indices[len(non_zero_indices)-1] if non_zero_indices.size > 0 else None
    return low_non_zero_index, high_non_zero_index

def ref_corel_calculate_ranges(left_range, right_range):
    left1, right1, delta1 = left_range
    left2, right2, delta2 = right_range
    # не пересекаются или
    if right1<=left2:
        return 0.0
    intersection = right1 - left2
    return intersection*2/(delta1 + delta2)

def ref_corel_calculate(hist1, hist2):
    # Fit parabolas to both histograms
    left1, right1 = get_left_right_index(hist1)
    if left1 is None or right1 is None:
        return 0.0
    delta1 = right1 - left1
    center1 = left1 + int(delta1/2)
    left2, right2 = get_left_right_index(hist2)
    if left2 is None or right2 is None:
        return 0.0
    delta2 = right2 - left2
    center2 = left2 + int(delta2 / 2)
    if center1<center2:
        return ref_corel_calculate_ranges((left1, right1, delta1), (left2, right2, delta2))
    return ref_corel_calculate_ranges((left2, right2, delta2), (left1, right1, delta1))

