#!/usr/bin/env python3
"""
Lab Test Script - Concurrent vs Single-threaded Server Comparison

This script implements the exact test described in the lab requirements:
- Make 10 concurrent requests to the server
- Measure total handling time  
- Compare threaded vs single-threaded performance
- Add ~1s delay to simulate work
"""

import argparse
import time
import concurrent.futures
import urllib.request
import urllib.error
from typing import List, Tuple


def make_request(url: str, request_id: int) -> Tuple[int, float, int]:
    """Make a single HTTP request and return (request_id, duration, status_code)"""
    start = time.time()
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            status = response.status
    except urllib.error.HTTPError as e:
        status = e.code
    except Exception:
        status = 0  # Connection error
    
    duration = time.time() - start
    return request_id, duration, status


def test_concurrent_requests(url: str, num_requests: int = 10) -> dict:
    """Make concurrent requests and measure performance"""
    print(f"🚀 Starting {num_requests} CONCURRENT requests to {url}")
    
    start_time = time.time()
    results = []
    
    # Use ThreadPoolExecutor to make truly concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_requests) as executor:
        # Submit all requests at once
        futures = [
            executor.submit(make_request, url, i+1) 
            for i in range(num_requests)
        ]
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    
    total_time = time.time() - start_time
    
    # Sort by request_id for display
    results.sort(key=lambda x: x[0])
    
    # Analyze results
    successful = [r for r in results if r[2] == 200]
    failed = [r for r in results if r[2] != 200]
    
    return {
        'mode': 'CONCURRENT',
        'total_time': total_time,
        'num_requests': num_requests,
        'successful': len(successful),
        'failed': len(failed),
        'avg_request_time': sum(r[1] for r in successful) / len(successful) if successful else 0,
        'results': results
    }


def test_sequential_requests(url: str, num_requests: int = 10) -> dict:
    """Make sequential requests and measure performance"""
    print(f"🐌 Starting {num_requests} SEQUENTIAL requests to {url}")
    
    start_time = time.time()
    results = []
    
    # Make requests one after another
    for i in range(num_requests):
        result = make_request(url, i+1)
        results.append(result)
    
    total_time = time.time() - start_time
    
    # Analyze results
    successful = [r for r in results if r[2] == 200]
    failed = [r for r in results if r[2] != 200]
    
    return {
        'mode': 'SEQUENTIAL',
        'total_time': total_time,
        'num_requests': num_requests,
        'successful': len(successful),
        'failed': len(failed),
        'avg_request_time': sum(r[1] for r in successful) / len(successful) if successful else 0,
        'results': results
    }


def print_results(result: dict):
    """Print formatted test results"""
    print(f"\n{'='*60}")
    print(f"📊 {result['mode']} TEST RESULTS")
    print(f"{'='*60}")
    print(f"Total Time:          {result['total_time']:.3f} seconds")
    print(f"Requests Made:       {result['num_requests']}")
    print(f"Successful (200):    {result['successful']}")
    print(f"Failed (non-200):    {result['failed']}")
    print(f"Avg Request Time:    {result['avg_request_time']:.3f} seconds")
    print(f"Throughput:          {result['successful']/result['total_time']:.1f} req/sec")
    
    print(f"\n📋 Individual Request Times:")
    for req_id, duration, status in result['results']:
        status_emoji = "✅" if status == 200 else "❌"
        print(f"  Request {req_id:2d}: {duration:.3f}s - {status} {status_emoji}")


def compare_lab_results(lab1_result: dict, lab2_result: dict, delay: float, num_requests: int):
    """Compare Lab 1 vs Lab 2 server performance"""
    print(f"\n{'🔄 LAB 1 vs LAB 2 COMPARISON'}")
    print(f"{'='*60}")
    
    speedup = lab1_result['total_time'] / lab2_result['total_time']
    
    print(f"Lab 1 (Single-threaded): {lab1_result['total_time']:.3f}s")
    print(f"Lab 2 (Multithreaded):   {lab2_result['total_time']:.3f}s")
    print(f"Speedup Factor:          {speedup:.1f}x")
    
    expected_lab1_time = num_requests * delay
    expected_lab2_time = delay * 1.5  # some overhead expected
    
    print(f"\n📊 ANALYSIS:")
    print(f"Expected Lab 1 time:     ~{expected_lab1_time:.1f}s (sequential processing)")
    print(f"Expected Lab 2 time:     ~{expected_lab2_time:.1f}s (parallel processing)")
    
    lab1_ok = abs(lab1_result['total_time'] - expected_lab1_time) < expected_lab1_time * 0.3
    lab2_ok = lab2_result['total_time'] < expected_lab1_time * 0.5
    
    print(f"\n🎯 RESULTS:")
    if lab1_ok and lab2_ok and speedup > 3:
        print("✅ PERFECT: Lab 1 shows sequential behavior, Lab 2 shows parallel speedup!")
        print("   This proves the difference between single-threaded and multithreaded servers.")
    elif lab2_ok and speedup > 2:
        print("👍 GOOD: Lab 2 shows significant speedup over Lab 1.")
    elif speedup > 1.2:
        print("⚠️  PARTIAL: Some speedup observed, but not optimal.")
    else:
        print("❌ ISSUE: No significant speedup. Check if both servers are configured correctly.")
    
    print(f"\n💡 PLT THEORY:")
    print(f"   Lab 1: Sequential program structure → Sequential execution")
    print(f"   Lab 2: Concurrent program structure → Parallel execution (with speedup)")
    print(f"   This demonstrates that concurrency (structure) enables parallelism (performance).")


