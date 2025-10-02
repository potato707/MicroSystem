"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Plus, Edit, Trash2, ExternalLink } from "lucide-react"
import { api } from "@/lib/api"
import type { Document } from "@/lib/types"
import { DocumentDialog } from "@/components/document-dialog"

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null)

  const fetchDocuments = async () => {
    try {
      const data = await api.getDocuments()
      setDocuments(data)
    } catch (error) {
      console.error("[v0] Failed to fetch documents:", error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDocuments()
  }, [])

  const handleEdit = (document: Document) => {
    setSelectedDocument(document)
    setDialogOpen(true)
  }

  const handleDelete = async (id: number) => {
    if (confirm("Are you sure you want to delete this document?")) {
      try {
        await api.deleteDocument(id)
        fetchDocuments()
      } catch (error) {
        console.error("[v0] Failed to delete document:", error)
      }
    }
  }

  const handleDialogClose = () => {
    setDialogOpen(false)
    setSelectedDocument(null)
    fetchDocuments()
  }

  const getDocumentTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      certificate: "bg-success/20 text-success",
      contract: "bg-primary/20 text-primary",
      cv: "bg-accent/20 text-accent",
      id: "bg-warning/20 text-warning",
      other: "bg-muted text-muted-foreground",
    }
    return colors[type] || "bg-muted text-muted-foreground"
  }

  return (
    <div className="p-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Documents</h1>
          <p className="text-muted-foreground mt-2">Manage employee documents and files</p>
        </div>
        <Button onClick={() => setDialogOpen(true)} className="gap-2">
          <Plus className="h-4 w-4" />
          Upload Document
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Document Library</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-center text-muted-foreground py-8">Loading documents...</p>
          ) : documents.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">No documents found</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Title</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Employee</TableHead>
                  <TableHead>Upload Date</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {documents.map((document) => (
                  <TableRow key={document.id}>
                    <TableCell className="font-medium">{document.title}</TableCell>
                    <TableCell>
                      <Badge className={getDocumentTypeColor(document.document_type)}>{document.document_type}</Badge>
                    </TableCell>
                    <TableCell>{document.employee}</TableCell>
                    <TableCell>{new Date(document.upload_date).toLocaleDateString()}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button variant="ghost" size="icon" asChild>
                          <a href={document.file_url} target="_blank" rel="noopener noreferrer">
                            <ExternalLink className="h-4 w-4" />
                          </a>
                        </Button>
                        <Button variant="ghost" size="icon" onClick={() => handleEdit(document)}>
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="icon" onClick={() => handleDelete(document.id)}>
                          <Trash2 className="h-4 w-4 text-destructive" />
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

      <DocumentDialog open={dialogOpen} onClose={handleDialogClose} document={selectedDocument} />
    </div>
  )
}
