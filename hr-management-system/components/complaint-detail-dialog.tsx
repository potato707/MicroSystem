"use client"

import type React from "react"
import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { api } from "@/lib/api"
import type { Complaint } from "@/lib/types"

interface ComplaintDetailDialogProps {
  open: boolean
  onClose: () => void
  complaint: Complaint | null
}

export function ComplaintDetailDialog({ open, onClose, complaint }: ComplaintDetailDialogProps) {
  const [loading, setLoading] = useState(false)
  const [replyMessage, setReplyMessage] = useState("")

  const handleReply = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!complaint) return

    setLoading(true)
    try {
      await api.replyToComplaint(complaint.id, {
        message: replyMessage,
        attachment_links: [],
      })
      setReplyMessage("")
      onClose()
    } catch (error) {
      console.error("[v0] Failed to reply to complaint:", error)
    } finally {
      setLoading(false)
    }
  }

  if (!complaint) return null

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{complaint.title}</DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          <div className="flex gap-2">
            <Badge>{complaint.status}</Badge>
            <Badge>{complaint.urgency}</Badge>
          </div>

          <div>
            <h3 className="text-sm font-medium mb-2">Description</h3>
            <p className="text-sm text-muted-foreground">{complaint.description}</p>
          </div>

          <div>
            <h3 className="text-sm font-medium mb-2">Submitted by</h3>
            <p className="text-sm text-muted-foreground">{complaint.employee_name}</p>
            <p className="text-xs text-muted-foreground">{new Date(complaint.created_at).toLocaleString()}</p>
          </div>

          {complaint.replies && complaint.replies.length > 0 && (
            <div>
              <h3 className="text-sm font-medium mb-3">Replies</h3>
              <div className="space-y-3">
                {complaint.replies.map((reply: any) => (
                  <div key={reply.id} className="bg-muted p-3 rounded-lg">
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-sm font-medium">{reply.user_name}</span>
                      <span className="text-xs text-muted-foreground">
                        {new Date(reply.created_at).toLocaleString()}
                      </span>
                    </div>
                    <p className="text-sm text-muted-foreground">{reply.message}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          <form onSubmit={handleReply} className="space-y-3">
            <Textarea
              value={replyMessage}
              onChange={(e) => setReplyMessage(e.target.value)}
              placeholder="Write a reply..."
              rows={3}
              required
            />
            <div className="flex justify-end">
              <Button type="submit" disabled={loading}>
                {loading ? "Sending..." : "Send Reply"}
              </Button>
            </div>
          </form>
        </div>
      </DialogContent>
    </Dialog>
  )
}
