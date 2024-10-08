use std::env;

/// Test the performance of concurrent read.
#[test]
fn test_concurrent_read() {
    let action_per_thread = env::var("ACTION_PER_THREAD")
        .unwrap_or("10000".to_string())
        .parse::<usize>()
        .unwrap();

    let thread_count = env::var("THREAD_COUNT")
        .unwrap_or("10".to_string())
        .parse::<usize>()
        .unwrap();
}

#[test]
fn test_concurrent_write() {}
