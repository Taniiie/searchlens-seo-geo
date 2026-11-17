"""
SearchLens Entry Point for Streamlit Cloud and Local Execution.
"""
import runpy

if __name__ == "__main__":
    runpy.run_module("dashboard", run_name="__main__")

