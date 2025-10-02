export interface Employee {
  id: string
  name: string
  position: string
  department: string
  hire_date: string
  salary: string
  status: "active" | "vacation" | "resigned" | "terminated" | "probation"
  phone: string
  email: string
  address: string
  emergency_contact: string
  profile_picture?: string
  username: string
  role: string
  payroll_time_left: string
}

export interface Attendance {
  id: string
  employee: string
  employee_name: string
  date: string
  check_in?: string
  check_out?: string
  status: "present" | "absent" | "late" | "on_leave"
  paid: boolean
}

export interface LeaveRequest {
  id: string
  employee: string
  employee_name: string
  start_date: string
  end_date: string
  reason: string
  status: "pending" | "approved" | "rejected"
  created_at: string
  updated_at: string
}

export interface Complaint {
  id: string
  employee: string
  employee_name: string
  title: string
  description: string
  status: "open" | "in_review" | "answered" | "closed"
  urgency: "low" | "medium" | "high"
  created_at: string
  updated_at: string
  attachments: any[]
  replies: any[]
}

export interface Reimbursement {
  id: string
  employee: string
  amount: string
  description: string
  status: "pending" | "approved" | "rejected"
  admin_comment?: string
  created_at: string
  updated_at: string
  attachments: any[]
}

export interface Document {
  id: number
  document_type: "certificate" | "contract" | "cv" | "id" | "other"
  title: string
  file_url: string
  upload_date: string
  description?: string
  employee: string
}

export interface Note {
  id: number
  note: string
  created_date: string
  employee: string
  created_by: string
}

export interface Wallet {
  id: number
  employee?: string
  balance: string
  transactions: WalletTransaction[]
}

export interface WalletTransaction {
  id: number
  transaction_type: "deposit" | "withdrawal"
  amount: string
  description: string
  created_at: string
}
