import os
import sys
import streamlit.web.cli as stcli

if __name__ == "__main__":
    # यह बिना ब्राउज़र टर्मिनल खोले सीधे आपकी मुख्य स्ट्रीमलिट ऐप को रन करेगा
    sys.argv = ["streamlit", "run", "app.py", "--server.headless=true", "--server.port=8501"]
    sys.exit(stcli.main())
