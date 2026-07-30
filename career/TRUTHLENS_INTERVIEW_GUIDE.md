# TruthLens Interview Guide

**50 Interview Questions with Answers**

---

## Architecture Questions (10)

### 1. Can you explain the overall architecture of TruthLens?

TruthLens follows a three-tier architecture:
- **Frontend:** React SPA with Vite, communicating via REST API
- **Backend:** FastAPI with ASGI, handling business logic and ML pipeline
- **Database:** PostgreSQL for data persistence
- **ML Pipeline:** PyTorch models for image analysis

The system uses a microservices approach with clear separation between UI, API, and ML components. The backend serves as the orchestration layer, coordinating between the database, ML models, and frontend.

### 2. How did you design the ML pipeline architecture?

The ML pipeline is designed as a modular system with:
- **Preprocessing Layer:** Image normalization and tensor conversion
- **Detection Layer:** Parallel execution of multiple models (EfficientNet, CLIP, face detection, forensics)
- **Explainability Layer:** Grad-CAM generation for visual explanations
- **Fusion Layer:** Weighted combination of detection results
- **Report Layer:** PDF generation with findings

I used the singleton pattern for model loading to optimize memory, and context managers for resource management to ensure proper cleanup.

### 3. How does the fusion engine work?

The fusion engine combines results from multiple detection modules:
1. **Image Type Detection:** Determines if the image is a document, artwork, portrait, etc.
2. **Weight Selection:** Chooses appropriate weights based on image type and pipeline
3. **Weighted Combination:** Combines EfficientNet, CLIP, forensics, and face detection scores
4. **Confidence Calibration:** Applies calibration factors for accurate probability display

The weights are configurable in `fusion_config.py` and can be adjusted based on validation results.

### 4. How did you handle model loading and memory management?

I used the singleton pattern to load models once at startup:
- Models are loaded in the application lifespan
- Model warm-up is performed to reduce first-request latency
- GPU memory is managed with PyTorch's automatic memory management
- Graceful shutdown includes GPU memory cleanup
- Context managers ensure proper resource cleanup

### 5. How does the frontend communicate with the backend?

The frontend uses Axios for HTTP requests:
- REST API endpoints for all operations
- JWT tokens stored in secure cookies for authentication
- Request interceptors add authentication headers
- Response interceptors handle errors globally
- WebSocket-style progress updates via polling for long-running operations

### 6. How did you design the database schema?

The database uses SQLAlchemy ORM with:
- **Users table:** Authentication and user profile data
- **Analyses table:** Analysis results and metadata
- **Foreign keys:** Relationships between users and their analyses
- **Indexes:** Optimized for common queries (user history, recent analyses)
- **JSON fields:** Flexible storage for analysis results

### 7. How does the system handle file uploads?

File uploads are handled with comprehensive security:
- **Magic bytes validation:** Checks actual file content, not just extension
- **MIME type validation:** Verifies content type
- **File size limits:** 10MB maximum
- **Executable detection:** Prevents malicious file uploads
- **Temporary storage:** Files stored in temporary directory during processing
- **Automatic cleanup:** Old files removed after 1 hour

### 8. How did you implement real-time progress updates?

I implemented WebSocket-style progress updates using:
- **Step-by-step progress indicators:** Each analysis step reports progress
- **Optimistic UI updates:** Frontend updates before receiving confirmation
- **Polling mechanism:** Frontend polls for progress updates
- **Animated progress bars:** Framer Motion for smooth animations
- **Error handling:** Graceful degradation if updates fail

### 9. How does the system handle concurrent requests?

The system handles concurrency through:
- **Async/await:** FastAPI's async support for non-blocking I/O
- **Connection pooling:** SQLAlchemy connection pooling for database
- **Rate limiting:** slowapi for API rate limiting
- **GPU queuing:** PyTorch handles GPU operations sequentially
- **Load balancing:** Docker Compose can scale backend instances

### 10. How did you design the error handling strategy?

Error handling is centralized through:
- **Custom exceptions:** Specific exceptions for different error types
- **Exception handlers:** FastAPI exception handlers for consistent responses
- **Structured error responses:** JSON format with error details
- **Logging:** All errors logged with request ID for tracing
- **User-friendly messages:** Generic messages for users, detailed for logs

---

## AI Questions (10)

### 11. What ML models did you use and why?

I used:
- **EfficientNet-B2:** Efficient CNN for image classification with good accuracy/speed tradeoff
- **CLIP:** OpenAI's model for semantic image-text understanding
- **MTCNN:** Multi-task cascaded CNN for accurate face detection
- **Grad-CAM:** For explainable AI visualizations

These models were chosen for their complementary strengths: EfficientNet for classification, CLIP for semantic understanding, MTCNN for face detection, and Grad-CAM for explainability.

