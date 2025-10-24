#!/bin/bash

echo "Testing Current Status API after fix..."
echo "=========================================="
echo ""

# Test for employee string who checked in at 8:00
curl -s 'http://localhost:8000/hr/api/shift-attendance/current_status/?employee_id=e70fe696-8c4a-4f73-83a0-64c66429caab' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoyMDc2MTM1MzM2LCJpYXQiOjE3NjA3NzUzMzYsImp0aSI6ImJkMTU2NWRkNTdlZDRkNTk5NGVkNjljZTcwZDdkYmY5IiwidXNlcl9pZCI6IjIyMWMzYTQ5LThiZTktNGI0MS1iNjkwLWZlZmQwYjFjMzE3NiJ9.RL1mKYWbmnaRm9JVZaecFLwv5qTGvNoWZ3ReMpa6zKo' \
  -H 'Content-Type: application/json' | jq '.'

echo ""
echo "=========================================="
echo "Expected: has_clocked_in = true, status = 'متأخر', late_minutes = 120"
