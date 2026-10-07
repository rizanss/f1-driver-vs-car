import type { Metadata } from "next";
import { HeadToHead } from "@/components/HeadToHead";
import { getDraws, getRatings } from "@/lib/data";

export const metadata: Metadata = { title: "Head to head" };

export default function Page() {
  return <HeadToHead drivers={getRatings().drivers} draws={getDraws().drivers} />;
}
