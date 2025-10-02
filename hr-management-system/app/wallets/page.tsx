"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { WalletIcon, Plus } from "lucide-react"
import { api } from "@/lib/api"
import type { Wallet, WalletTransaction } from "@/lib/types"

export default function WalletsPage() {
  const [centralWallet, setCentralWallet] = useState<Wallet | null>(null)
  const [centralTransactions, setCentralTransactions] = useState<WalletTransaction[]>([])
  const [loading, setLoading] = useState(true)

  const fetchWalletData = async () => {
    try {
      const [wallet, transactions] = await Promise.all([api.getCentralWallet(), api.getCentralWalletTransactions()])
      setCentralWallet(wallet)
      setCentralTransactions(transactions)
    } catch (error) {
      console.error("[v0] Failed to fetch wallet data:", error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchWalletData()
  }, [])

  const getTransactionColor = (type: string) => {
    return type === "deposit" ? "text-success" : "text-destructive"
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-foreground">Wallets</h1>
        <p className="text-muted-foreground mt-2">Manage central and employee wallets</p>
      </div>

      <Tabs defaultValue="central" className="space-y-6">
        <TabsList>
          <TabsTrigger value="central">Central Wallet</TabsTrigger>
          <TabsTrigger value="employees">Employee Wallets</TabsTrigger>
        </TabsList>

        <TabsContent value="central" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <WalletIcon className="h-5 w-5" />
                Central Wallet Balance
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <p className="text-muted-foreground">Loading...</p>
              ) : (
                <div className="text-4xl font-bold text-foreground">${centralWallet?.balance || "0.00"}</div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Transaction History</CardTitle>
              <Button size="sm" className="gap-2">
                <Plus className="h-4 w-4" />
                New Transaction
              </Button>
            </CardHeader>
            <CardContent>
              {loading ? (
                <p className="text-center text-muted-foreground py-8">Loading transactions...</p>
              ) : centralTransactions.length === 0 ? (
                <p className="text-center text-muted-foreground py-8">No transactions found</p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead className="text-right">Amount</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {centralTransactions.map((transaction) => (
                      <TableRow key={transaction.id}>
                        <TableCell>{new Date(transaction.created_at).toLocaleDateString()}</TableCell>
                        <TableCell>
                          <Badge variant="outline">{transaction.transaction_type}</Badge>
                        </TableCell>
                        <TableCell>{transaction.description}</TableCell>
                        <TableCell
                          className={`text-right font-medium ${getTransactionColor(transaction.transaction_type)}`}
                        >
                          {transaction.transaction_type === "deposit" ? "+" : "-"}${transaction.amount}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="employees">
          <Card>
            <CardHeader>
              <CardTitle>Employee Wallets</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-center text-muted-foreground py-8">
                Select an employee from the Employees page to view their wallet
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
