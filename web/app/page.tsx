import type { Metadata } from "next";
import { DriverRanking } from "@/components/DriverRanking";
import { getRatings } from "@/lib/data";

export const metadata: Metadata = { title: "Driver ranking" };

export default function Page() {
  return <DriverRanking drivers={getRatings().drivers} />;
}
