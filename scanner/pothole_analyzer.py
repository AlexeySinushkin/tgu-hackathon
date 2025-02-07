import unittest
import cv2
from enum import Enum
import numpy as np
from matplotlib import pyplot as plt
from correlation import ref_corel_calculate, second_color_intensity
from image_utils import draw_correl_value

cell_size = 20
num_bins = 255
color_range = [0, 256]
threshold_good_correlate = 0.4
threshold_medium_correlate = 0.3
threshold_pothole = 0.2


class CellKind(Enum):
    UNKNOWN = 0
    FLAT = 1
    PROBABLY_POTHOLE = 2
    POTHOLE = 3
    SKIP = 4  # исключено из анализа (похоже на дорожную разметку, осевая, пешеходный переход)


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
        self.second_color_intensity = 0.0
        self.kind = CellKind.UNKNOWN

    # получить маленький кусочек изображения, соответствующий этой ячейке
    def crop(self, image):
        return image[self.y_lt:self.y_lt + cell_size, self.x_lt:self.x_lt + cell_size]

    def get_color(self):
        color = (255, 255, 255)
        if self.kind == CellKind.PROBABLY_POTHOLE:
            # BGR yellow
            color = (0, 255, 255)
        elif self.kind == CellKind.POTHOLE:
            # red
            color = (0, 0, 255)
        return color


class FoundRegion:
    x_left_top: int
    y_left_top: int
    width: int
    height: int
    def __init__(self, cell):
        self.x_left_top = cell.x_lt
        self.y_left_top = cell.y_lt
        self.width = cell.width*2
        self.height = cell.height*2


