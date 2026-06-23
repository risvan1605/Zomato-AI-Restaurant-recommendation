# Lumina Dining - Deployment Plan

This document outlines the strategy for deploying the Lumina Dining AI Recommendation system to production. The architecture is split into two cloud providers to optimize for their respective strengths:

- **Frontend**: Deployed on [Vercel](https://vercel.com/) (Optimized for Next.js, Global CDN, Edge Network)
- **Backend**: Deployed on [Railway](https://railway.app/) (Optimized for Docker/Python, simple scaling, persistent volumes if needed)

---

## 1. Backend Deployment (Railway)

The FastAPI backend will be deployed to Railway as a long-running Python web service.

### 1.1 Prerequisites
- A [Railway Account](https://railway.app/)
- The project pushed to a GitHub repository.

### 1.2 Deployment Steps
1. **Create a New Project**: Go to the Railway dashboard and select **New Project** -> **Deploy from GitHub repo**.
2. **Select Repository**: Choose your `Zomato-AI-Restaurant-recommendation` repository.
3. **Configure Service**:
   - **Root Directory**: Leave as `/` (root of the repo).
   - **Build Command**: Railway will automatically detect the `requirements.txt` file and install the Python dependencies using `pip`.
   - **Start Command**: Railway needs to know how to start the FastAPI server. Go to the service **Settings** -> **Deploy** -> **Custom Start Command** and enter:
     ```bash
     uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
     ```
     *(Note: Railway injects the `$PORT` environment variable automatically).*

### 1.3 Environment Variables
In the Railway dashboard, navigate to the **Variables** tab for your backend service and add the following:

| Variable | Value / Description |
| :--- | :--- |
| `GROQ_API_KEY` | Your Groq API Key for the Llama 3 LLM. |
| `ENVIRONMENT` | `production` |
| `LOG_LEVEL` | `INFO` |

> **IMPORTANT**: Ensure the `GROQ_API_KEY` is set correctly, otherwise the backend will constantly fall back to the metric-based recommendation engine.

### 1.4 Post-Deployment
- Wait for the build and deployment to complete.
- Railway will automatically generate a public domain (e.g., `https://zomato-ai-backend-production.up.railway.app`). 
- **Copy this URL**. You will need it to configure the frontend.
- Test the health check endpoint in your browser: `https://<railway-url>/api/v1/health`.

---

## 2. Frontend Deployment (Vercel)

The Next.js 15 frontend will be deployed on Vercel, which provides native, zero-configuration support for Next.js applications.

### 2.1 Prerequisites
- A [Vercel Account](https://vercel.com/) (linked to your GitHub).
- The Railway backend URL from the previous step.

### 2.2 Deployment Steps
1. **Import Project**: Go to the Vercel dashboard and click **Add New** -> **Project**.
2. **Select Repository**: Import the `Zomato-AI-Restaurant-recommendation` repository.
3. **Configure Project**:
   - **Framework Preset**: Vercel will auto-detect **Next.js**.
   - **Root Directory**: Click "Edit" and select `frontend`. *(This is critical since the Next.js app is located in the `/frontend` subfolder, not the root)*.
   - **Build Command**: Leave as default (`npm run build`).
   - **Install Command**: Leave as default (`npm install`).

### 2.3 Environment Variables
Before clicking "Deploy", expand the **Environment Variables** section and add the connection to your Railway backend:

| Variable | Value |
| :--- | :--- |
| `NEXT_PUBLIC_API_URL` | `https://<your-railway-url>.railway.app/api/v1` |

> **WARNING**: Do **not** include a trailing slash (`/`) at the end of the `NEXT_PUBLIC_API_URL`. Ensure it points exactly to the `/api/v1` path.

### 2.4 Deploy
- Click **Deploy**. Vercel will install the Tailwind dependencies, build the Next.js optimized production bundle, and deploy it to their global Edge network.
- Once finished, you will receive your production URL (e.g., `https://lumina-dining.vercel.app`).

---

## 3. Continuous Integration & Updates

Since both Vercel and Railway are linked directly to your GitHub repository:
- **Automatic Deployments**: Any time you push a new commit to the `main` branch, both platforms will automatically intercept the webhook, rebuild their respective services, and deploy the new version with zero downtime.
- **Preview Environments**: Vercel will automatically generate preview URLs if you open a Pull Request, allowing you to test frontend UI changes before merging them into production.

## 4. Troubleshooting Production

- **CORS Issues**: If the frontend cannot communicate with the backend, check that the FastAPI CORS middleware in `src/api/middleware.py` permits requests from your Vercel domain. *(Currently, the backend allows `["*"]` so this should work out of the box).*
- **Dataset Downloading**: On the very first boot in Railway, the backend will download the Zomato dataset from Hugging Face (~574 MB) and parse it. This may take ~10 seconds. Subsequent boots will be instantaneous.
