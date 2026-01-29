#  Spring Boot Generator

**Spring Boot Generator** is an interactive CLI tool that generates **production-ready Spring Boot applications** in seconds.

It helps developers bootstrap clean, modular, Docker-ready Java projects following industry best practices.

---

##  Features

- Interactive command-line interface
- Java **17** and **21** support
- Modular and scalable project structure
- Clean layered architecture (Controller / Service / Repository)
- Multi-database support
- Docker & Docker Compose ready
- Swagger UI & ReDoc documentation
- Spring Data JPA + Hibernate
- Flyway database migrations
- MapStruct mapper configuration
- Production-grade `pom.xml`

---

## 🧱 Generated Project Structure

```text
com.example.demo
├── Application.java
├── config
├── modules
│   └── user
│       ├── controller
│       ├── service
│       │   └── impl
│       ├── repository
│       ├── dto
│       ├── entity
│       └── mapper
└── resources
    ├── application.yml
    └── db
        └── migration
```

---

##  Supported Databases

- PostgreSQL
- MySQL
- MariaDB
- H2 (in-memory)

Each option includes:
- JDBC driver
- Hibernate configuration
- Docker service (if enabled)

---

## 📦 Installation

```bash
pip install springboot-generator
```

---

## ▶ Usage

```bash
springboot-generator
```

The CLI will guide you through:
- Base package name
- Java version
- Database selection
- Docker enablement
- Swagger / ReDoc configuration
- Module creation

---

## 🐳 Docker Usage

```bash
cd your-project
docker compose up --build
```

Access:
- API: http://localhost:8080
- Swagger UI: http://localhost:8080/swagger-ui.html
- ReDoc: http://localhost:8080/redoc.html
- OpenAPI: http://localhost:8080/v3/api-docs

---

##  Database & Migrations

Flyway is enabled by default.

```text
src/main/resources/db/migration
```

---

##  Windows Users

If the command is not recognized:

```text
'springboot-generator' is not recognized
```

Add to PATH:

```text
C:\Users\<USERNAME>\AppData\Roaming\Python\Python3X\Scripts
```

Or run:

```bash
python -m springboot_generator.main
```

---

##  Requirements

- Python ≥ 3.9
- Java ≥ 17
- Maven ≥ 3.6
- Docker (optional)

---

##  Contributing

Contributions and feedback are welcome.

---

##  License

Apache License 2.0
