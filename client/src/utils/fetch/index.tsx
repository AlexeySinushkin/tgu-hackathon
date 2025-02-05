import { baseApi } from "../../api/constant";

export const fetchData = async (
  route: string
): Promise<
  { id: number; latitude: number; longitude: number; data: string }[]
> => {
  return await fetch(baseApi + route)
    .then((response) => {
      return response.json();
    })
    .then((data) => {
      return data;
    })
    .catch((error) => error);
};
