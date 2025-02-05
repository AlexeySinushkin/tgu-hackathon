import { LatLngExpression } from "leaflet";
import { Coordinate, Coordinates } from "./map.types";

export const getCenterCoordinate = (
  coordinates: [number, number][]
): LatLngExpression => {
  const total = coordinates.length;
  const sumLat = coordinates.reduce((sum, coord) => sum + coord[0], 0);
  const sumLon = coordinates.reduce((sum, coord) => sum + coord[1], 0);

  return [sumLat / total, sumLon / total];
};

export const getDistance = (
  [lat1, lon1]: Coordinate,
  [lat2, lon2]: Coordinate
) => {
  const R = 6371000; // Радиус Земли в метрах
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

  return R * c;
};

export const getDistanceAndBearing = (
  [lat1, lon1]: [number, number],
  [lat2, lon2]: [number, number]
) => {
  const R = 6371000; // Радиус Земли в метрах
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;

  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);

  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  const distance = R * c; // Расстояние в метрах

  // Определяем направление (азимут) в градусах
  const y = Math.sin(dLon) * Math.cos((lat2 * Math.PI) / 180);
  const x =
    Math.cos((lat1 * Math.PI) / 180) * Math.sin((lat2 * Math.PI) / 180) -
    Math.sin((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.cos(dLon);

  let bearing = (Math.atan2(y, x) * 180) / Math.PI;
  if (bearing < 0) bearing += 360; // Приводим к диапазону 0-360°

  return { distance, bearing };
};

export const sortByDistance = (
  array: { distance: number; index: number; bearing: number }[]
) => {
  return array.sort((a, b) => a.distance - b.distance);
};

export const filterNonZeroDistances = (
  array: { distance: number; index: number; bearing: number }[]
) => {
  return array
    .filter((item) => item.distance !== 0)
    .filter((item) => item.bearing < 250);
};

export const getNearCoordinate = (
  coordinates: Coordinates,
  actualCoordinate: Coordinate
) => {
  const distances = coordinates.map((coordinate, index) => ({
    ...getDistanceAndBearing(coordinate, actualCoordinate),
    index,
  }));

  return coordinates[
    filterNonZeroDistances(sortByDistance(distances))[0].index
  ];
};
