#!/bin/bash
cd /app/auto-mcp-upload
python3 scripts/mcp_local_tester.py --command /app/venv/bin/python3 --args "-m cmcp.main --test-mode" 2>&1 | tail -100
