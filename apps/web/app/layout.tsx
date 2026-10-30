import type { Metadata } from "next"
import "./globals.css"
import { Sidebar } from "@/components/layout/Sidebar"
import { Header } from "@/components/layout/Header"

export const metadata: Metadata = {
  title: "StockPilot AI — Indian Equities Quantitative Platform",
  description: "AI-Powered Stock Analysis, Walk-Forward ML Prediction & Paper Trading for NSE/BSE Equities",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#080D14] text-slate-100 flex min-h-screen">
        <Sidebar />
        <div className="flex-1 flex flex-col min-w-0 bg-[#080D14]">
          <Header />
          <main className="flex-1 p-5 overflow-y-auto">{children}</main>
        </div>
      </body>
    </html>
  )
}
