import os
import sys
import time

from gcp_mysql import MySQLService

try:
    from dotenv import load_dotenv
    load_dotenv(".env.local")
except ImportError:
    pass

CONNECT_RETRIES = 3
CONNECT_RETRY_DELAY = 2.0


def get_db():
    GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
    GCP_SECRET_ID = os.getenv("GCP_SECRET_ID")  
    if not GCP_PROJECT_ID or not GCP_SECRET_ID:
        raise ValueError("GCP_PROJECT_ID and GCP_SECRET_ID must be set")
    db = MySQLService.from_gcp_secret(project_id=GCP_PROJECT_ID, secret_id=GCP_SECRET_ID)

    connected = False
    for attempt in range(1, CONNECT_RETRIES + 1):
        try:
            if db.test_connection():
                print("Connected successfully!")
                connected = True
                break
        except Exception as e:
            if attempt < CONNECT_RETRIES:
                print(f"Attempt {attempt}/{CONNECT_RETRIES} failed: {e}", file=sys.stderr)
                print(f"Retrying in {CONNECT_RETRY_DELAY}s...", file=sys.stderr)
                time.sleep(CONNECT_RETRY_DELAY)
            else:
                _print_connection_help()
                raise

    if connected:
        results = db.execute_query("SELECT * FROM meetings LIMIT 1")
        for row in results:
            print(row)

    return db


def _print_connection_help():
    print(
        "\n--- Connection failed. Check:\n"
        "  1. Start proxy:\n"
        "     ./infra/local/run-cloud-sql-proxy.sh --build-environment docker --config infra/local/cloud-sql.json --detach\n"
        "  2. Verify proxy is running: docker ps\n"
        "  3. Check proxy logs: cd infra/local/docker && docker compose logs -f\n"
        "  4. Verify port matches: check infra/local/cloud-sql.json and MYSQL_PORT env var\n"
        "  5. Or use CLI mode: ./infra/local/run-cloud-sql-proxy.sh --config infra/local/cloud-sql.json\n",
        file=sys.stderr,
    )


if __name__ == "__main__":
    get_db()