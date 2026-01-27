# Quick Deployment Commands

## 1. GitHub Setup (First Time)

```powershell
# Navigate to your project
cd "d:\Sciebo\Dokumente\Coding\07_miscellaneous\spectra-simulation"

# Initialize git (if not already)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: NMR Spectra Simulator"

# Create repository on GitHub first, then:
git remote add origin https://github.com/YOUR_USERNAME/nmr-spectra-simulator.git
git branch -M main
git push -u origin main
```

## 2. Google Cloud Run Deployment (Recommended)

### One-Time Setup:
```powershell
# Install Google Cloud SDK
# Download from: https://cloud.google.com/sdk/docs/install

# Login and set project
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Enable APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### Deploy:
```powershell
# From your project directory
cd "d:\Sciebo\Dokumente\Coding\07_miscellaneous\spectra-simulation"

# Deploy to Cloud Run
gcloud run deploy nmr-simulator `
  --source . `
  --platform managed `
  --region us-central1 `
  --allow-unauthenticated `
  --memory 2Gi `
  --cpu 2 `
  --timeout 600 `
  --max-instances 10

# Get your URL
gcloud run services describe nmr-simulator --region us-central1 --format='value(status.url)'
```

## 3. Test Locally with Production Settings

```powershell
# Install dependencies
pip install -r requirements.txt

# Test with gunicorn (like production)
gunicorn --config gunicorn.conf.py web_app:app

# Or test Docker build
docker build -t nmr-simulator .
docker run -p 8080:8080 nmr-simulator

# Access at http://localhost:8080
```

## 4. Update Deployed App

```powershell
# Make your changes, then:
git add .
git commit -m "Description of changes"
git push

# Redeploy to Cloud Run
gcloud run deploy nmr-simulator --source . --region us-central1
```

## 5. Monitor Your App

```powershell
# View logs
gcloud run services logs read nmr-simulator --region us-central1

# Stream live logs
gcloud run services logs tail nmr-simulator --region us-central1

# Open monitoring dashboard
gcloud run services list
# Then visit: https://console.cloud.google.com/run
```

## 6. Cost Management

```powershell
# Set max instances to control costs
gcloud run services update nmr-simulator `
  --max-instances 5 `
  --region us-central1

# View current config
gcloud run services describe nmr-simulator --region us-central1
```

## 7. Custom Domain (Optional)

```powershell
# Map your domain
gcloud run domain-mappings create `
  --service nmr-simulator `
  --domain your-domain.com `
  --region us-central1
```

## 8. Troubleshooting

```powershell
# Check service status
gcloud run services describe nmr-simulator --region us-central1

# View recent errors
gcloud run services logs read nmr-simulator --region us-central1 --limit 50

# Test locally first
python web_app.py

# Check Docker build
docker build -t test-nmr .
docker run -p 8080:8080 test-nmr
```

## Cost Estimate

**Cloud Run Pricing (US):**
- First 2 million requests/month: FREE
- After that: ~$0.40 per million requests
- Memory/CPU: ~$0.00002448 per GB-second
- **Typical monthly cost: $5-20 for moderate use**

## Files Created for Deployment:
- ✅ `.gitignore` - Git ignore rules
- ✅ `requirements.txt` - Python dependencies
- ✅ `runtime.txt` - Python version
- ✅ `Dockerfile` - Container configuration
- ✅ `gunicorn.conf.py` - Production server config
- ✅ `app.yaml` - App Engine config (alternative)
- ✅ `.gcloudignore` - Cloud deployment ignore rules
- ✅ `DEPLOYMENT.md` - Full deployment guide
- ✅ `.github/workflows/deploy.yml` - Auto-deployment (optional)
- ✅ `README.md` - Updated project documentation

## Next Steps:
1. Create GitHub repository
2. Push code to GitHub
3. Set up Google Cloud project
4. Deploy with command above
5. Test your live URL!
