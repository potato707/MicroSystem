// API client for HR management system
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "https://api.example.com"

export class ApiClient {
  private token: string | null = null

  constructor() {
    if (typeof window !== "undefined") {
      this.token = localStorage.getItem("access_token")
    }
  }

  setToken(token: string) {
    this.token = token
    if (typeof window !== "undefined") {
      localStorage.setItem("access_token", token)
    }
  }

  clearToken() {
    this.token = null
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token")
      localStorage.removeItem("refresh_token")
    }
  }

  private async request(endpoint: string, options: RequestInit = {}) {
    const headers: HeadersInit = {
      "Content-Type": "application/json",
      ...options.headers,
    }

    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    })

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`)
    }

    return response.json()
  }

  // Auth
  async login(username: string, password: string) {
    const data = await this.request("/api/token/", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    })
    this.setToken(data.access)
    if (typeof window !== "undefined") {
      localStorage.setItem("refresh_token", data.refresh)
    }
    return data
  }

  async refreshToken() {
    const refresh = typeof window !== "undefined" ? localStorage.getItem("refresh_token") : null
    if (!refresh) throw new Error("No refresh token")

    const data = await this.request("/api/token/refresh/", {
      method: "POST",
      body: JSON.stringify({ refresh }),
    })
    this.setToken(data.access)
    return data
  }

  // Employees
  async getEmployees() {
    return this.request("/hr/employees/")
  }

  async getEmployee(id: string) {
    return this.request(`/hr/employees/${id}/`)
  }

  async createEmployee(data: any) {
    return this.request("/hr/employees/", {
      method: "POST",
      body: JSON.stringify(data),
    })
  }

  async updateEmployee(id: string, data: any) {
    return this.request(`/hr/employees/${id}/`, {
      method: "PUT",
      body: JSON.stringify(data),
    })
  }

  async patchEmployee(id: string, data: any) {
    return this.request(`/hr/employees/${id}/`, {
      method: "PATCH",
      body: JSON.stringify(data),
    })
  }

  async deleteEmployee(id: string) {
    return this.request(`/hr/employees/${id}/`, {
      method: "DELETE",
    })
  }

  // Attendance
  async getAttendance(params?: { date?: string; user_id?: string }) {
    const query = new URLSearchParams(params as any).toString()
    return this.request(`/hr/attendance/${query ? `?${query}` : ""}`)
  }

  async createAttendance(data: any) {
    return this.request("/hr/attendance/", {
      method: "POST",
      body: JSON.stringify(data),
    })
  }

  async updateAttendance(id: string, data: any) {
    return this.request(`/hr/attendance/${id}/`, {
      method: "PUT",
      body: JSON.stringify(data),
    })
  }

  async patchAttendance(id: string, data: any) {
    return this.request(`/hr/attendance/${id}/`, {
      method: "PATCH",
      body: JSON.stringify(data),
    })
  }

  async checkIn(employeeId: string) {
    return this.request(`/hr/attendance/${employeeId}/checkin/`, {
      method: "POST",
    })
  }

  async checkOut(employeeId: string) {
    return this.request(`/hr/attendance/${employeeId}/checkout/`, {
      method: "POST",
    })
  }

  // Leave Requests
  async getLeaveRequests() {
    return this.request("/hr/leave_requests/list/")
  }

  async createLeaveRequest(data: any) {
    return this.request("/hr/leave_requests/", {
      method: "POST",
      body: JSON.stringify(data),
    })
  }

  async updateLeaveRequestStatus(id: string, data: any) {
    return this.request(`/hr/leave_requests/${id}/status/`, {
      method: "PUT",
      body: JSON.stringify(data),
    })
  }

  async patchLeaveRequestStatus(id: string, data: any) {
    return this.request(`/hr/leave_requests/${id}/status/`, {
      method: "PATCH",
      body: JSON.stringify(data),
    })
  }

  // Complaints
  async getComplaints() {
    return this.request("/hr/complaints/list/")
  }

  async createComplaint(data: any) {
    return this.request("/hr/complaints/", {
      method: "POST",
      body: JSON.stringify(data),
    })
  }

  async replyToComplaint(complaintId: string, data: any) {
    return this.request(`/hr/complaints/${complaintId}/reply/`, {
      method: "POST",
      body: JSON.stringify(data),
    })
  }

  // Reimbursements
  async getReimbursements() {
    return this.request("/hr/reimbursements/")
  }

  async createReimbursement(data: any) {
    return this.request("/hr/reimbursements/create/", {
      method: "POST",
      body: JSON.stringify(data),
    })
  }

  async reviewReimbursement(id: string, data: any) {
    return this.request(`/hr/reimbursements/${id}/review/`, {
      method: "PUT",
      body: JSON.stringify(data),
    })
  }

  async patchReimbursement(id: string, data: any) {
    return this.request(`/hr/reimbursements/${id}/review/`, {
      method: "PATCH",
      body: JSON.stringify(data),
    })
  }

  // Documents
  async getDocuments() {
    return this.request("/hr/documents/")
  }

  async createDocument(data: any) {
    return this.request("/hr/documents/", {
      method: "POST",
      body: JSON.stringify(data),
    })
  }

  async updateDocument(id: number, data: any) {
    return this.request(`/hr/documents/${id}/`, {
      method: "PUT",
      body: JSON.stringify(data),
    })
  }

  async patchDocument(id: number, data: any) {
    return this.request(`/hr/documents/${id}/`, {
      method: "PATCH",
      body: JSON.stringify(data),
    })
  }

  async deleteDocument(id: number) {
    return this.request(`/hr/documents/${id}/`, {
      method: "DELETE",
    })
  }

  // Notes
  async getNotes() {
    return this.request("/hr/notes/")
  }

  async createNote(data: any) {
    return this.request("/hr/notes/", {
      method: "POST",
      body: JSON.stringify(data),
    })
  }

  async updateNote(id: number, data: any) {
    return this.request(`/hr/notes/${id}/`, {
      method: "PUT",
      body: JSON.stringify(data),
    })
  }

  async patchNote(id: number, data: any) {
    return this.request(`/hr/notes/${id}/`, {
      method: "PATCH",
      body: JSON.stringify(data),
    })
  }

  async deleteNote(id: number) {
    return this.request(`/hr/notes/${id}/`, {
      method: "DELETE",
    })
  }

  // Wallets
  async getEmployeeWallet(employeeId: string) {
    return this.request(`/hr/employees/${employeeId}/wallet/`)
  }

  async getEmployeeWalletTransactions(employeeId: string) {
    return this.request(`/hr/employees/${employeeId}/wallet/transactions/history/`)
  }

  async createWalletTransaction(employeeId: string, data: any) {
    return this.request(`/hr/employees/${employeeId}/wallet/transactions/`, {
      method: "POST",
      body: JSON.stringify(data),
    })
  }

  async getCentralWallet() {
    return this.request("/hr/central-wallet/")
  }

  async getCentralWalletTransactions() {
    return this.request("/hr/central-wallet/transactions/history/")
  }

  async createCentralWalletTransaction(data: any) {
    return this.request("/hr/central-wallet/transactions/", {
      method: "POST",
      body: JSON.stringify(data),
    })
  }
}

export const api = new ApiClient()
