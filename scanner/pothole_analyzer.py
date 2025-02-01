import cv2
from enum import Enum
import numpy as np

cell_size = 20

class CellKind(Enum):
    UNKNOWN = 0
    FLAT = 1
    PROBABLY_POTHOLE = 2
    POTHOLE = 3
    SKIP = 4    #исключено из анализа (похоже на дорожную разметку, осевая, пешеходный переход)

class Cell:
    x_lt: int
    y_lt: int
    width: int
    height: int
    correlation: float | None
    kind: CellKind
    def __init__(self, x_lt, y_lt, width, height):
        self.x_lt = x_lt
        self.y_lt = y_lt
        self.width = width
        self.height = height
        self.correlation = None
        self.kind = CellKind.UNKNOWN

    # получить маленький кусочек изображения, соответствующий этой ячейке
    def crop(self, image):
        return image[self.y_lt:self.y_lt + cell_size, self.x_lt:self.x_lt + cell_size]

    def get_color(self):
        color = (255, 255, 255)
        if self.kind == CellKind.PROBABLY_POTHOLE:
            #BGR yellow
            color = (0, 255, 255)
        elif self.kind == CellKind.POTHOLE:
            # red
            color = (0, 0, 255)
        return color


class PotholeAnalyzer:
  width: int
  height: int
  def __init__(self, width, height):
    self.width = width
    self.height = height
    #референсный ряд ячеек - нижний. Отсчет снизу вверх
    #Мы считаем кадр пригодный для анализа в том случае если есе ячейки в референсном ряду плюс минус одинаковы

    # количество ячеек вдоль оси х
    cells_count_x = int((width / cell_size) - 2)
    padding = (width - (cells_count_x*cell_size))/cells_count_x
    cells_count_y = int((height-padding) / (cell_size + padding))
    self.reference_row = []
    self.search_grid = []

    for j in range(0, cells_count_y):
        row = []
        y_lt = int(height - cell_size - padding - (cell_size + padding) * j)
        for i in range(0, cells_count_x):
            x_lt = int((cell_size + padding) * i)
            row.append(Cell(x_lt, y_lt, cell_size, cell_size))
        if j == 0:
            self.reference_row = row
        else:
            self.search_grid.append(row)

  def analyze_and_draw(self, image_for_analyze, image_for_draw):
    self._reset_cells()
    # Apply Gaussian blur
    image_for_analyze = cv2.GaussianBlur(image_for_analyze, (15, 15), 5)
    analyze_success = self._analyze(image_for_analyze)
    #рисуем референсный ряд
    for cell in self.reference_row:
        cv2.rectangle(image_for_draw, (cell.x_lt, cell.y_lt), (cell.x_lt+cell_size, cell.y_lt+cell_size), (0, 0, 0), 1)
    for row in self.search_grid:
        for cell in row:
            if analyze_success and cell.correlation is not None:
                # визуализируем корреляцию гистограммы -  чем меньше корреляция, тем выше столбик
                cv2.line(image_for_draw, (cell.x_lt+1, cell.y_lt+cell_size),
                         (cell.x_lt+1, int(cell.y_lt+(cell_size*cell.correlation))),
                         cell.get_color(), 2)  # Blue dashed line
                #cv2.rectangle(image_for_draw, (cell.x_lt, cell.y_lt), (cell.x_lt + cell_size, cell.y_lt + cell_size), cell.get_color(), 1)

  def _reset_cells(self):
      for row in self.search_grid:
          for cell in row:
              cell.kind = CellKind.UNKNOWN
              cell.correlation = None

  def _analyze(self, gray_image) ->bool:
    threshold_good_correlate = 0.7
    threshold_medium_correlate = 0.5
    threshold_pothole = 0.3
    color_range = [0, 256]
    beta = 100
    ref_row_hist = []
    # Initialize an empty histogram
    num_bins = 255
    for cell in self.reference_row:
        cell_image = cell.crop(gray_image)
        hist = cv2.calcHist([cell_image], [0], None, [num_bins], color_range)
        cv2.normalize(hist, hist, alpha=0, beta=beta, norm_type=cv2.NORM_MINMAX)
        ref_row_hist.append(hist)

    # средняя гистограмма по референсным ячейкам
    middle_index = int(len(ref_row_hist) / 2)
    avg_hist = ref_row_hist[middle_index]
    avg_count = 1
    left_limit = 0
    right_limit = len(ref_row_hist)-1
    left = middle_index
    right = middle_index
    for i in range(middle_index, right_limit):
        correlation = cv2.compareHist(ref_row_hist[i], ref_row_hist[i+1], cv2.HISTCMP_CORREL)
        if threshold_good_correlate <= correlation:
            avg_count += 1
            avg_hist += ref_row_hist[i+1]  # Accumulate histogram
            right = i+1
        else:
            break
    for i in range(middle_index, left_limit, -1):
        correlation = cv2.compareHist(ref_row_hist[i], ref_row_hist[i-1], cv2.HISTCMP_CORREL)
        if threshold_good_correlate <= correlation:
            avg_count += 1
            avg_hist += ref_row_hist[i-1]  # Accumulate histogram
            left = i-1
        else:
            break
    if (right-left) < len(ref_row_hist) / 2:
        return False
    avg_hist /= avg_count
    for row in self.search_grid:
        for i in range(left, right+1):
            cell = row[i]
            cell_image = cell.crop(gray_image)
            hist = cv2.calcHist([cell_image], [0], None, [num_bins], color_range)
            cv2.normalize(hist, hist, alpha=0, beta=beta, norm_type=cv2.NORM_MINMAX)
            cell.correlation = cv2.compareHist(hist, avg_hist, cv2.HISTCMP_CORREL)
            if threshold_medium_correlate < cell.correlation:
                cell.kind = CellKind.FLAT
            elif threshold_pothole < cell.correlation <= threshold_medium_correlate:
                cell.kind = CellKind.PROBABLY_POTHOLE
            elif cell.correlation <= threshold_pothole:
                cell.kind = CellKind.POTHOLE
    return True


