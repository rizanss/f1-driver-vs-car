import type { Metadata } from "next";
import { Career } from "@/components/Career";
import { getRatings } from "@/lib/data";

export const metadata: Metadata = { title: "Career path" };

export default function Page() {
  return <Career drivers={getRatings().drivers} />;
}