class PotholeAnalyzer:
    width: int
    height: int
    threshold = 0.5
    threshold_pothole = 0.07
    threshold_max = 0.1
    def __init__(self, width, height):
        self.width = width
        self.height = height
        # референсный ряд ячеек - нижний. Отсчет снизу вверх
        # Мы считаем кадр пригодный для анализа в том случае если есе ячейки в референсном ряду плюс минус одинаковы

        # количество ячеек вдоль оси х
        cells_count_x = int((width / cell_size) - 2)
        padding = (width - (cells_count_x * cell_size)) / cells_count_x
        cells_count_y = int((height - padding) / (cell_size + padding))
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


    def analyze_and_draw(self, image_for_analyze, image_for_draw) -> FoundRegion | None:
        self.__reset_cells()
        analyze_success = self.analyze(image_for_analyze)
        # рисуем референсный ряд
        for cell in self.reference_row:
            cv2.rectangle(image_for_draw, (cell.x_lt, cell.y_lt), (cell.x_lt + cell_size, cell.y_lt + cell_size),
                          (0, 0, 0), 1)
        result = None
        for row in self.search_grid:
            for cell in row:
                if analyze_success and cell.second_color_intensity>0.3:
                    # визуализируем корреляцию гистограммы -  чем меньше корреляция, тем выше столбик
                    correl_value = int(cell.second_color_intensity*10)
                    draw_correl_value(image_for_draw, correl_value, cell.x_lt + 5, int(cell.y_lt+cell_size/2))
                    cv2.rectangle(image_for_draw, (cell.x_lt, cell.y_lt), (cell.x_lt + cell_size, cell.y_lt + cell_size), cell.get_color(), 1)
                    result = FoundRegion(cell)
        return result

    def __reset_cells(self):
        for row in self.search_grid:
            for cell in row:
                cell.kind = CellKind.UNKNOWN
                cell.correlation = None
                cell.second_color_intensity = 0.0

    def calculate_reference_row(self, gray_image):
        ref_row_hist = []
        for cell in self.reference_row:
            cell_image = cell.crop(gray_image)
            hist = cv2.calcHist([cell_image], [0], None, [num_bins], color_range)
            cv2.normalize(hist, hist, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
            ref_row_hist.append(hist)
        return gray_image, ref_row_hist


    def calculate_reference_row_correl(self, ref_row_hist):
        correl_result = np.zeros(len(ref_row_hist), dtype=np.float32)
        # средняя гистограмма по референсным ячейкам
        middle_index = int(len(ref_row_hist) / 2)
        #чем меньше тем лучше
        correl_result[middle_index] = 1.0
        left_limit = 0
        right_limit = len(ref_row_hist) - 1
        left = middle_index
        right = middle_index
        for i in range(middle_index, right_limit):
            correlation = ref_corel_calculate(ref_row_hist[i], ref_row_hist[i + 1])
            if correlation >= self.threshold:
                correl_result[i + 1] = correlation
                right = i + 1
            else:
                break
        for i in range(middle_index, left_limit, -1):
            correlation = ref_corel_calculate(ref_row_hist[i], ref_row_hist[i - 1])
            if correlation >= self.threshold:
                correl_result[i - 1] = correlation
                left = i - 1
            else:
                break
        return left, right, correl_result

    def analyze(self, gray_image):
        # Apply Gaussian blur
        gray_image = cv2.GaussianBlur(gray_image, (7, 7), 9)
        gray_image, ref_row_hist = self.calculate_reference_row(gray_image)
        left, right, ref_correl = self.calculate_reference_row_correl(ref_row_hist)
        #если ячеек для анализа меньше половины - не может анализировать
        if (right - left) < len(ref_row_hist) / 2:
            return False
        for row in self.search_grid:
            for i in range(left, right + 1):
                cell = row[i]
                cell_image = cell.crop(gray_image)
                hist = cv2.calcHist([cell_image], [0], None, [num_bins], color_range)
                cv2.normalize(hist, hist, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
                #cell.correlation = ref_corel_calculate(hist, ref_row_hist[i])
                cell.second_color_intensity = second_color_intensity(hist, ref_row_hist[i])
        return True


class Frame55Test(unittest.TestCase):
    def show_ref_cells_img(self, analyzer, gray_image):
        len_cells = len(analyzer.reference_row)
        rows = int(len_cells / 6) + 1
        fig, axes = plt.subplots(rows, 5, figsize=(20, 10))
        axes = axes.flatten()
        for i, ax in enumerate(axes.flat):
            if i < len_cells:
                # Plot the histogram
                img =analyzer.reference_row[i].crop(gray_image)
                ax.imshow(img)
                ax.set_title(f"Image {i}")
        plt.tight_layout()
        plt.show()

    def show_ref_cells_hist(self, analyzer, hist):
        len_cells = len(analyzer.reference_row)
        rows = int(len_cells / 6) + 1
        fig, axes = plt.subplots(rows, 5, figsize=(20, 10))
        axes = axes.flatten()
        for i, ax in enumerate(axes.flat):
            if i < len(hist):
                # Plot the histogram
                ax.plot(hist[i], color='black')
                ax.set_title(f"Histogram {i}")
                ax.set_xlim([80, 110])  # Set x-axis range for pixel intensity
        plt.tight_layout()
        plt.show()

    def show_ref_cells_hist2(self, analyzer, hist):
        len_cells = len(analyzer.reference_row)
        rows = int(len_cells / 6) + 1
        fig, axes = plt.subplots(rows, 5, figsize=(20, 10))
        axes = axes.flatten()
        for i, ax in enumerate(axes.flat):
            if i < len(hist):
                # Plot the histogram
                ax.plot(hist[i][0], color='black')
                ax.set_title(f"Histogram {i} {hist[i][1]}")

        plt.tight_layout()
        plt.show()


    def test_draw_hist_ref(self):
        gray_image = cv2.imread("resources/frame_55.png")
        analyzer = PotholeAnalyzer(432, 128)
        gray_image, hist = analyzer.calculate_reference_row(gray_image)
        left, right, avg_hist = analyzer.calculate_reference_row_correl(hist)

        print(f"left {left}, right {right}")
        print(f"recalculate correlation to Avg histogram")
        for i in range(len(hist)):
            correlation = ref_corel_calculate(hist[i], avg_hist)
            print(f"{i} - {correlation}")
        #self.show_ref_cells_hist(analyzer, hist, avg_hist)
        #self.show_ref_cells_img(analyzer, gray_image)

    def test_draw_hist_row(self):
        gray_image = cv2.imread("resources/frame_55.png")
        analyzer = PotholeAnalyzer(432, 128)
        analyzer.analyze(gray_image)
        hists = []
        for i in range(len(analyzer.reference_row)):
            cell = analyzer.search_grid[0][i]
            cell_image = cell.crop(gray_image)
            hist = cv2.calcHist([cell_image], [0], None, [num_bins], color_range)
            cv2.normalize(hist, hist, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
            hists.append((hist, cell.correlation))
        self.show_ref_cells_hist2(analyzer, hists)

    def test_draw(self):
        gray_image = cv2.imread("resources/frame_55.png")
        analyzer = PotholeAnalyzer(432, 128)
        analyzer.analyze_and_draw(gray_image, gray_image)
        cv2.imshow("Cells", gray_image)
        key = cv2.waitKey(0)
        # Esc
        if key == 27:
            cv2.destroyAllWindows()


