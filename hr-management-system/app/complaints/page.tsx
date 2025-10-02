"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Plus, MessageSquare } from "lucide-react"
import { api } from "@/lib/api"
import type { Complaint } from "@/lib/types"
import { ComplaintDialog } from "@/components/complaint-dialog"
import { ComplaintDetailDialog } from "@/components/complaint-detail-dialog"

export default function ComplaintsPage() {
  const [complaints, setComplaints] = useState<Complaint[]>([])
  const [loading, setLoading] = useState(true)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [detailDialogOpen, setDetailDialogOpen] = useState(false)
  const [selectedComplaint, setSelectedComplaint] = useState<Complaint | null>(null)

  const fetchComplaints = async () => {
    try {
      const data = await api.getComplaints()
      setComplaints(data)
    } catch (error) {
      console.error("[v0] Failed to fetch complaints:", error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchComplaints()
  }, [])

  const handleViewDetails = (complaint: Complaint) => {
    setSelectedComplaint(complaint)
    setDetailDialogOpen(true)
  }

  const handleDialogClose = () => {
    setDialogOpen(false)
    fetchComplaints()
  }

  const handleDetailDialogClose = () => {
    setDetailDialogOpen(false)
    setSelectedComplaint(null)
    fetchComplaints()
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      open: "bg-warning/20 text-warning",
      in_review: "bg-primary/20 text-primary",
      answered: "bg-success/20 text-success",
      closed: "bg-muted text-muted-foreground",
    }
    return colors[status] || "bg-muted text-muted-foreground"
  }

  const getUrgencyColor = (urgency: string) => {
    const colors: Record<string, string> = {
      low: "bg-muted text-muted-foreground",
      medium: "bg-warning/20 text-warning",
      high: "bg-destructive/20 text-destructive",
    }
    return colors[urgency] || "bg-muted text-muted-foreground"
  }

  return (
    <div className="p-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Complaints</h1>
          <p className="text-muted-foreground mt-2">Manage employee complaints and feedback</p>
        </div>
        <Button onClick={() => setDialogOpen(true)} className="gap-2">
          <Plus className="h-4 w-4" />
          New Complaint
        </Button>
      </div>

      <div className="grid gap-6">
        {loading ? (
          <Card>
            <CardContent className="py-8">
              <p className="text-center text-muted-foreground">Loading complaints...</p>
            </CardContent>
          </Card>
        ) : complaints.length === 0 ? (
          <Card>
            <CardContent className="py-8">
              <p className="text-center text-muted-foreground">No complaints found</p>
            </CardContent>
          </Card>
        ) : (
          complaints.map((complaint) => (
            <Card key={complaint.id} className="hover:bg-card/80 transition-colors cursor-pointer">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-lg">{complaint.title}</CardTitle>
                    <p className="text-sm text-muted-foreground mt-1">By {complaint.employee_name}</p>
                  </div>
                  <div className="flex gap-2">
                    <Badge className={getStatusColor(complaint.status)}>{complaint.status}</Badge>
                    <Badge className={getUrgencyColor(complaint.urgency)}>{complaint.urgency}</Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground line-clamp-2 mb-4">{complaint.description}</p>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    <span>{new Date(complaint.created_at).toLocaleDateString()}</span>
                    <span className="flex items-center gap-1">
                      <MessageSquare className="h-3 w-3" />
                      {complaint.replies?.length || 0} replies
                    </span>
                  </div>
                  <Button variant="outline" size="sm" onClick={() => handleViewDetails(complaint)}>
                    View Details
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      <ComplaintDialog open={dialogOpen} onClose={handleDialogClose} />
      <ComplaintDetailDialog open={detailDialogOpen} onClose={handleDetailDialogClose} complaint={selectedComplaint} />
    </div>
  )
}
