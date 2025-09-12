import subprocess

def run_pytest():
    print("Running pytest on all tests in the 'tests' folder...")
    result = subprocess.run(["pytest", "tests/"], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print("Some tests failed. See above for details.")
    else:
        print("All pytest tests passed successfully.")

if __name__ == "__main__":
    run_pytest()