### 12. How does Grad-CAM work in your system?

Grad-CAM generates heatmaps showing important image regions:
1. **Hook registration:** Register forward and backward hooks on target layer
2. **Forward pass:** Pass image through model, capture activations
3. **Backward pass:** Compute gradients for predicted class
4. **Weighting:** Weight activations by gradients
5. **Heatmap generation:** Generate heatmap from weighted activations
6. **Colorization:** Apply colormap for visualization
7. **Overlay:** Blend heatmap with original image

### 13. How did you integrate multiple ML models?

I created a unified detector interface:
- **Abstract base class:** Common interface for all detectors
- **Factory pattern:** Detector instantiation based on configuration
- **Parallel execution:** Models run in parallel where possible
- **Result aggregation:** Results collected and combined by fusion engine
- **Error handling:** Graceful degradation if one model fails

### 14. How do you handle model inference time?

Optimizations for inference time:
- **Model warm-up:** Pre-load models at startup
- **Batch processing:** Process multiple images when possible
- **GPU acceleration:** Use CUDA when available
- **Image preprocessing:** Efficient tensor conversion
- **Async execution:** Non-blocking inference with FastAPI

### 15. How does the system handle different image types?

The system uses image type classification:
- **Edge detection:** Detects sharp edges (documents)
- **Text detection:** OCR for text presence
- **Color analysis:** Color distribution analysis
- **Aspect ratio:** Determines portrait/landscape
- **Dynamic weights:** Fusion engine adjusts weights based on type

### 16. How did you implement forensic analysis?

Forensic analysis includes:
- **ELA (Error Level Analysis):** Re-compresses image and analyzes differences
- **Noise analysis:** Measures noise levels in grayscale image
- **Compression artifacts:** Detects JPEG compression inconsistencies
- **Metadata analysis:** Examines EXIF data for inconsistencies

### 17. How do you validate model predictions?

Validation through:
- **Confidence scores:** Each model provides confidence
- **Fusion engine:** Combines multiple model predictions
- **Threshold tuning:** Adjusted based on validation dataset
- **Human-in-the-loop:** Users can provide feedback
- **Continuous improvement:** Models can be retrained with new data

### 18. How does the system handle model updates?

Model updates are handled through:
- **Versioned models:** Models stored with version numbers
- **Configuration-based loading:** Model path in configuration
- **Graceful reload:** Models can be reloaded without restart
- **A/B testing:** Can test new models alongside old ones
- **Rollback:** Can revert to previous model version

### 19. How do you measure model performance?

Performance metrics:
- **Accuracy:** Percentage of correct predictions
- **Precision/Recall:** For different confidence thresholds
- **F1 Score:** Balance of precision and recall
- **Inference time:** Time per prediction
- **GPU utilization:** GPU memory and compute usage

### 20. How would you improve the ML pipeline?

Future improvements:
- **Model quantization:** Reduce model size and improve speed
- **Ensemble methods:** Combine multiple model instances
- **Transfer learning:** Fine-tune on specific datasets
- **Active learning:** Learn from user feedback
- **AutoML:** Automated model selection and tuning

---

## React Questions (10)

### 21. Why did you choose React over other frameworks?

I chose React because:
- **Large ecosystem:** Extensive library and tool support
- **Component-based:** Reusable component architecture
- **Hooks:** Modern state management without classes
- **Performance:** Virtual DOM for efficient updates
- **Industry standard:** Widely used in industry
- **TypeScript support:** Optional static typing

### 22. How did you structure the React application?

Structure follows:
- **Components:** Reusable UI components in `src/components/`
- **Pages:** Route-level components in `src/pages/`
- **Services:** API calls in `src/services/`
- **Context:** Global state in `src/context/`
- **Utils:** Helper functions in `src/utils/`
- **Lazy loading:** Code splitting with React.lazy

### 23. How do you manage state in the application?

State management through:
- **React Context:** Global state for auth and theme
- **useState:** Local component state
- **useReducer:** Complex local state logic
- **Custom hooks:** Reusable state logic (useAuth, useTheme)
- **Server state:** API responses managed by Axios

### 24. How did you implement authentication?

Authentication through:
- **JWT tokens:** Stored in secure HTTP-only cookies
- **AuthContext:** Global authentication state
- **Protected routes:** Route guards for authenticated pages
- **Token refresh:** Automatic token refresh before expiration
- **Google OAuth:** OAuth2 integration for social login

### 25. How do you handle file uploads in React?

File upload handling:
- **Drag-and-drop:** Custom UploadZone component
- **File input:** Standard file input with validation
- **Progress tracking:** Upload progress with Axios
- **Error handling:** User-friendly error messages
- **Preview:** Image preview before upload

