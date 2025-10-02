"use client"

import type React from "react"
import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { api } from "@/lib/api"
import type { Reimbursement } from "@/lib/types"

interface ReimbursementReviewDialogProps {
  open: boolean
  onClose: () => void
  reimbursement: Reimbursement | null
}

export function ReimbursementReviewDialog({ open, onClose, reimbursement }: ReimbursementReviewDialogProps) {
  const [loading, setLoading] = useState(false)
  const [usePatch, setUsePatch] = useState(false)
  const [formData, setFormData] = useState({
    status: "approved",
    admin_comment: "",
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!reimbursement) return

    setLoading(true)
    try {
      // Use PUT or PATCH based on toggle
      if (usePatch) {
        await api.patchReimbursement(reimbursement.id, formData)
      } else {
        await api.reviewReimbursement(reimbursement.id, formData)
      }
      onClose()
    } catch (error) {
      console.error("[v0] Failed to review reimbursement:", error)
    } finally {
      setLoading(false)
    }
  }

  if (!reimbursement) return null

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Review Reimbursement Request</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div className="flex items-center gap-2 p-3 bg-muted rounded-lg">
            <Label htmlFor="update-method" className="text-sm">
              Update Method:
            </Label>
            <Select value={usePatch ? "patch" : "put"} onValueChange={(value) => setUsePatch(value === "patch")}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="put">PUT</SelectItem>
                <SelectItem value="patch">PATCH</SelectItem>
              </SelectContent>
            </Select>
            <span className="text-xs text-muted-foreground">{usePatch ? "Partial update" : "Full update"}</span>
          </div>

          <div className="bg-muted p-4 rounded-lg space-y-2">
            <div>
              <span className="text-sm font-medium">Amount:</span>
              <span className="text-sm ml-2">${reimbursement.amount}</span>
            </div>
            <div>
              <span className="text-sm font-medium">Description:</span>
              <p className="text-sm text-muted-foreground mt-1">{reimbursement.description}</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="status">Decision *</Label>
              <Select value={formData.status} onValueChange={(value) => setFormData({ ...formData, status: value })}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="approved">Approve</SelectItem>
                  <SelectItem value="rejected">Reject</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="admin_comment">Comment</Label>
              <Textarea
                id="admin_comment"
                value={formData.admin_comment}
                onChange={(e) => setFormData({ ...formData, admin_comment: e.target.value })}
                placeholder="Add a comment (optional)..."
                rows={3}
              />
            </div>

            <div className="flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={onClose}>
                Cancel
              </Button>
              <Button type="submit" disabled={loading}>
                {loading ? "Submitting..." : "Submit Review"}
              </Button>
            </div>
          </form>
        </div>
      </DialogContent>
    </Dialog>
  )
}
