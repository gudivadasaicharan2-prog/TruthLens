# TruthLens System Design

**Comprehensive system design documentation for TruthLens**

---

## Architecture Overview

TruthLens follows a modern three-tier architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                         Client Layer                         │
│                    (React SPA + Vite)                       │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/HTTPS
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│                    (FastAPI + Gunicorn)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  API Layer   │  │  Business    │  │  ML Pipeline  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
┌───────────────┐         ┌───────────────┐
│  PostgreSQL   │         │  File Storage  │
│   Database    │         │  (Local/S3)    │
└───────────────┘         └───────────────┘
```

### Component Responsibilities

**Client Layer:**
- User interface and interaction
- Client-side validation
- State management
- API communication

**Application Layer:**
- Request routing and validation
- Business logic
- ML pipeline orchestration
- Authentication and authorization

**Data Layer:**
- Data persistence
- File storage
- Caching (future)

---

## Scaling Strategy

### Horizontal Scaling

**Backend Scaling:**
- **Stateless design:** FastAPI instances are stateless
- **Load balancer:** Nginx or cloud load balancer distributes requests
- **Auto-scaling:** Kubernetes HPA based on CPU/memory metrics
- **Session management:** JWT tokens stored in cookies, no server-side sessions

**Database Scaling:**
- **Read replicas:** Multiple read replicas for read-heavy workloads
- **Connection pooling:** SQLAlchemy connection pooling
- **Query optimization:** Indexed queries for common operations
- **Sharding:** Future: Horizontal sharding for large datasets

**ML Scaling:**
- **GPU instances:** Separate GPU instances for ML inference
- **Model serving:** Dedicated model serving with TorchServe or MLflow
- **Batch processing:** Queue-based batch processing for multiple images
- **Model caching:** Models loaded in memory for fast inference

### Vertical Scaling

**Resource Allocation:**
- **CPU:** 4-8 cores for API processing
- **Memory:** 8-16GB RAM for application and ML models
- **GPU:** 8-16GB VRAM for ML inference
- **Storage:** SSD for fast I/O

**Optimization:**
- **Async operations:** Non-blocking I/O with FastAPI
- **Connection pooling:** Reuse database connections
- **Model warm-up:** Pre-load models at startup
- **Memory management:** Proper cleanup and garbage collection

---

## Load Balancing

### Load Balancer Configuration

**Nginx Configuration:**
```nginx
upstream backend {
    least_conn;
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}

