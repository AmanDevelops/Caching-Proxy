# High-Performance Caching Proxy

A blazing-fast caching proxy server built with Flask and Redis.

## Performance Optimizations Implemented

### 1. **Connection Pooling**

- Redis connection pool with 20 max connections
- Connection reuse reduces overhead
- Configurable timeout and retry settings

### 2. **Asynchronous Operations**

- Cache writes happen asynchronously (fire-and-forget)
- ThreadPoolExecutor for non-blocking cache operations
- Responses return immediately without waiting for cache writes

### 3. **Data Compression**

- Gzip compression for cached data
- Pickle serialization (faster than JSON)
- Significant memory savings in Redis

### 4. **Optimized HTTP Requests**

- Connection keep-alive for upstream requests
- Optimized timeout settings (3s connect, 10s read)
- Proper user-agent and headers


## Quick Start

### Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your configuration

# Run with Flask development server
python app.py
```

## API Endpoints

- `GET /` - Proxy requests to upstream server
- `GET /<path>` - Proxy requests to upstream server with path
- `POST /cache/clear` - Clear cache

## Environment Variables

- `PROXY_URL` - Upstream server URL
- `PROXY_EXPIRY` - Cache expiry time in seconds
- `REDIS_HOST` - Redis server host
- `REDIS_PORT` - Redis server port
- `REDIS_PASSWORD` - Redis password (optional)

## Performance Monitoring

The proxy includes several headers for monitoring:

- `X-Cache: HIT|MISS` - Cache status

## Benchmarking

A benchmark was performed which evaluated the `/posts/1` endpoint under a steady load of 10 requests per second, simulating 600 virtual users. The results demonstrate robust and consistent performance aligned with industry standards for proxy responsiveness and reliability:

### Throughput: 

600 requests were processed with a 100% success rate (HTTP 200), and zero failures or errors.

- **Response Time:**  
  - **Mean:** 3 ms  
  - **Median (p50):** 3 ms  
  - **95th percentile (p95):** 4 ms  
  - **Maximum:** 8 ms  
  - **99th percentile (p99):** 6 ms  
- **Session Length:**  
  - **Mean:** 5.7 ms  
  - **Median:** 5.3 ms  
  - **95th percentile:** 8.4 ms  
  - **Maximum:** 28.8 ms

All response times are well below the commonly accepted industry threshold of 100 ms for high-performance APIs, indicating excellent scalability and low latency under load. No virtual user sessions failed, confirming stable and reliable service behavior throughout the test.

### Inspiration
https://roadmap.sh/projects/caching-server
