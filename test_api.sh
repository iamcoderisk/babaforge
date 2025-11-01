#!/bin/bash
echo "Testing API endpoints..."
echo ""
echo "1. Test endpoint:"
curl -s http://localhost:5000/api/test | python3 -m json.tool
echo ""
