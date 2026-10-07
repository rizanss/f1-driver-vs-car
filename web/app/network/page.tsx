import type { Metadata } from "next";
import { Network } from "@/components/Network";
import { getNetwork } from "@/lib/data";

export const metadata: Metadata = { title: "Driver network" };

export default function Page() {
  return <Network network={getNetwork()} />;
}
