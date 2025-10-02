"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Users, Calendar, FileText, DollarSign } from "lucide-react"
import { api } from "@/lib/api"

export default function DashboardPage() {
  const [stats, setStats] = useState({
    employees: 0,
    attendance: 0,
    leaveRequests: 0,
    reimbursements: 0,
  })

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const today = new Date().toISOString().split("T")[0]
        const [employees, attendance, leaves, reimbursements] = await Promise.all([
          api.getEmployees(),
          api.getAttendance({date: today}),
          api.getLeaveRequests(),
          api.getReimbursements(),
        ])

        setStats({
          employees: employees.length,
          attendance: attendance.length,
          leaveRequests: leaves.filter((l: any) => l.status === "pending").length,
          reimbursements: reimbursements.filter((r: any) => r.status === "pending").length,
        })
      } catch (error) {
        console.error("[v0] Failed to fetch dashboard stats:", error)
      }
    }

    fetchStats()
  }, [])

  const cards = [
    {
      title: "Total Employees",
      value: stats.employees,
      icon: Users,
      color: "text-primary",
    },
    {
      title: "Today's Attendance",
      value: stats.attendance,
      icon: Calendar,
      color: "text-accent",
    },
    {
      title: "Pending Leave Requests",
      value: stats.leaveRequests,
      icon: FileText,
      color: "text-warning",
    },
    {
      title: "Pending Reimbursements",
      value: stats.reimbursements,
      icon: DollarSign,
      color: "text-success",
    },
  ]

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-foreground">Dashboard</h1>
        <p className="text-muted-foreground mt-2">Welcome to the HR Management System</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {cards.map((card) => (
          <Card key={card.title}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">{card.title}</CardTitle>
              <card.icon className={`h-5 w-5 ${card.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-foreground">{card.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">No recent activity to display</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <p className="text-sm text-muted-foreground">Use the sidebar to navigate to different sections</p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
