import "./globals.css";
import Navbar from "../components/Navbar";

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
        <Navbar />
        {children}
      </body>
    </html>
  );
}