### 26. How did you optimize React performance?

Performance optimizations:
- **React.memo:** Memoize expensive components
- **useMemo:** Memoize expensive calculations
- **useCallback:** Memoize function references
- **Code splitting:** Lazy load routes with React.lazy
- **Virtual scrolling:** For large lists
- **Image optimization:** Lazy loading and caching

### 27. How do you handle API calls?

API calls through:
- **Axios:** HTTP client with interceptors
- **Service layer:** Centralized API calls in `api.js`
- **Request interceptors:** Add authentication headers
- **Response interceptors:** Handle errors globally
- **Retry logic:** Automatic retry for failed requests

### 28. How did you implement real-time updates?

Real-time updates through:
- **Polling:** Periodic API calls for progress
- **Optimistic updates:** Update UI before confirmation
- **WebSocket-style:** Simulated WebSocket with polling
- **Error recovery:** Graceful degradation on failure

### 29. How do you handle errors in React?

Error handling through:
- **Error boundaries:** Catch component errors
- **Try-catch:** In async functions
- **Error messages:** User-friendly error displays
- **Logging:** Error logging to backend
- **Recovery:** Retry mechanisms for recoverable errors

### 30. How would you improve the React application?

Future improvements:
- **TypeScript:** Add static typing
- **State management:** Redux or Zustand for complex state
- **Testing:** More component tests with React Testing Library
- **Performance:** Web Workers for heavy computations
- **PWA:** Progressive Web App features

---

## FastAPI Questions (10)

### 31. Why did you choose FastAPI over other frameworks?

I chose FastAPI because:
- **Performance:** Built on Starlette, very fast
- **Async support:** Native async/await support
- **Type hints:** Automatic validation with Pydantic
- **Auto-docs:** Automatic OpenAPI documentation
- **Modern:** Modern Python features
- **Easy to learn:** Simple and intuitive API

### 32. How did you structure the FastAPI application?

Structure follows:
- **API layer:** Routes in `app/api/v1/`
- **Core layer:** Business logic in `app/core/`
- **Models:** Database models in `app/models/`
- **Schemas:** Pydantic schemas in `app/schemas/`
- **Services:** ML services in `app/ai/`
- **Main:** Application entry point in `app/main.py`

### 33. How do you handle authentication in FastAPI?

Authentication through:
- **JWT tokens:** OAuth2PasswordBearer scheme
- **Dependency injection:** Depends() for auth checks
- **User context:** Current user in request state
- **Token validation:** Verify token signature and expiration
- **Google OAuth:** OAuth2 flow for social login

### 34. How did you implement rate limiting?

Rate limiting through:
- **slowapi:** Decorator-based rate limiting
- **Custom limits:** Different limits per endpoint
- **HTTP 429:** Standard rate limit response
- **Configurable:** Limits in environment variables
- **Per-user:** Rate limit by user ID when authenticated

### 35. How do you validate requests?

Request validation through:
- **Pydantic schemas:** Automatic validation
- **File validation:** Magic bytes, MIME type, size
- **Custom validators:** Pydantic validators
- **Error handling:** Validation errors return 422
- **Sanitization:** Input sanitization for security

### 36. How did you implement middleware?

Middleware for:
- **Security headers:** CSP, HSTS, X-Frame-Options
- **CORS:** Cross-origin resource sharing
- **Request tracing:** Unique request ID assignment
- **Error handling:** Centralized error handling
- **Logging:** Request/response logging

### 37. How do you handle database operations?

Database operations through:
- **SQLAlchemy ORM:** Type-safe database operations
- **Async sessions:** Async database sessions
- **Connection pooling:** Efficient connection reuse
- **Transactions:** Automatic transaction management
- **Migrations:** Alembic for schema migrations

### 38. How did you implement health checks?

Health checks through:
- **Basic health:** `/health` - simple status
- **Readiness:** `/health/ready` - dependencies check
- **Liveness:** `/health/live` - process health
- **Detailed:** `/health/detailed` - comprehensive status
- **Docker health:** Health check in Dockerfile

### 39. How do you handle async operations?

Async operations through:
- **Async/await:** Non-blocking I/O
- **Async database:** Async SQLAlchemy sessions
- **Async file I/O:** aiofiles for file operations
- **Background tasks:** FastAPI BackgroundTasks
- **Celery:** For long-running tasks (future)

### 40. How would you improve the FastAPI application?

Future improvements:
- **WebSockets:** Real bidirectional communication
- **GraphQL:** Alternative to REST API
- **Caching:** Redis for response caching
- **Message queue:** RabbitMQ for async tasks
- **Microservices:** Split into separate services

---

## Security Questions (5)

