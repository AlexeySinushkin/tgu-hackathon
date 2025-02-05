import { useState, useEffect } from "react";
import { getDistance } from "./map.helpes";

// Хук для передвижения по маршруту
const useRouteProgress = (
  coordinates: [number, number][],
  startPosition: [number, number]
) => {
  const [currentPosition, setCurrentPosition] =
    useState<[number, number]>(startPosition);
  const [currentIndex, setCurrentIndex] = useState<number | null>(null);

  useEffect(() => {
    let interval: NodeJS.Timeout;

    const moveToNextPoint = () => {
      if (currentIndex === null) return;

      const nextIndex = currentIndex + 1;
      if (nextIndex >= coordinates.length) {
        clearInterval(interval);
        return;
      }

      const currentCoord = coordinates[currentIndex];
      const nextCoord = coordinates[nextIndex];
      const distance = getDistance(currentCoord, nextCoord);
      const steps = Math.ceil(distance / 1); // 1 метр за шаг
      let step = 0;

      interval = setInterval(() => {
        if (step >= steps) {
          clearInterval(interval);
          setCurrentIndex(nextIndex);
        } else {
          const lat =
            currentCoord[0] + ((nextCoord[0] - currentCoord[0]) / steps) * step;
          const lon =
            currentCoord[1] + ((nextCoord[1] - currentCoord[1]) / steps) * step;
          setCurrentPosition([lat, lon]);
          step++;
        }
      }, 1000); // Шаг каждую секунду
    };

    if (currentIndex === null) {
      // Найти первую ближайшую координату в радиусе 50 м
      for (let i = 0; i < coordinates.length; i++) {
        if (getDistance(startPosition, coordinates[i]) <= 50) {
          setCurrentIndex(i);
          break;
        }
      }
    } else {
      moveToNextPoint();
    }

    return () => clearInterval(interval);
  }, [currentIndex]);

  return currentPosition;
};

export default useRouteProgress;
