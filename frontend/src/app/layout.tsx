import "./globals.css";
import Navbar from "../components/Navbar";
import { Providers } from "../hooks/lib/providers";

export const metadata = {
  title: "FairLens",
  description: "AI Fairness Platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-slate-950 text-white">
        <Providers>
          <Navbar />
          {children}
        </Providers>
      </body>
    </html>
  );
}