### 41. How did you secure file uploads?

File upload security:
- **Magic bytes validation:** Check actual file content
- **MIME type validation:** Verify content type
- **File size limits:** 10MB maximum
- **Executable detection:** Prevent malicious files
- **Temporary storage:** Isolated temporary directory
- **Automatic cleanup:** Remove old files

### 42. How do you prevent SQL injection?

SQL injection prevention:
- **SQLAlchemy ORM:** Parameterized queries
- **Pydantic validation:** Input validation
- **No raw SQL:** Avoid raw SQL queries
- **Least privilege:** Database user with limited permissions
- **Input sanitization:** Additional sanitization layer

### 43. How did you implement security headers?

Security headers:
- **CSP:** Content Security Policy
- **HSTS:** HTTP Strict Transport Security
- **X-Frame-Options:** Prevent clickjacking
- **X-Content-Type-Options:** Prevent MIME sniffing
- **X-XSS-Protection:** XSS protection
- **Referrer-Policy:** Control referrer information
- **Permissions-Policy:** Feature policy

### 44. How do you handle secrets?

Secrets management:
- **Environment variables:** All secrets in environment
- **Validation:** Secret length validation (≥32 characters)
- **No hardcoding:** No secrets in code
- **Production validation:** Additional checks in production
- **Vault:** Future: HashiCorp Vault for secrets

### 45. How do you prevent XSS attacks?

XSS prevention:
- **React:** Automatic XSS escaping
- **CSP:** Content Security Policy
- **Input validation:** Pydantic validation
- **Output encoding:** Proper encoding in responses
- **Sanitization:** DOMPurify for user content

---

## Docker Questions (5)

### 46. How did you containerize the application?

Containerization:
- **Multi-stage builds:** Optimized image size
- **Separate containers:** Backend and frontend containers
- **Docker Compose:** Local development orchestration
- **Non-root user:** Security best practice
- **Health checks:** Docker health check configuration

### 47. How does Docker Compose work?

Docker Compose:
- **Services:** PostgreSQL, backend, frontend
- **Networks:** Service communication
- **Volumes:** Data persistence
- **Environment variables:** Configuration
- **Dependencies:** Service startup order

### 48. How do you optimize Docker images?

Image optimization:
- **Multi-stage builds:** Separate build and runtime
- **Alpine images:** Smaller base images
- **Layer caching:** Leverage Docker layer cache
- **.dockerignore:** Exclude unnecessary files
- **Minimal dependencies:** Only required packages

### 49. How do you handle production deployment?

Production deployment:
- **Docker images:** Production-ready images
- **Registry:** Docker Hub or private registry
- **CI/CD:** Automated building and pushing
- **Environment variables:** Production configuration
- **Health checks:** Container health monitoring

### 50. How would you scale the application?

Scaling strategies:
- **Horizontal scaling:** Multiple backend instances
- **Load balancer:** Nginx or cloud load balancer
- **Database replication:** Read replicas for scaling
- **Caching:** Redis for response caching
- **CDN:** Static content delivery
- **GPU scaling:** Separate GPU instances for ML

---

## Bonus Questions

### What was the most challenging part of this project?

The most challenging part was integrating multiple ML models into a cohesive pipeline. Each model had different input requirements, output formats, and performance characteristics. I had to create a unified interface, handle model loading efficiently, and combine results in a meaningful way. The fusion engine was particularly complex, requiring dynamic weight selection based on image type.

### What are you most proud of?

I'm most proud of achieving enterprise-grade security (85/100 score) and comprehensive observability (90/100 score). These are often overlooked in personal projects but are critical for production systems. The structured logging, request tracing, and performance metrics make the system maintainable and debuggable in production.

### What would you do differently?

I would start with a more comprehensive testing strategy from the beginning. Initially, I focused on functionality and added tests later. In hindsight, I should have used test-driven development to ensure better coverage from the start. I would also add visual regression tests earlier to catch UI issues.

### How do you stay updated with technology?

I follow:
- **Blogs:** Engineering blogs from tech companies
- **Twitter/X:** Follow industry experts
- **GitHub:** Explore trending repositories
- **Conferences:** Watch conference talks online
- **Documentation:** Read official documentation
- **Practice:** Build projects with new technologies

---

## Tips for Interview Success

1. **Be specific:** Use concrete examples from the project
2. **Explain trade-offs:** Discuss why you made certain choices
3. **Show enthusiasm:** Demonstrate passion for the work
4. **Ask questions:** Engage with the interviewer
5. **Be honest:** Admit what you don't know
6. **Connect to business:** Explain the business value
7. **Show growth:** Discuss what you learned
8. **Be prepared:** Review these questions before interviews

Good luck with your interviews!
