To deploy your Java project using Docker and set up a CI/CD pipeline with GitHub Actions on your Linux server, follow these steps. The documentation outlines the process of containerizing your application, setting up GitHub Actions for CI/CD, and deploying to your Linux server.

---

### **Dockerized Deployment with GitHub Actions CI/CD**

#### **1. Prerequisites**
- **Linux server** (for deployment)
- **GitHub repository** for the project
- **Docker installed** on the Linux server
- **External database** and **Redis** already configured
- **Docker Hub account** (optional) or **private container registry** for storing images

#### **2. Dockerizing Your Java Application**

Create a `Dockerfile` to containerize your Java application. Place it in the root of your project directory.

Here’s an example `Dockerfile`:

```dockerfile
# Use an official OpenJDK image as the base image
FROM openjdk:17-jdk-alpine

# Set the working directory inside the container
WORKDIR /app

# Copy the jar file built from your project to the container
COPY target/yourproject.jar /app/yourproject.jar

# Expose the necessary port (optional, based on your app)
EXPOSE 8080

# Command to run the application
CMD ["java", "-jar", "/app/yourproject.jar"]
```

Make sure your JAR file is built and located in the `target/` directory (if using Maven) or `build/libs/` (if using Gradle).

#### **3. Create a Docker Compose File** (Optional)

If your application relies on external services like Redis and a database, you can use Docker Compose to manage them during local development.

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8080:8080"
    environment:
      - REDIS_HOST=redis
      - DB_HOST=yourdb
    depends_on:
      - redis
      - db

  redis:
    image: redis:latest
    ports:
      - "6379:6379"

  db:
    image: mysql:latest
    environment:
      MYSQL_ROOT_PASSWORD: rootpassword
      MYSQL_DATABASE: yourdatabase
    ports:
      - "3306:3306"
```

#### **4. Setting Up GitHub Actions**

To automate the build and deployment of your project using GitHub Actions, create a file named `.github/workflows/deploy.yml` in your project repository.

Here’s an example GitHub Actions configuration for building and deploying your Docker container to a Linux server via SSH:

```yaml
name: CI/CD Pipeline

on:
  push:
    branches:
      - main

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Set up JDK 17
      uses: actions/setup-java@v3
      with:
        java-version: '17'

    - name: Build with Maven
      run: mvn clean package

    - name: Build Docker image
      run: docker build -t yourusername/yourproject:latest .

    - name: Log in to Docker Hub
      run: echo "${{ secrets.DOCKER_HUB_ACCESS_TOKEN }}" | docker login -u "${{ secrets.DOCKER_HUB_USERNAME }}" --password-stdin

    - name: Push Docker image to Docker Hub
      run: docker push yourusername/yourproject:latest

  deploy:
    runs-on: ubuntu-latest
    needs: build

    steps:
    - name: Deploy to Server via SSH
      uses: appleboy/ssh-action@v0.1.7
      with:
        host: ${{ secrets.SERVER_HOST }}
        username: ${{ secrets.SERVER_USER }}
        key: ${{ secrets.SERVER_SSH_KEY }}
        passphrase: ${{ secrets.SERVER_PASSPHRASE }}
        script: |
          docker pull yourusername/yourproject:latest
          docker stop yourproject || true
          docker rm yourproject || true
          docker run -d --name yourproject -p 8080:8080 yourusername/yourproject:latest
```

#### **5. Setting Up Secrets in GitHub**

To securely store sensitive data (like server SSH credentials and Docker Hub login), add secrets to your GitHub repository.

1. Navigate to your repository on GitHub.
2. Go to **Settings** > **Secrets and variables** > **Actions**.
3. Add the following secrets:
   - **DOCKER_HUB_USERNAME**: Your Docker Hub username.
   - **DOCKER_HUB_ACCESS_TOKEN**: A Docker Hub access token (can be generated from Docker Hub).
   - **SERVER_HOST**: The IP or hostname of your Linux server.
   - **SERVER_USER**: The SSH username for accessing your server.
   - **SERVER_SSH_KEY**: The private SSH key for connecting to your server (paste the key here without line breaks).
   - **SERVER_PASSPHRASE**: (Optional) The passphrase for the SSH key, if used.

#### **6. Install Docker on the Linux Server**

If Docker is not already installed on your server, install it by following these steps:

For **Ubuntu**:
```bash
sudo apt update
sudo apt install docker.io -y
```

For **CentOS**:
```bash
sudo yum install docker -y
```

Enable Docker to start on boot and run it:
```bash
sudo systemctl enable docker
sudo systemctl start docker
```

#### **7. Running the Application on the Server**

Once the GitHub Action runs, the Docker container will be pulled onto your server, stopped if it was running, and restarted with the new version.

To check the status of the application, log into your server and use:

```bash
docker ps -a
```

You can monitor logs with:

```bash
docker logs yourproject
```

#### **8. Conclusion**

By following this process, your Java project will automatically be built and deployed to a Linux server whenever changes are pushed to the `main` branch. The CI/CD pipeline in GitHub Actions handles the entire workflow, from building the Docker image to deploying it on the server.