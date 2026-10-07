import type { Metadata } from "next";
import { Swap } from "@/components/Swap";
import { getDraws, getRatings } from "@/lib/data";

export const metadata: Metadata = { title: "Car swap" };

export default function Page() {
  return <Swap drivers={getRatings().drivers} draws={getDraws()} />;
}
