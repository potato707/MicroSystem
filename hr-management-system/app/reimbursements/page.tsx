"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Plus } from "lucide-react"
import { api } from "@/lib/api"
import type { Reimbursement } from "@/lib/types"
import { ReimbursementDialog } from "@/components/reimbursement-dialog"
import { ReimbursementReviewDialog } from "@/components/reimbursement-review-dialog"

export default function ReimbursementsPage() {
  const [reimbursements, setReimbursements] = useState<Reimbursement[]>([])
  const [loading, setLoading] = useState(true)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [reviewDialogOpen, setReviewDialogOpen] = useState(false)
  const [selectedReimbursement, setSelectedReimbursement] = useState<Reimbursement | null>(null)

  const fetchReimbursements = async () => {
    try {
      const data = await api.getReimbursements()
      setReimbursements(data)
    } catch (error) {
      console.error("[v0] Failed to fetch reimbursements:", error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchReimbursements()
  }, [])

  const handleReview = (reimbursement: Reimbursement) => {
    setSelectedReimbursement(reimbursement)
    setReviewDialogOpen(true)
  }

  const handleDialogClose = () => {
    setDialogOpen(false)
    fetchReimbursements()
  }

  const handleReviewDialogClose = () => {
    setReviewDialogOpen(false)
    setSelectedReimbursement(null)
    fetchReimbursements()
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
          <h1 className="text-3xl font-bold text-foreground">Reimbursements</h1>
          <p className="text-muted-foreground mt-2">Manage employee reimbursement requests</p>
        </div>
        <Button onClick={() => setDialogOpen(true)} className="gap-2">
          <Plus className="h-4 w-4" />
          New Request
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Reimbursement Requests</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-center text-muted-foreground py-8">Loading reimbursements...</p>
          ) : reimbursements.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">No reimbursement requests found</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Employee</TableHead>
                  <TableHead>Amount</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {reimbursements.map((reimbursement) => (
                  <TableRow key={reimbursement.id}>
                    <TableCell className="font-medium">{reimbursement.employee}</TableCell>
                    <TableCell>${reimbursement.amount}</TableCell>
                    <TableCell className="max-w-xs truncate">{reimbursement.description}</TableCell>
                    <TableCell>
                      <Badge className={getStatusColor(reimbursement.status)}>{reimbursement.status}</Badge>
                    </TableCell>
                    <TableCell>{new Date(reimbursement.created_at).toLocaleDateString()}</TableCell>
                    <TableCell className="text-right">
                      {reimbursement.status === "pending" && (
                        <Button variant="outline" size="sm" onClick={() => handleReview(reimbursement)}>
                          Review
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <ReimbursementDialog open={dialogOpen} onClose={handleDialogClose} />
      <ReimbursementReviewDialog
        open={reviewDialogOpen}
        onClose={handleReviewDialogClose}
        reimbursement={selectedReimbursement}
      />
    </div>
  )
}
