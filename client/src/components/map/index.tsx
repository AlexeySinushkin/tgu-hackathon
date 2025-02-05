import {
  MapContainer,
  TileLayer,
  Marker,
  Polyline,
  Circle,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { useMemo } from "react";
import L, { LatLngExpression } from "leaflet";
import {
  getCenterCoordinate,
  getDistance,
  getNearCoordinate,
} from "./map.helpes";
import useRouteProgress from "./useRouterProgress";
import { Coordinates } from "./map.types";

// Кастомная иконка маркера
const customIcon = new L.Icon({
  iconUrl: "/auto.png",
  iconSize: [24, 24],
});

const MapComponent = ({ coordinates }: { coordinates: Coordinates }) => {
  const carCoordinate = useRouteProgress(coordinates, coordinates[0]);
  const centerCoordinate = useMemo(
    () => getCenterCoordinate(coordinates),
    [coordinates]
  );

  const nearCoordinate = getNearCoordinate(coordinates, carCoordinate);
  const distance = getDistance(nearCoordinate, carCoordinate);

  return (
    <>
      {distance < 10 && (
        <div className="message">
          <p>В {Math.round(distance)} метрах яма</p>
        </div>
      )}
      <MapContainer
        center={centerCoordinate} // Центрируем карту на середину маршрута
        zoom={20}
        style={{ height: "100%", width: "100%", position: "absolute" }}
      >
        {/* Подложка OpenStreetMap */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {/* Маркеры для каждой точки */}
        {coordinates.map((position, index) => (
          <Circle
            key={index}
            center={position}
            pathOptions={{ fillColor: "red", color: "red" }}
            radius={3}
          />
        ))}

        <Marker position={carCoordinate} icon={customIcon} />
        {/* Линия, соединяющая точки */}
        <Polyline
          positions={[nearCoordinate as LatLngExpression, carCoordinate]}
          color="blue"
        />
      </MapContainer>
    </>
  );
};

export default MapComponent;
