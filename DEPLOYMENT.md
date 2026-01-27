# Deployment Guide

## Prerequisites

- Git installed
- GitHub account
- Google Cloud account (for cloud hosting)
- Python 3.13 installed locally

## 1. GitHub Deployment

### Initial Setup

```bash
# Navigate to project directory
cd "d:\Sciebo\Dokumente\Coding\07_miscellaneous\spectra-simulation"

# Initialize git repository (if not already done)
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: NMR Spectra Simulator web app"

# Create repository on GitHub (via web interface)
# Then link and push:
git remote add origin https://github.com/YOUR_USERNAME/nmr-spectra-simulator.git
git branch -M main
git push -u origin main
```

### Update Repository

```bash
# After making changes
git add .
git commit -m "Description of changes"
git push
```

## 2. Google Cloud Deployment

### Option A: Cloud Run (Recommended - Docker-based)

**Advantages**: Automatic scaling, pay-per-use, supports long requests

```bash
# Install Google Cloud SDK
# https://cloud.google.com/sdk/docs/install

# Login to Google Cloud
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# Build and deploy
gcloud run deploy nmr-simulator \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 3600 \
  --max-instances 10

# Get the service URL
gcloud run services describe nmr-simulator --region us-central1 --format='value(status.url)'
```

### Option B: App Engine (Simpler, less flexible)

```bash
# Create App Engine application
gcloud app create --region=us-central

# Deploy
gcloud app deploy app.yaml

# Open in browser
gcloud app browse
```

### Option C: Compute Engine (Full VM control)

1. Create a VM instance
2. SSH into the VM
3. Clone your GitHub repository
4. Install dependencies and run the app with a process manager (systemd, supervisor)

## 3. Environment Configuration

### Production Settings

Create a production configuration by modifying `web_app.py`:

```python
# At the top of the file, add:
import os

# Replace debug settings:
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False)
```

### Adding gunicorn for Production

Add to `requirements.txt`:
```
gunicorn==21.2.0
```

Create `gunicorn.conf.py`:
```python
bind = "0.0.0.0:8080"
workers = 2
threads = 4
timeout = 300
accesslog = "-"
errorlog = "-"
loglevel = "info"
```

## 4. Domain and SSL

### Custom Domain (Cloud Run)

```bash
# Map custom domain
gcloud run domain-mappings create \
  --service nmr-simulator \
  --domain your-domain.com \
  --region us-central1
```

## 5. Monitoring and Logs

### View Logs

**Cloud Run:**
```bash
gcloud run services logs read nmr-simulator --region us-central1
```

**App Engine:**
```bash
gcloud app logs tail -s default
```

### Monitoring Dashboard

- Access: https://console.cloud.google.com/monitoring
- Set up alerts for errors, high CPU, memory usage

## 6. Costs Estimation

### Cloud Run (Recommended)
- **Free tier**: 2M requests/month, 360,000 GB-seconds
- **After free tier**: ~$0.40 per million requests
- **Typical cost**: $5-20/month for moderate usage

### App Engine
- **Free tier**: 28 instance hours/day
- **After free tier**: ~$0.05/hour for F2 instance
- **Typical cost**: $15-40/month

## 7. Security Best Practices

1. **Enable HTTPS only** (automatically enabled on Cloud Run/App Engine)
2. **Add authentication** if needed (Firebase Auth, OAuth)
3. **Rate limiting** to prevent abuse
4. **Input validation** for all user inputs
5. **CORS configuration** if frontend is on different domain

## 8. Continuous Deployment (CI/CD)

### GitHub Actions for Cloud Run

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - id: 'auth'
        uses: 'google-github-actions/auth@v1'
        with:
          credentials_json: '${{ secrets.GCP_SA_KEY }}'
      
      - name: 'Deploy to Cloud Run'
        uses: 'google-github-actions/deploy-cloudrun@v1'
        with:
          service: 'nmr-simulator'
          region: 'us-central1'
          source: './'
```

## 9. Troubleshooting

### Common Issues

**Memory errors:**
- Increase memory allocation: `--memory 4Gi`

**Timeout errors:**
- Increase timeout: `--timeout 3600`

**Import errors:**
- Verify all dependencies in `requirements.txt`
- Check Python version compatibility

**Static files not loading:**
- Ensure static folder is included in deployment
- Check CORS settings

## 10. Local Testing Before Deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Test with gunicorn locally
gunicorn --bind 0.0.0.0:8080 --workers 1 --threads 4 web_app:app

# Test Docker build
docker build -t nmr-simulator .
docker run -p 8080:8080 nmr-simulator
```

## Support

For issues, check:
- Google Cloud documentation: https://cloud.google.com/docs
- GitHub repository issues section
- Application logs via Cloud Console
