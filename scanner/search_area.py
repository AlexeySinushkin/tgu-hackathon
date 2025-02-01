#интересуемая область на изображении

class SearchArea:
  #расстояние от левого верхнего угла в процентах
  left_top: (float, float) # x, y
  right_bottom: (float, float)

  def __init__(self, x_lt, y_lt, x_rb, y_rb):
    self.left_top = (x_lt, y_lt)
    self.right_bottom = (x_rb, y_rb)

  #получить картинку области
  def crop(self, image):
    height, width = image.shape[:2]
    x1 = int(self.left_top[0] * width)
    x2 = int(self.right_bottom[0] * width)
    y1 = int(self.left_top[1]*height)
    y2 = int(self.right_bottom[1]*height)
    return image[y1:y2, x1:x2]

  #пересчитать координаты, которые были найдены в уменьшенной области поиска
  #в координаты оригинальной картинки
  def translate_coordinates_to_original(self, original_image, x, y):
    height, width = original_image.shape[:2]
    original_x = self.left_top[0] * width + x
    original_y = self.left_top[1] * height + y
    return int(original_x), int(original_y)