def compare_results(concurrent_result: dict, sequential_result: dict):
    """Compare and analyze the two test results (kept for compatibility)"""
    print(f"\n{'🔄 COMPARISON ANALYSIS'}")
    print(f"{'='*60}")
    
    speedup = sequential_result['total_time'] / concurrent_result['total_time']
    
    print(f"Sequential Total Time:   {sequential_result['total_time']:.3f}s")
    print(f"Concurrent Total Time:   {concurrent_result['total_time']:.3f}s")
    print(f"Speedup Factor:          {speedup:.1f}x")
    
    if speedup > 5:
        print("🎯 EXCELLENT: True parallelism achieved!")
        print("   Multiple threads are executing simultaneously on multiple cores.")
    elif speedup > 2:
        print("👍 GOOD: Decent parallelism with some overhead.")
    elif speedup > 1.1:
        print("⚠️  LIMITED: Some concurrency but limited parallelism.")
    else:
        print("❌ NO SPEEDUP: Server might be single-threaded or CPU bound.")
    
    print(f"\n💡 THEORY:")
    print(f"   With {concurrent_result['num_requests']} requests and ~1s handler delay:")
    print(f"   - Threaded server (concurrent):  ~1-2s expected")
    print(f"   - Single-threaded server:        ~{concurrent_result['num_requests']}s expected")


def main():
    parser = argparse.ArgumentParser(description="Lab Test: Lab 1 vs Lab 2 Server Comparison")
    parser.add_argument("--lab1-url", default="http://localhost:8001/index.html",
                      help="Lab 1 server URL (single-threaded) - default: http://localhost:8001/index.html")
    parser.add_argument("--lab2-url", default="http://localhost:8000/index.html", 
                      help="Lab 2 server URL (multithreaded) - default: http://localhost:8000/index.html")
    parser.add_argument("-n", "--requests", type=int, default=10,
                      help="Number of requests to make (default: 10)")
    parser.add_argument("--mode", choices=['lab1', 'lab2', 'compare'], 
                      default='compare', help="Test mode (default: compare both labs)")
    parser.add_argument("--delay", type=float, default=1.0, help="Expected server delay for analysis")
    
    args = parser.parse_args()
    
    print(f"🧪 LAB COMPARISON: Lab 1 (Single-threaded) vs Lab 2 (Multithreaded)")
    print(f"Lab 1 URL: {args.lab1_url}")
    print(f"Lab 2 URL: {args.lab2_url}")
    print(f"Requests: {args.requests}")
    print(f"Mode: {args.mode}")
    print(f"Expected per-request delay: {args.delay}s")
    print(f"Expected Lab 1 time: ~{args.requests * args.delay}s (sequential processing)")
    print(f"Expected Lab 2 time: ~{args.delay}s (parallel processing)")
    
    print(f"\n⚠️  Make sure BOTH servers are running with HANDLER_DELAY={args.delay}!")
    print(f"   Lab 1: Single-threaded HTTP server on port 8001")
    print(f"   Lab 2: Multithreaded HTTP server on port 8000")
    
    try:
        if args.mode in ['lab1', 'compare']:
            print(f"\n{'='*60}")
            print(f"🐌 TESTING LAB 1 SERVER (Single-threaded)")
            print(f"{'='*60}")
            lab1_result = test_concurrent_requests(args.lab1_url, args.requests)
            lab1_result['mode'] = 'LAB 1 (Single-threaded)'
            print_results(lab1_result)
        
        if args.mode in ['lab2', 'compare']:
            if args.mode == 'compare':
                print(f"\n{'⏳ Waiting 2 seconds between tests...'}")
                time.sleep(2)
            
            print(f"\n{'='*60}")
            print(f"🚀 TESTING LAB 2 SERVER (Multithreaded)")
            print(f"{'='*60}")
            lab2_result = test_concurrent_requests(args.lab2_url, args.requests)
            lab2_result['mode'] = 'LAB 2 (Multithreaded)'
            print_results(lab2_result)
        
        if args.mode == 'compare':
            compare_lab_results(lab1_result, lab2_result, args.delay, args.requests)
        
    except KeyboardInterrupt:
        print(f"\n❌ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")


if __name__ == "__main__":
    main()