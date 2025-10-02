"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Plus, Check, X } from "lucide-react"
import { api } from "@/lib/api"
import type { LeaveRequest } from "@/lib/types"
import { LeaveRequestDialog } from "@/components/leave-request-dialog"

export default function LeaveRequestsPage() {
  const [leaveRequests, setLeaveRequests] = useState<LeaveRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [dialogOpen, setDialogOpen] = useState(false)

  const fetchLeaveRequests = async () => {
    try {
      const data = await api.getLeaveRequests()
      setLeaveRequests(data)
    } catch (error) {
      console.error("[v0] Failed to fetch leave requests:", error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchLeaveRequests()
  }, [])

  const handleApprove = async (id: string, usePatch = false) => {
    try {
      if (usePatch) {
        await api.patchLeaveRequestStatus(id, { status: "approved" })
      } else {
        await api.updateLeaveRequestStatus(id, { status: "approved" })
      }
      fetchLeaveRequests()
    } catch (error) {
      console.error("[v0] Failed to approve leave request:", error)
    }
  }

  const handleReject = async (id: string, usePatch = false) => {
    try {
      if (usePatch) {
        await api.patchLeaveRequestStatus(id, { status: "rejected" })
      } else {
        await api.updateLeaveRequestStatus(id, { status: "rejected" })
      }
      fetchLeaveRequests()
    } catch (error) {
      console.error("[v0] Failed to reject leave request:", error)
    }
  }

  const handleDialogClose = () => {
    setDialogOpen(false)
    fetchLeaveRequests()
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      pending: "bg-warning/20 text-warning",
      approved: "bg-success/20 text-success",
      rejected: "bg-destructive/20 text-destructive",
    }
    return colors[status] || "bg-muted text-muted-foreground"
  }

  return (
    <div className="p-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Leave Requests</h1>
          <p className="text-muted-foreground mt-2">Manage employee leave requests</p>
        </div>
        <Button onClick={() => setDialogOpen(true)} className="gap-2">
          <Plus className="h-4 w-4" />
          New Request
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Leave Request List</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-center text-muted-foreground py-8">Loading leave requests...</p>
          ) : leaveRequests.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">No leave requests found</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Employee</TableHead>
                  <TableHead>Start Date</TableHead>
                  <TableHead>End Date</TableHead>
                  <TableHead>Reason</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {leaveRequests.map((request) => (
                  <TableRow key={request.id}>
                    <TableCell className="font-medium">{request.employee_name}</TableCell>
                    <TableCell>{request.start_date}</TableCell>
                    <TableCell>{request.end_date}</TableCell>
                    <TableCell className="max-w-xs truncate">{request.reason}</TableCell>
                    <TableCell>
                      <Badge className={getStatusColor(request.status)}>{request.status}</Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      {request.status === "pending" && (
                        <div className="flex justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleApprove(request.id)}
                            title="Approve (PUT)"
                          >
                            <Check className="h-4 w-4 text-success" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleReject(request.id)}
                            title="Reject (PUT)"
                          >
                            <X className="h-4 w-4 text-destructive" />
                          </Button>
                        </div>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <LeaveRequestDialog open={dialogOpen} onClose={handleDialogClose} />
    </div>
  )
}
