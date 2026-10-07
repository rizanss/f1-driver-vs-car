import type { Metadata } from "next";
import { CarRanking } from "@/components/CarRanking";
import { getRatings } from "@/lib/data";

export const metadata: Metadata = { title: "Car ranking" };

export default function Page() {
  const { cars, drivers } = getRatings();
  return <CarRanking cars={cars} drivers={drivers} />;
}
