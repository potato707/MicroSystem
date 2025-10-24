#!/bin/bash

# Test Employee Dashboard Stats API with shift schedule integration

echo "Testing Employee Dashboard Stats API..."
echo "========================================"
echo ""

curl -s 'http://localhost:8000/hr/employee-dashboard-stats/' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoyMDc2MTM1MzM2LCJpYXQiOjE3NjA3NzUzMzYsImp0aSI6ImJkMTU2NWRkNTdlZDRkNTk5NGVkNjljZTcwZDdkYmY5IiwidXNlcl9pZCI6IjIyMWMzYTQ5LThiZTktNGI0MS1iNjkwLWZlZmQwYjFjMzE3NiJ9.RL1mKYWbmnaRm9JVZaecFLwv5qTGvNoWZ3ReMpa6zKo' \
  -H 'Content-Type: application/json' | jq '.'

echo ""
echo "========================================"
echo "Expected behavior:"
echo "- If employee checked in after 6:15 AM → status: 'late'"
echo "- If employee checked in before 6:15 AM → status: 'present'"
echo "- late_minutes should show the actual delay"
