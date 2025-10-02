"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Plus, Edit, Trash2 } from "lucide-react"
import { api } from "@/lib/api"
import type { Employee } from "@/lib/types"
import { EmployeeDialog } from "@/components/employee-dialog"

export default function EmployeesPage() {
  const [employees, setEmployees] = useState<Employee[]>([])
  const [loading, setLoading] = useState(true)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [selectedEmployee, setSelectedEmployee] = useState<Employee | null>(null)

  const fetchEmployees = async () => {
    try {
      const data = await api.getEmployees()
      setEmployees(data)
    } catch (error) {
      console.error("[v0] Failed to fetch employees:", error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchEmployees()
  }, [])

  const handleEdit = (employee: Employee) => {
    setSelectedEmployee(employee)
    setDialogOpen(true)
  }

  const handleDelete = async (id: string) => {
    if (confirm("Are you sure you want to delete this employee?")) {
      try {
        await api.deleteEmployee(id)
        fetchEmployees()
      } catch (error) {
        console.error("[v0] Failed to delete employee:", error)
      }
    }
  }

  const handleDialogClose = () => {
    setDialogOpen(false)
    setSelectedEmployee(null)
    fetchEmployees()
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      active: "bg-success/20 text-success",
      vacation: "bg-warning/20 text-warning",
      resigned: "bg-muted text-muted-foreground",
      terminated: "bg-destructive/20 text-destructive",
      probation: "bg-primary/20 text-primary",
    }
    return colors[status] || "bg-muted text-muted-foreground"
  }

  return (
    <div className="p-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Employees</h1>
          <p className="text-muted-foreground mt-2">Manage your organization's employees</p>
        </div>
        <Button onClick={() => setDialogOpen(true)} className="gap-2">
          <Plus className="h-4 w-4" />
          Add Employee
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Employee List</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-center text-muted-foreground py-8">Loading employees...</p>
          ) : employees.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">No employees found</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Position</TableHead>
                  <TableHead>Department</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {employees.map((employee) => (
                  <TableRow key={employee.id}>
                    <TableCell className="font-medium">{employee.name}</TableCell>
                    <TableCell>{employee.position}</TableCell>
                    <TableCell>{employee.department}</TableCell>
                    <TableCell>{employee.email}</TableCell>
                    <TableCell>
                      <Badge className={getStatusColor(employee.status)}>{employee.status}</Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button variant="ghost" size="icon" onClick={() => handleEdit(employee)}>
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="icon" onClick={() => handleDelete(employee.id)}>
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

      <EmployeeDialog open={dialogOpen} onClose={handleDialogClose} employee={selectedEmployee} />
    </div>
  )
}
