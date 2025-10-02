"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Plus, Edit, LogIn, LogOutIcon } from "lucide-react"
import { api } from "@/lib/api"
import type { Attendance } from "@/lib/types"
import { AttendanceDialog } from "@/components/attendance-dialog"
import { Sidebar } from "@/components/sidebar"

export default function AttendancePage() {
  const [attendance, setAttendance] = useState<Attendance[]>([])
  const [loading, setLoading] = useState(true)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [selectedAttendance, setSelectedAttendance] = useState<Attendance | null>(null)
  const [dateFilter, setDateFilter] = useState(new Date().toISOString().split("T")[0])

  const fetchAttendance = async () => {
    try {
      const data = await api.getAttendance({ date: dateFilter })
      setAttendance(data)
    } catch (error) {
      console.error("[v0] Failed to fetch attendance:", error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAttendance()
  }, [dateFilter])

  const handleCheckIn = async (employeeId: string) => {
    try {
      await api.checkIn(employeeId)
      fetchAttendance()
    } catch (error) {
      console.error("[v0] Failed to check in:", error)
    }
  }

  const handleCheckOut = async (employeeId: string) => {
    try {
      await api.checkOut(employeeId)
      fetchAttendance()
    } catch (error) {
      console.error("[v0] Failed to check out:", error)
    }
  }

  const handleEdit = (record: Attendance) => {
    setSelectedAttendance(record)
    setDialogOpen(true)
  }

  const handleDialogClose = () => {
    setDialogOpen(false)
    setSelectedAttendance(null)
    fetchAttendance()
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      present: "bg-success/20 text-success",
      absent: "bg-destructive/20 text-destructive",
      late: "bg-warning/20 text-warning",
      on_leave: "bg-primary/20 text-primary",
    }
    return colors[status] || "bg-muted text-muted-foreground"
  }

  return (
    <div className="p-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Attendance</h1>
          <p className="text-muted-foreground mt-2">Track employee attendance and check-ins</p>
        </div>
        <Button onClick={() => setDialogOpen(true)} className="gap-2">
          <Plus className="h-4 w-4" />
          Add Record
        </Button>
      </div>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Filter by Date</CardTitle>
        </CardHeader>
        <CardContent>
          <Input type="date" value={dateFilter} onChange={(e) => setDateFilter(e.target.value)} className="max-w-xs" />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Attendance Records</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-center text-muted-foreground py-8">Loading attendance...</p>
          ) : attendance.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">No attendance records found</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Employee</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Check In</TableHead>
                  <TableHead>Check Out</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Paid</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {attendance.map((record) => (
                  <TableRow key={record.id}>
                    <TableCell className="font-medium">{record.employee_name}</TableCell>
                    <TableCell>{record.date}</TableCell>
                    <TableCell>{record.check_in || "-"}</TableCell>
                    <TableCell>{record.check_out || "-"}</TableCell>
                    <TableCell>
                      <Badge className={getStatusColor(record.status)}>{record.status}</Badge>
                    </TableCell>
                    <TableCell>{record.paid ? "Yes" : "No"}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        {!record.check_in && (
                          <Button variant="ghost" size="icon" onClick={() => handleCheckIn(record.employee)}>
                            <LogIn className="h-4 w-4 text-success" />
                          </Button>
                        )}
                        {record.check_in && !record.check_out && (
                          <Button variant="ghost" size="icon" onClick={() => handleCheckOut(record.employee)}>
                            <LogOutIcon className="h-4 w-4 text-warning" />
                          </Button>
                        )}
                        <Button variant="ghost" size="icon" onClick={() => handleEdit(record)}>
                          <Edit className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <AttendanceDialog open={dialogOpen} onClose={handleDialogClose} attendance={selectedAttendance} />
    </div>
  )
}
