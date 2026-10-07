import type { Metadata } from "next";
import { CarVsDriver } from "@/components/CarVsDriver";
import { getSeasons } from "@/lib/data";

export const metadata: Metadata = { title: "Car vs driver" };

export default function Page() {
  const { seasons, eras } = getSeasons();
  return <CarVsDriver seasons={seasons} eras={eras} />;
}
