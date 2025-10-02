"use client"

import type React from "react"
import { useState, useEffect } from "react"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { api } from "@/lib/api"
import type { Employee } from "@/lib/types"

interface EmployeeDialogProps {
  open: boolean
  onClose: () => void
  employee: Employee | null
}

export function EmployeeDialog({ open, onClose, employee }: EmployeeDialogProps) {
  const [loading, setLoading] = useState(false)
  const [usePatch, setUsePatch] = useState(false)
  const [formData, setFormData] = useState({
    name: "",
    position: "",
    department: "",
    hire_date: "",
    salary: "",
    status: "active",
    phone: "",
    email: "",
    address: "",
    emergency_contact: "",
    username: "",
    password: "",
    role: "employee",
  })

  useEffect(() => {
    if (employee) {
      setFormData({
        name: employee.name,
        position: employee.position,
        department: employee.department,
        hire_date: employee.hire_date,
        salary: employee.salary,
        status: employee.status,
        phone: employee.phone,
        email: employee.email,
        address: employee.address,
        emergency_contact: employee.emergency_contact,
        username: employee.username,
        password: "",
        role: employee.role,
      })
    } else {
      setFormData({
        name: "",
        position: "",
        department: "",
        hire_date: "",
        salary: "",
        status: "active",
        phone: "",
        email: "",
        address: "",
        emergency_contact: "",
        username: "",
        password: "",
        role: "employee",
      })
    }
  }, [employee])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      if (employee) {
        // Use PUT or PATCH based on toggle
        if (usePatch) {
          await api.patchEmployee(employee.id, formData)
        } else {
          await api.updateEmployee(employee.id, formData)
        }
      } else {
        await api.createEmployee(formData)
      }
      onClose()
    } catch (error) {
      console.error("[v0] Failed to save employee:", error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{employee ? "Edit Employee" : "Add New Employee"}</DialogTitle>
          <DialogDescription>
            {employee
              ? "Update employee information. Use PUT for full update or PATCH for partial update."
              : "Fill in the employee details below."}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {employee && (
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

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="name">Name *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="position">Position *</Label>
              <Input
                id="position"
                value={formData.position}
                onChange={(e) => setFormData({ ...formData, position: e.target.value })}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="department">Department *</Label>
              <Input
                id="department"
                value={formData.department}
                onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="hire_date">Hire Date *</Label>
              <Input
                id="hire_date"
                type="date"
                value={formData.hire_date}
                onChange={(e) => setFormData({ ...formData, hire_date: e.target.value })}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="salary">Salary *</Label>
              <Input
                id="salary"
                type="number"
                step="0.01"
                value={formData.salary}
                onChange={(e) => setFormData({ ...formData, salary: e.target.value })}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="status">Status *</Label>
              <Select value={formData.status} onValueChange={(value) => setFormData({ ...formData, status: value })}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="vacation">Vacation</SelectItem>
                  <SelectItem value="resigned">Resigned</SelectItem>
                  <SelectItem value="terminated">Terminated</SelectItem>
                  <SelectItem value="probation">Probation</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="phone">Phone *</Label>
              <Input
                id="phone"
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">Email *</Label>
              <Input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="username">Username *</Label>
              <Input
                id="username"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password {!employee && "*"}</Label>
              <Input
                id="password"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                required={!employee}
                placeholder={employee ? "Leave blank to keep current" : ""}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="role">Role *</Label>
              <Select value={formData.role} onValueChange={(value) => setFormData({ ...formData, role: value })}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="employee">Employee</SelectItem>
                  <SelectItem value="manager">Manager</SelectItem>
                  <SelectItem value="admin">Admin</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="emergency_contact">Emergency Contact *</Label>
              <Input
                id="emergency_contact"
                value={formData.emergency_contact}
                onChange={(e) => setFormData({ ...formData, emergency_contact: e.target.value })}
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="address">Address *</Label>
            <Input
              id="address"
              value={formData.address}
              onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              required
            />
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? "Saving..." : employee ? "Update Employee" : "Create Employee"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
