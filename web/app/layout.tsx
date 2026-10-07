import type { Metadata } from "next";
import { Barlow, Barlow_Condensed } from "next/font/google";
import { DataProvider } from "@/components/DataProvider";
import { Header } from "@/components/Header";
import { getShared } from "@/lib/data";
import "./globals.css";

const barlow = Barlow({ subsets: ["latin"], weight: ["400", "500", "600", "700"], variable: "--font-barlow" });
const condensed = Barlow_Condensed({
  subsets: ["latin"],
  weight: ["600", "700"],
  style: ["normal", "italic"],
  variable: "--font-barlow-condensed",
});

export const metadata: Metadata = {
  title: { default: "Driver vs Car", template: "%s · Driver vs Car" },
  description: "How fast is the driver, and how fast is the car? A Bayesian model of F1 qualifying, 2018–2026.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${barlow.variable} ${condensed.variable}`}>
      <body>
        <DataProvider value={getShared()}>
          <Header />
          <main className="mx-auto w-full max-w-6xl px-4 pb-16 sm:px-6">{children}</main>
          <footer className="border-t border-grid">
            <div className="mx-auto flex w-full max-w-6xl flex-wrap justify-between gap-2 px-4 py-6 text-sm text-muted sm:px-6">
              <span>One-lap pace from F1 qualifying 2018–2026, split into driver and car with a Bayesian model.</span>
              <span>Data: FastF1 · Driver photos © Formula 1 · Built by Riza Nursyah</span>
            </div>
          </footer>
        </DataProvider>
      </body>
    </html>
  );
}
