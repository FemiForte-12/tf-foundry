import psycopg2
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import random

# Database connection parameters
DB_PARAMS = {
    'host': 'your-aurora-cluster-endpoint',  # Replace with your Aurora endpoint
    'database': 'application_db',
    'user': 'dbadmin',
    'password': 'your-password'  # Replace with your actual password
}

# Test query that generates CPU load
CPU_INTENSIVE_QUERY = """
WITH RECURSIVE fibonacci(n, fib_n, next_fib_n) AS (
    SELECT 1, 0::numeric, 1::numeric
    UNION ALL
    SELECT n + 1, next_fib_n, fib_n + next_fib_n
    FROM fibonacci
    WHERE n < 35
)
SELECT sum(fib_n) FROM fibonacci;
"""

# Test query that holds connections
SIMPLE_QUERY = "SELECT pg_sleep(5);"

def execute_cpu_intensive_query(thread_id):
    """Execute CPU intensive query"""
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        print(f"Thread {thread_id}: Executing CPU intensive query")
        cur.execute(CPU_INTENSIVE_QUERY)
        cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error in thread {thread_id}: {str(e)}")

def hold_connection(thread_id):
    """Hold a connection for a period of time"""
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        print(f"Thread {thread_id}: Holding connection")
        cur.execute(SIMPLE_QUERY)
        cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error in thread {thread_id}: {str(e)}")

def test_cpu_scaling():
    """Test CPU-based autoscaling"""
    print("Starting CPU load test...")
    with ThreadPoolExecutor(max_workers=20) as executor:
        for i in range(50):  # Launch 50 CPU-intensive queries
            executor.submit(execute_cpu_intensive_query, i)
            time.sleep(0.5)  # Small delay between launches

def test_connection_scaling():
    """Test connection-based autoscaling"""
    print("Starting connection load test...")
    with ThreadPoolExecutor(max_workers=150) as executor:
        for i in range(150):  # Create 150 concurrent connections
            executor.submit(hold_connection, i)
            time.sleep(0.1)  # Small delay between launches

def main():
    while True:
        print("\nAurora PostgreSQL Load Testing Menu:")
        print("1. Test CPU-based autoscaling")
        print("2. Test connection-based autoscaling")
        print("3. Run both tests")
        print("4. Exit")
        
        choice = input("Select an option (1-4): ")
        
        if choice == '1':
            test_cpu_scaling()
        elif choice == '2':
            test_connection_scaling()
        elif choice == '3':
            test_cpu_scaling()
            time.sleep(5)
            test_connection_scaling()
        elif choice == '4':
            break
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()
