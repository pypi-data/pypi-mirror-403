import subprocess

def run_test():
    cmd = ["cargo", "test", "--test", "integration_test", "--", "--nocapture"]
    result = subprocess.run(cmd, cwd=r"e:\G\GeminiCLI\ai-test-project\CroStem_v012\cro_stem", capture_output=True, text=True)
    print("STDOUT:")
    print(result.stdout)
    print("\nSTDERR:")
    print(result.stderr)

if __name__ == "__main__":
    run_test()
