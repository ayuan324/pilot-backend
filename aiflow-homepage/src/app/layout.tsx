import type { Metadata } from "next";
import { GeistSans } from "geist/font/sans";
import "./globals.css";

export const metadata: Metadata = {
  title: "πlot - Build AI Workflows with Natural Language",
  description:
    "Design, create, and deploy intelligent AI workflows with natural language and visual tools. The easiest way to build AI applications.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full">
      <body className={`${GeistSans.className} antialiased h-full`}>
        {children}
      </body>
    </html>
  );
}
