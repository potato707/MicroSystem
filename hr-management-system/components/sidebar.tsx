"use client"

import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import {
  Users,
  Calendar,
  FileText,
  MessageSquare,
  DollarSign,
  Wallet,
  FolderOpen,
  StickyNote,
  LayoutDashboard,
  LogOut,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { api } from "@/lib/api"

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Employees", href: "/employees", icon: Users },
  { name: "Attendance", href: "/attendance", icon: Calendar },
  { name: "Leave Requests", href: "/leave-requests", icon: FileText },
  { name: "Complaints", href: "/complaints", icon: MessageSquare },
  { name: "Reimbursements", href: "/reimbursements", icon: DollarSign },
  { name: "Wallets", href: "/wallets", icon: Wallet },
  { name: "Documents", href: "/documents", icon: FolderOpen },
  { name: "Notes", href: "/notes", icon: StickyNote },
]

export function Sidebar() {
  const pathname = usePathname()
  const router = useRouter()

  const handleLogout = () => {
    api.clearToken()
    router.push("/login")
  }

  return (
    <div className="flex h-screen w-64 flex-col bg-sidebar border-r border-sidebar-border">
      <div className="flex h-16 items-center border-b border-sidebar-border px-6">
        <h1 className="text-xl font-bold text-sidebar-foreground">HR System</h1>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigation.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? "bg-sidebar-accent text-sidebar-accent-foreground"
                  : "text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground"
              }`}
            >
              <item.icon className="h-5 w-5" />
              {item.name}
            </Link>
          )
        })}
      </nav>

      <div className="border-t border-sidebar-border p-4">
        <Button
          onClick={handleLogout}
          variant="ghost"
          className="w-full justify-start gap-3 text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground"
        >
          <LogOut className="h-5 w-5" />
          Logout
        </Button>
      </div>
    </div>
  )
}
