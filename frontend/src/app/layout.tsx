import "./globals.css";
import Navbar from "../components/Navbar";
import { ClerkProvider } from "@clerk/nextjs";
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
    <ClerkProvider>
      <html lang="en">
        <body className="bg-slate-950 text-white">
          <Providers>
            <Navbar />
            {children}
          </Providers>
        </body>
      </html>
    </ClerkProvider>
  );
}