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
import type { Document } from "@/lib/types"

interface DocumentDialogProps {
  open: boolean
  onClose: () => void
  document: Document | null
}

export function DocumentDialog({ open, onClose, document }: DocumentDialogProps) {
  const [loading, setLoading] = useState(false)
  const [usePatch, setUsePatch] = useState(false)
  const [formData, setFormData] = useState({
    document_type: "other",
    title: "",
    file_url: "",
    description: "",
    employee: "",
  })

  useEffect(() => {
    if (document) {
      setFormData({
        document_type: document.document_type,
        title: document.title,
        file_url: document.file_url,
        description: document.description || "",
        employee: document.employee,
      })
    } else {
      setFormData({
        document_type: "other",
        title: "",
        file_url: "",
        description: "",
        employee: "",
      })
    }
  }, [document])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      if (document) {
        // Use PUT or PATCH based on toggle
        if (usePatch) {
          await api.patchDocument(document.id, formData)
        } else {
          await api.updateDocument(document.id, formData)
        }
      } else {
        await api.createDocument(formData)
      }
      onClose()
    } catch (error) {
      console.error("[v0] Failed to save document:", error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{document ? "Edit Document" : "Upload New Document"}</DialogTitle>
          <DialogDescription>
            {document
              ? "Update document information. Use PUT for full update or PATCH for partial update."
              : "Add a new document to the library."}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {document && (
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
            <Label htmlFor="title">Title *</Label>
            <Input
              id="title"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="document_type">Document Type *</Label>
            <Select
              value={formData.document_type}
              onValueChange={(value) => setFormData({ ...formData, document_type: value })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="certificate">Certificate</SelectItem>
                <SelectItem value="contract">Contract</SelectItem>
                <SelectItem value="cv">CV</SelectItem>
                <SelectItem value="id">ID</SelectItem>
                <SelectItem value="other">Other</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="file_url">File URL *</Label>
            <Input
              id="file_url"
              type="url"
              value={formData.file_url}
              onChange={(e) => setFormData({ ...formData, file_url: e.target.value })}
              placeholder="https://example.com/document.pdf"
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
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Optional description..."
              rows={3}
            />
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? "Saving..." : document ? "Update Document" : "Upload Document"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
