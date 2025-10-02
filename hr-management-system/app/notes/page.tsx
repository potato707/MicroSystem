"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Plus, Edit, Trash2 } from "lucide-react"
import { api } from "@/lib/api"
import type { Note } from "@/lib/types"
import { NoteDialog } from "@/components/note-dialog"

export default function NotesPage() {
  const [notes, setNotes] = useState<Note[]>([])
  const [loading, setLoading] = useState(true)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [selectedNote, setSelectedNote] = useState<Note | null>(null)

  const fetchNotes = async () => {
    try {
      const data = await api.getNotes()
      setNotes(data)
    } catch (error) {
      console.error("[v0] Failed to fetch notes:", error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchNotes()
  }, [])

  const handleEdit = (note: Note) => {
    setSelectedNote(note)
    setDialogOpen(true)
  }

  const handleDelete = async (id: number) => {
    if (confirm("Are you sure you want to delete this note?")) {
      try {
        await api.deleteNote(id)
        fetchNotes()
      } catch (error) {
        console.error("[v0] Failed to delete note:", error)
      }
    }
  }

  const handleDialogClose = () => {
    setDialogOpen(false)
    setSelectedNote(null)
    fetchNotes()
  }

  return (
    <div className="p-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Notes</h1>
          <p className="text-muted-foreground mt-2">Manage employee notes and observations</p>
        </div>
        <Button onClick={() => setDialogOpen(true)} className="gap-2">
          <Plus className="h-4 w-4" />
          Add Note
        </Button>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {loading ? (
          <Card>
            <CardContent className="py-8">
              <p className="text-center text-muted-foreground">Loading notes...</p>
            </CardContent>
          </Card>
        ) : notes.length === 0 ? (
          <Card>
            <CardContent className="py-8">
              <p className="text-center text-muted-foreground">No notes found</p>
            </CardContent>
          </Card>
        ) : (
          notes.map((note) => (
            <Card key={note.id}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <CardTitle className="text-base">Note #{note.id}</CardTitle>
                  <div className="flex gap-1">
                    <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => handleEdit(note)}>
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => handleDelete(note.id)}>
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-3 line-clamp-3">{note.note}</p>
                <div className="text-xs text-muted-foreground">
                  <p>Employee: {note.employee}</p>
                  <p>Created: {new Date(note.created_date).toLocaleDateString()}</p>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      <NoteDialog open={dialogOpen} onClose={handleDialogClose} note={selectedNote} />
    </div>
  )
}
