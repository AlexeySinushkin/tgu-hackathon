import { useEffect, useState } from "react";

import "./App.css";
import { fetchData } from "./utils/fetch";
import MapComponent from "./components/map";
import { Coordinates } from "./components/map/map.types";

function App() {
  const [data, setData] = useState<Coordinates>([]);

  useEffect(() => {
    const asyncFetchData = async () => {
      const response = await fetchData("get-confirmed-coordinates");
      setData(response.map(({ latitude, longitude }) => [latitude, longitude]));
    };

    asyncFetchData();
  }, []);

  // Координаты точек маршрута
  const coordinates: Coordinates = [
    [52.226479, 104.303981],
    [52.226713, 104.303622],
    [52.227018, 104.303144],
    [52.227547, 104.302495],
    [52.227797, 104.30227],
    [52.228106, 104.302538],
    [52.228395, 104.302887],
    [52.228861, 104.303761],
  ];

  if (!data) {
    return <p>Загрузка</p>;
  }

  if (data.length < 2) {
    setData(coordinates);
  }

  return <MapComponent coordinates={data} />;
}

export default App;
