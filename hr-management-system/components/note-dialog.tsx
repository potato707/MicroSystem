"use client"

import type React from "react"
import { useState, useEffect } from "react"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { api } from "@/lib/api"
import type { Note } from "@/lib/types"

interface NoteDialogProps {
  open: boolean
  onClose: () => void
  note: Note | null
}

export function NoteDialog({ open, onClose, note }: NoteDialogProps) {
  const [loading, setLoading] = useState(false)
  const [usePatch, setUsePatch] = useState(false)
  const [formData, setFormData] = useState({
    note: "",
    employee: "",
    created_by: "",
  })

  useEffect(() => {
    if (note) {
      setFormData({
        note: note.note,
        employee: note.employee,
        created_by: note.created_by,
      })
    } else {
      setFormData({
        note: "",
        employee: "",
        created_by: "",
      })
    }
  }, [note])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      if (note) {
        // Use PUT or PATCH based on toggle
        if (usePatch) {
          await api.patchNote(note.id, formData)
        } else {
          await api.updateNote(note.id, formData)
        }
      } else {
        await api.createNote(formData)
      }
      onClose()
    } catch (error) {
      console.error("[v0] Failed to save note:", error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{note ? "Edit Note" : "Add New Note"}</DialogTitle>
          <DialogDescription>
            {note
              ? "Update note information. Use PUT for full update or PATCH for partial update."
              : "Create a new note for an employee."}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {note && (
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
          )}

          <div className="space-y-2">
            <Label htmlFor="note">Note *</Label>
            <Textarea
              id="note"
              value={formData.note}
              onChange={(e) => setFormData({ ...formData, note: e.target.value })}
              placeholder="Write your note here..."
              rows={5}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="employee">Employee ID *</Label>
            <Input
              id="employee"
              value={formData.employee}
              onChange={(e) => setFormData({ ...formData, employee: e.target.value })}
              placeholder="Employee UUID"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="created_by">Created By (User ID) *</Label>
            <Input
              id="created_by"
              value={formData.created_by}
              onChange={(e) => setFormData({ ...formData, created_by: e.target.value })}
              placeholder="User UUID"
              required
            />
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? "Saving..." : note ? "Update Note" : "Create Note"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
