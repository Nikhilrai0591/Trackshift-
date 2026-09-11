import { useEffect, useRef, useState, useCallback } from 'react';

/**
 * Polls an async fetcher function on an interval, exposing data/error/loading.
 * Pauses cleanly on unmount. `intervalMs = 0` disables polling (fetch once).
 */
export function usePolling(fetcher, intervalMs = 1000, deps = []) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const timerRef = useRef(null);
  const mountedRef = useRef(true);
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  const tick = useCallback(async () => {
    try {
      const result = await fetcherRef.current();
      if (mountedRef.current) {
        setData(result);
        setError(null);
      }
    } catch (e) {
      if (mountedRef.current) setError(e);
    } finally {
      if (mountedRef.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    setLoading(true);
    tick();
    if (intervalMs > 0) {
      timerRef.current = setInterval(tick, intervalMs);
    }
    return () => {
      mountedRef.current = false;
      if (timerRef.current) clearInterval(timerRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [intervalMs, ...deps]);

  return { data, error, loading, refetch: tick };
}
