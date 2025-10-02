"use client"

import type React from "react"
import { useState, useEffect } from "react"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { api } from "@/lib/api"
import type { Attendance } from "@/lib/types"

interface AttendanceDialogProps {
  open: boolean
  onClose: () => void
  attendance: Attendance | null
}

export function AttendanceDialog({ open, onClose, attendance }: AttendanceDialogProps) {
  const [loading, setLoading] = useState(false)
  const [usePatch, setUsePatch] = useState(false)
  const [formData, setFormData] = useState({
    date: new Date().toISOString().split("T")[0],
    check_in: "",
    check_out: "",
    status: "present",
    paid: false,
  })

  useEffect(() => {
    if (attendance) {
      setFormData({
        date: attendance.date,
        check_in: attendance.check_in || "",
        check_out: attendance.check_out || "",
        status: attendance.status,
        paid: attendance.paid,
      })
    } else {
      setFormData({
        date: new Date().toISOString().split("T")[0],
        check_in: "",
        check_out: "",
        status: "present",
        paid: false,
      })
    }
  }, [attendance])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      if (attendance) {
        // Use PUT or PATCH based on toggle
        if (usePatch) {
          await api.patchAttendance(attendance.id, formData)
        } else {
          await api.updateAttendance(attendance.id, formData)
        }
      } else {
        await api.createAttendance(formData)
      }
      onClose()
    } catch (error) {
      console.error("[v0] Failed to save attendance:", error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{attendance ? "Edit Attendance" : "Add Attendance Record"}</DialogTitle>
          <DialogDescription>
            {attendance
              ? "Update attendance record. Use PUT for full update or PATCH for partial update."
              : "Create a new attendance record."}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {attendance && (
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
            <Label htmlFor="date">Date *</Label>
            <Input
              id="date"
              type="date"
              value={formData.date}
              onChange={(e) => setFormData({ ...formData, date: e.target.value })}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="check_in">Check In Time</Label>
            <Input
              id="check_in"
              type="time"
              value={formData.check_in}
              onChange={(e) => setFormData({ ...formData, check_in: e.target.value })}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="check_out">Check Out Time</Label>
            <Input
              id="check_out"
              type="time"
              value={formData.check_out}
              onChange={(e) => setFormData({ ...formData, check_out: e.target.value })}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="status">Status *</Label>
            <Select value={formData.status} onValueChange={(value) => setFormData({ ...formData, status: value })}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="present">Present</SelectItem>
                <SelectItem value="absent">Absent</SelectItem>
                <SelectItem value="late">Late</SelectItem>
                <SelectItem value="on_leave">On Leave</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center space-x-2">
            <Checkbox
              id="paid"
              checked={formData.paid}
              onCheckedChange={(checked) => setFormData({ ...formData, paid: checked as boolean })}
            />
            <Label htmlFor="paid" className="cursor-pointer">
              Paid
            </Label>
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? "Saving..." : attendance ? "Update Record" : "Create Record"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
