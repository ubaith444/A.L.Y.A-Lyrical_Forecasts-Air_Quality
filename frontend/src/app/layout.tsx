import type { Metadata } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";

const jakarta = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-jakarta",
  display: "swap",
});

export const metadata: Metadata = {
  title: "A.L.Y.A — Lyrical Forecasts & Air Quality",
  description:
    "A.L.Y.A: Weather forecasting, air quality monitoring, and climate intelligence for India. Accurate data presented through a calm, lyrical interface. The sky, simplified.",
  icons: {
    icon: "/logo.png",
    apple: "/logo.png",
  },
  keywords: [
    "A.L.Y.A",
    "Alya Weather",
    "Weather India",
    "Tamil Nadu Weather",
    "Chennai Forecast",
    "CPCB AQI",
    "Air Quality Index India",
    "Climate Intelligence",
    "Monsoon Analysis",
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={jakarta.variable}>
      <head>
        <meta name="theme-color" content="#FAFAF7" />
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5" />
        <link rel="icon" href="/logo.png" type="image/png" />
      </head>
      <body className="font-sans bg-canvas text-ink-primary antialiased min-h-screen flex flex-col selection:bg-brand-skyLight selection:text-brand-sky">
        {children}
      </body>
    </html>
  );
}
