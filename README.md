# Cirkle

A full-stack social media platform inspired by Twitter, featuring a robust FastAPI backend and a modern Android mobile application.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Backend Setup](#backend-setup)
- [Frontend Setup](#frontend-setup)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Contributing](#contributing)
- [License](#license)

## 🌟 Overview

Cirkle is a Twitter-like social media platform that allows users to share tweets, manage profiles, and interact with other users. The application is built with a microservices architecture using Docker containers, featuring a Python FastAPI backend and an Android native frontend.

## ✨ Features

### User Features
- 🔐 **User Authentication** - Secure JWT-based authentication
- 👤 **User Profiles** - Create and manage user profiles
- 📝 **Tweet Management** - Create, read, update, and delete tweets
- 🖼️ **Image Upload** - Share images with your tweets
- 📱 **Mobile App** - Native Android application
- 🔄 **Real-time Updates** - Pull-to-refresh functionality
- 📄 **Pagination** - Efficient data loading with Paging 3

### Admin Features
- 🛠️ **Admin Panel** - Comprehensive admin dashboard
- 📊 **User Management** - Monitor and manage users
- 📈 **Analytics** - System monitoring and performance metrics

### Technical Features
- ⚡ **High Performance** - Redis caching for improved response times
- 🔒 **Security** - Rate limiting, security headers, and encrypted data
- 🐳 **Containerized** - Docker and Docker Compose for easy deployment
- 📝 **Logging & Monitoring** - Structured logging and performance monitoring
- 🔄 **Background Tasks** - Celery for asynchronous task processing
- 🌐 **Reverse Proxy** - Nginx with SSL support

## 🛠️ Tech Stack

### Backend

| Category | Technologies |
|----------|-------------|
| **Framework** | FastAPI, Uvicorn |
| **Database** | MySQL 8, SQLAlchemy, Alembic |
| **Caching** | Redis 7 |
| **Authentication** | JWT (python-jose), Passlib, Bcrypt |
| **Background Tasks** | Celery |
| **Web Server** | Nginx 1.25 |
| **Containerization** | Docker, Docker Compose |
| **Data Validation** | Pydantic |
| **Async Support** | aiohttp, aiomysql |
| **Testing & Mocking** | Faker |
| **Logging** | python-json-logger |
| **Monitoring** | psutil |

### Frontend (Android)

| Category | Technologies |
|----------|-------------|
| **Language** | Kotlin 2.2.0 |
| **Build System** | Gradle 8.11.1 |
| **Architecture** | MVVM |
| **Dependency Injection** | Dagger Hilt 2.56.1 |
| **Navigation** | Navigation Component 2.9.1 |
| **Networking** | Retrofit 3.0, OkHttp 5 |
| **JSON Parsing** | Moshi, Gson |
| **Image Loading** | Glide 4.16 |
| **UI Components** | Material Design 1.12 |
| **View Binding** | ViewBinding |
| **Camera** | CameraX 1.4.2 |
| **Pagination** | Paging 3.3.6 |
| **Async** | Kotlin Coroutines 1.10.2 |
| **Security** | Security Crypto (EncryptedSharedPreferences) |
| **Loading Animations** | Shimmer 0.5 |
| **SDK Requirements** | Min SDK 24, Target SDK 36 |

## 📋 Prerequisites

### Backend
- Docker Engine 20.0+
- Docker Compose 2.0+
- (Optional) Python 3.11+ for local development

### Frontend
- Android Studio Iguana or later
- JDK 11
- Android SDK with API Level 36
- Minimum device: Android 7.0 (API 24)

## 📁 Project Structure

```
Cirkle/
├── backend/
│   ├── docker-compose.yml          # Docker orchestration
│   ├── nginx/                      # Nginx configuration
│   │   ├── nginx.conf
│   │   ├── conf.d/
│   │   │   ├── proxy_params.conf
│   │   │   └── security.conf
│   │   └── ssl/                    # SSL certificates
│   └── backend/
│       ├── Dockerfile
│       ├── requirements.txt        # Python dependencies
│       ├── entrypoint.sh          # Container startup script
│       ├── assets/                # Static assets
│       └── src/
│           ├── main.py            # Application entry point
│           ├── auth/              # Authentication module
│           ├── user_profile/      # User profile module
│           ├── tweets/            # Tweets module
│           ├── admin/             # Admin module
│           ├── core/              # Core utilities
│           │   ├── config.py      # Configuration
│           │   ├── security.py    # Security utilities
│           │   ├── rate_limit.py  # Rate limiting
│           │   └── middleware.py  # Middleware
│           ├── database/          # Database configuration
│           ├── caching/           # Redis & Celery
│           ├── monitoring/        # Performance monitoring
│           └── scripts/           # Utility scripts
│
└── frontend/
    ├── build.gradle.kts           # Project build configuration
    ├── settings.gradle.kts        # Project settings
    ├── gradle/
    │   └── libs.versions.toml     # Dependency versions
    └── app/
        ├── build.gradle.kts       # App build configuration
        ├── proguard-rules.pro     # ProGuard rules
        └── src/
            ├── main/
            │   ├── AndroidManifest.xml
            │   ├── java/com/app/cirkle/  # Kotlin source files
            │   └── res/                   # Resources
            ├── androidTest/               # Instrumented tests
            └── test/                      # Unit tests
```

## 🚀 Backend Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Cirkle/backend
```

### 2. Environment Configuration

Create a `.env` file in `backend/backend/src/`:

```env
# Database Configuration
DATABASE_URL=mysql+aiomysql://root:rootpassword@mysql:3306/dbname

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_ORIGINS=["http://localhost:3000"]

# Environment
ENVIRONMENT=development
DEBUG=True
```

### 3. SSL Configuration (Production)

Place your SSL certificates in:
- `nginx/ssl/certs/` - SSL certificate files
- `nginx/ssl/private/` - Private key files
- `nginx/dhparam/` - DH parameters

### 4. Docker Services

The application uses the following services:

- **MySQL** - Port 3307 (mapped from 3306)
- **Redis** - Port 6379
- **Backend API** - Internal port 8000
- **Nginx** - Ports 80 (HTTP) and 443 (HTTPS)

## 📱 Frontend Setup

### 1. Open Project in Android Studio

```bash
cd Cirkle/frontend
```

Open the `frontend` directory in Android Studio.

### 2. Configure API Endpoint

Update the base URL in your network configuration (typically in a `Constants.kt` or API service file):

```kotlin
const val BASE_URL = "http://your-backend-url/"
```

For local development with emulator:
- Use `http://10.0.2.2/` to connect to localhost
- Or use your machine's local IP address

### 3. Sync Gradle

Let Android Studio sync the Gradle files and download dependencies.

## ▶️ Running the Application

### Backend

#### Development Mode

```bash
cd backend
docker-compose up -d
```

This will start:
- MySQL database on port 3307
- Redis on port 6379
- FastAPI backend (via Nginx on port 80/443)

#### View Logs

```bash
docker-compose logs -f backend
```

#### Stop Services

```bash
docker-compose down
```

#### Generate Mock Data

```bash
docker-compose exec backend python scripts/generate_mock_data.py
```

#### Run Tests

```bash
docker-compose exec backend python scripts/run_full_test.py
```

### Frontend

#### Run on Emulator

1. Start an Android Virtual Device (AVD) in Android Studio
2. Click "Run" (▶️) or press `Shift + F10`

#### Run on Physical Device

1. Enable Developer Options on your Android device
2. Enable USB Debugging
3. Connect your device via USB
4. Select your device in Android Studio
5. Click "Run" (▶️)

#### Build APK

```bash
./gradlew assembleDebug
```

The APK will be generated in `app/build/outputs/apk/debug/`

#### Build Release APK

```bash
./gradlew assembleRelease
```

## 📚 API Documentation

### Base URL
```
http://localhost/api/v1
```

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login user |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/auth/logout` | Logout user |

### Profile Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/profile/me` | Get current user profile |
| PUT | `/profile/me` | Update current user profile |
| GET | `/profile/{user_id}` | Get user profile by ID |

### Tweet Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/tweets/` | Create new tweet |
| GET | `/tweets/` | Get all tweets (paginated) |
| GET | `/tweets/{tweet_id}` | Get tweet by ID |
| PUT | `/tweets/{tweet_id}` | Update tweet |
| DELETE | `/tweets/{tweet_id}` | Delete tweet |

### Admin Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/users` | Get all users |
| GET | `/admin/stats` | Get system statistics |
| DELETE | `/admin/users/{user_id}` | Delete user |

### Interactive API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost/docs
- **ReDoc**: http://localhost/redoc

## 🏗️ Development

### Backend Development

#### Database Migrations

Create a new migration:
```bash
docker-compose exec backend alembic revision --autogenerate -m "description"
```

Apply migrations:
```bash
docker-compose exec backend alembic upgrade head
```

#### Add New Dependencies

1. Update `requirements.txt`
2. Rebuild the Docker image:
```bash
docker-compose up -d --build backend
```

### Frontend Development

#### Add New Dependencies

Add to `gradle/libs.versions.toml` or directly in `app/build.gradle.kts`, then sync Gradle.

#### Code Style

The project follows Kotlin coding conventions. Use Android Studio's built-in formatter.

## 🧪 Testing

### Backend Tests
```bash
docker-compose exec backend python scripts/run_full_test.py
```

### Frontend Tests

Unit tests:
```bash
./gradlew test
```

Instrumented tests:
```bash
./gradlew connectedAndroidTest
```

## 🔒 Security Features

- JWT-based authentication with refresh tokens
- Password hashing with bcrypt
- Rate limiting to prevent abuse
- Security headers via Nginx
- CORS configuration
- Encrypted SharedPreferences on Android
- SQL injection protection via SQLAlchemy ORM
- Input validation with Pydantic

## 📊 Monitoring & Logging

### Backend Monitoring
- Structured JSON logging
- Performance monitoring with psutil
- Request/response logging middleware
- Health check endpoints

### Nginx Logs
Located in `nginx/log/`:
- `access.log` - HTTP access logs
- `error.log` - Error logs

## 🐛 Troubleshooting

### Backend Issues

**Database connection failed:**
- Ensure MySQL container is running: `docker-compose ps`
- Check database credentials in `.env`
- Verify health check: `docker-compose logs mysql`

**Redis connection failed:**
- Check Redis container: `docker-compose ps redis`
- Verify Redis is accessible: `docker-compose exec redis redis-cli ping`

**Port already in use:**
- Change port mapping in `docker-compose.yml`
- Or stop the conflicting service

### Frontend Issues

**Cannot connect to backend:**
- Verify backend is running
- Check BASE_URL configuration
- For emulator, use `10.0.2.2` instead of `localhost`

**Build failed:**
- Clean project: `Build > Clean Project`
- Invalidate caches: `File > Invalidate Caches / Restart`
- Sync Gradle: `File > Sync Project with Gradle Files`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Authors

Gursimar Singh

## 🙏 Acknowledgments

- FastAPI for the excellent Python web framework
- Android team for the robust mobile development platform
- All open-source contributors whose libraries made this project possible

---

**Built with ❤️ using FastAPI and Kotlin**