server {
    listen 80;
    server_name truthlens.app;

    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        root /var/www/frontend;
        try_files $uri $uri/ /index.html;
    }
}
```

### Load Balancing Algorithms

**Least Connections:** Routes to server with fewest active connections
**Round Robin:** Distributes requests evenly
**IP Hash:** Routes based on client IP (session affinity)

### Health Checks

**Active Health Checks:**
- HTTP health checks every 10 seconds
- Unhealthy instances removed from pool
- Healthy instances added back after recovery

**Passive Health Checks:**
- Monitor response times
- Remove slow instances
- Circuit breaker for failing endpoints

---

## Caching Strategy

### Application-Level Caching

**Response Caching:**
- **Cache headers:** Cache-Control headers for static assets
- **API response caching:** Cache expensive API responses
- **TTL:** Configurable time-to-live for cached data

**Database Query Caching:**
- **SQLAlchemy caching:** Query result caching
- **Redis integration:** Future: Redis for distributed caching
- **Materialized views:** Pre-computed expensive queries

### CDN Caching

**Static Assets:**
- **CDN distribution:** Serve static assets via CDN
- **Cache invalidation:** Cache busting with versioned filenames
- **Edge caching:** Cache at edge locations

### ML Model Caching

**Model Caching:**
- **In-memory caching:** Models loaded in memory
- **Model versioning:** Cache multiple model versions
- **Warm-up:** Pre-load models at startup

---

## Storage Architecture

### File Storage

**Upload Storage:**
- **Local storage:** Temporary storage during processing
- **S3 integration:** Future: AWS S3 for scalable storage
- **CDN:** Serve processed images via CDN

**Storage Hierarchy:**
```
uploads/
├── temporary/     # Temporary uploads (1 hour TTL)
├── processed/      # Processed images (7 days TTL)
├── reports/        # Generated reports (30 days TTL)
└── models/         # ML models (persistent)
```

### Database Storage

**PostgreSQL Schema:**
- **Users table:** User authentication and profile
- **Analyses table:** Analysis results and metadata
- **Sessions table:** Session management (if needed)
- **Audit log table:** Security audit trail

**Storage Optimization:**
- **Indexes:** Optimized for common queries
- **Partitioning:** Future: Partition by date for large tables
- **Compression:** Compress large text fields
- **Vacuum:** Regular database maintenance

---

## GPU Inference

### GPU Architecture

**GPU Utilization:**
- **CUDA:** PyTorch CUDA for GPU acceleration
- **Batch processing:** Process multiple images in parallel
- **Memory management:** Efficient GPU memory usage
- **Model quantization:** Future: Reduce model size

### GPU Scheduling

**Request Queue:**
- **Queue system:** Celery or Redis Queue for GPU tasks
- **Worker pool:** Multiple GPU workers
- **Priority queue:** Prioritize paid users
- **Timeout handling:** Cancel long-running tasks

### GPU Scaling

**Auto-scaling:**
- **GPU instances:** Scale GPU instances based on demand
- **Spot instances:** Use spot instances for cost savings
- **Multi-GPU:** Distribute across multiple GPUs
- **Model serving:** Dedicated model serving infrastructure

### GPU Optimization

**Optimizations:**
- **Mixed precision:** FP16 for faster inference
- **TensorRT:** Future: NVIDIA TensorRT optimization
- **ONNX:** Future: ONNX runtime for cross-platform
- **Model pruning:** Remove unused model weights

---

## Future Improvements

### Short-term (Next 3 Months)

**Performance:**
- **Redis caching:** Implement Redis for distributed caching
- **CDN integration:** Serve static assets via CDN
- **Database optimization:** Add read replicas
- **Query optimization:** Improve slow queries

**Features:**
- **WebSocket:** Real bidirectional communication
- **Video support:** Extend to video deepfake detection
- **Audio support:** Add audio deepfake detection
- **Mobile apps:** iOS and Android applications

### Medium-term (6 Months)

**Architecture:**
- **Microservices:** Split into separate services
- **Message queue:** RabbitMQ or Kafka for async tasks
- **Event sourcing:** Event-driven architecture
- **CQRS:** Command Query Responsibility Segregation

**ML:**
- **Model ensemble:** Combine multiple model instances
- **Active learning:** Learn from user feedback
- **AutoML:** Automated model selection
- **Federated learning:** Privacy-preserving learning

### Long-term (12 Months)

**Infrastructure:**
- **Kubernetes:** Container orchestration
- **Service mesh:** Istio for service communication
- **Multi-region:** Deploy across multiple regions
- **Edge computing:** Deploy inference at edge

**AI:**
- **Custom models:** Train custom models on domain data
- **Transfer learning:** Fine-tune on specific datasets
- **Neural architecture search:** AutoML for model design
- **Explainable AI:** Advanced explainability techniques

---

## Security Architecture

### Security Layers

**Network Security:**
- **HTTPS/TLS:** Encrypted communication
- **Firewall:** Network-level firewalls
- **DDoS protection:** Cloud DDoS protection
- **VPC:** Private network isolation

**Application Security:**
- **Authentication:** JWT and OAuth2
- **Authorization:** Role-based access control
- **Input validation:** Comprehensive validation
- **Rate limiting:** API rate limiting

**Data Security:**
- **Encryption at rest:** Database encryption
- **Encryption in transit:** TLS encryption
- **Data masking:** Sensitive data masking
- **Backup encryption:** Encrypted backups

### Security Best Practices

**Practices:**
- **Least privilege:** Minimal permissions
- **Defense in depth:** Multiple security layers
- **Security headers:** Comprehensive headers
- **Audit logging:** Security event logging
- **Regular updates:** Keep dependencies updated

---

## Monitoring and Observability

### Logging

**Structured Logging:**
- **JSON format:** Machine-readable logs
- **Request tracing:** Unique request IDs
- **Log levels:** DEBUG, INFO, WARNING, ERROR
- **Log aggregation:** ELK stack or CloudWatch

### Metrics

 **Performance Metrics:**
- **Response time:** API response times
- **Throughput:** Requests per second
- **Error rate:** Error percentage
- **Resource usage:** CPU, memory, GPU

**Business Metrics:**
- **Analysis count:** Number of analyses
- **User growth:** Active users
- **Accuracy:** Model accuracy
- **User satisfaction:** Feedback scores

### Tracing

**Distributed Tracing:**
- **OpenTelemetry:** Distributed tracing
- **Span tracking:** Request propagation
- **Service map:** Service dependency map
- **Performance analysis:** Bottleneck identification

### Alerting

**Alerting:**
- **Threshold alerts:** CPU, memory, disk usage
- **Error alerts:** High error rates
- **Performance alerts:** Slow response times
- **Security alerts:** Suspicious activity

---

## Disaster Recovery

### Backup Strategy

**Database Backups:**
- **Daily backups:** Automated daily backups
- **Point-in-time recovery:** WAL logs for recovery
- **Cross-region:** Replicate to different region
- **Backup testing:** Regular restore testing

**File Backups:**
- **S3 versioning:** Versioned file storage
- **Lifecycle policies:** Automatic old file deletion
- **Cross-region:** Replicate to different region

### High Availability

**Redundancy:**
- **Multi-AZ:** Deploy across availability zones
- **Load balancing:** Distribute across instances
- **Failover:** Automatic failover on failure
- **Health checks:** Continuous health monitoring

---

## Cost Optimization

### Cost Reduction Strategies

**Infrastructure:**
- **Spot instances:** Use spot instances for non-critical workloads
- **Reserved instances:** Reserved instances for steady workloads
- **Auto-scaling:** Scale down during low traffic
- **Right-sizing:** Use appropriate instance sizes

**Storage:**
- **Lifecycle policies:** Move old data to cheaper storage
- **Compression:** Compress stored data
- **Deduplication:** Remove duplicate data
- **CDN caching:** Reduce origin requests

**ML:**
- **Batch processing:** Process images in batches
- **Model quantization:** Reduce model size
- **GPU sharing:** Share GPU instances
- **Spot GPUs:** Use spot GPU instances

---

## Conclusion

TruthLens is designed with scalability, reliability, and performance in mind. The architecture supports horizontal scaling, efficient load balancing, comprehensive caching, and optimized GPU inference. Future improvements will focus on microservices, advanced ML techniques, and enhanced infrastructure.

The system is production-ready with enterprise-grade security, observability, and disaster recovery capabilities.
