# 🚀 Deployment Guide

This guide will help you deploy the Multi-Hop Reasoning Agent to Streamlit Cloud.

## 📋 Prerequisites

1. **GitHub Account**: You need a GitHub account to host your code
2. **Google Cloud Project**: Set up a Google Cloud project with Vertex AI enabled
3. **API Credentials**: Generate Google API credentials and service account keys

## 🔑 Setting Up Google Cloud Credentials

### 1. Create a Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Vertex AI API

### 2. Create Service Account
1. Go to IAM & Admin → Service Accounts
2. Click "Create Service Account"
3. Give it a name (e.g., "streamlit-agent")
4. Grant the following roles:
   - Vertex AI User
   - Vertex AI Service Agent

### 3. Generate JSON Key
1. Click on your service account
2. Go to "Keys" tab
3. Click "Add Key" → "Create New Key"
4. Choose JSON format
5. Download the key file

### 4. Get API Key
1. Go to APIs & Services → Credentials
2. Click "Create Credentials" → "API Key"
3. Copy the API key

## 🐙 GitHub Setup

### 1. Fork the Repository
1. Go to the original repository
2. Click "Fork" in the top right
3. Clone your forked repository locally

### 2. Update Configuration
1. Edit `multi_hop_agent/config/settings.py` if needed
2. Update `setup.py` with your information
3. Commit and push your changes

## ☁️ Streamlit Cloud Deployment

### 1. Deploy to Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click "New app"
4. Select your forked repository
5. Set the main file path to `streamlit_app.py`
6. Click "Deploy!"

### 2. Configure Secrets
1. In your Streamlit app, go to Settings → Secrets
2. Add your Google API credentials in TOML format:

```toml
[google]
api_key = "your_actual_api_key_here"
service_account_json = "your_full_json_content_here"

[llm]
model = "gemini-2.5-flash"
```

**Note**: Temperature, top_p, and top_k are now configurable directly in the Streamlit UI with sliders. The default values are:
- Temperature: 0.1 (focused responses)
- Top-p: 0.95 (balanced diversity)
- Top-k: 40 (balanced vocabulary diversity)

### 3. Alternative: Environment Variables
If you prefer environment variables, you can set them in Streamlit Cloud:
1. Go to Settings → General
2. Add environment variables:
   - `GOOGLE_API_KEY`
   - `GOOGLE_CREDENTIALS_PATH`
   - `LLM_MODEL_NAME`

## 🔒 Security Best Practices

### 1. Never Commit Credentials
- ✅ Use Streamlit secrets in production
- ❌ Never hardcode API keys in code
- ❌ Never commit credential files

### 2. Environment-Specific Configuration
- **Production**: Use Streamlit secrets
- **CI/CD**: Use environment variables

### 3. Access Control
- Limit service account permissions
- Use least-privilege access
- Regularly rotate credentials

## 🧪 Testing Your Deployment

### 1. Basic Functionality
1. Open your deployed Streamlit app
2. Try a simple question
3. Check if the agent responds
4. Verify error handling

### 2. Error Handling
1. Test with invalid credentials
2. Test with network issues
3. Verify user-friendly error messages

### 3. Performance
1. Monitor response times
2. Check resource usage
3. Test with different question types

## 🚨 Troubleshooting

### Common Issues

#### 1. "GOOGLE_API_KEY not found"
- Check Streamlit secrets configuration
- Verify the secret name matches exactly
- Ensure the secret is properly formatted

#### 2. "Authentication failed"
- Verify your service account key is correct
- Check if Vertex AI API is enabled
- Ensure proper IAM permissions

#### 3. "Module not found"
- Check `requirements.txt` includes all dependencies
- Verify package names match exactly
- Check Python version compatibility

#### 4. "Permission denied"
- Verify service account has proper roles
- Check if the project is active
- Ensure billing is enabled

### Debug Steps
1. Check Streamlit logs in the app
2. Verify environment variables are set
3. Test credentials locally first
4. Check Google Cloud Console for errors

## 📊 Monitoring

### 1. Streamlit Analytics
- View app usage statistics
- Monitor performance metrics
- Track user interactions

### 2. Google Cloud Monitoring
- Monitor API usage
- Track costs
- Set up alerts for quotas

### 3. Application Logs
- Check Streamlit logs
- Monitor agent execution
- Track error rates

## 🔄 Updates and Maintenance

### 1. Code Updates
1. Make changes locally
2. Test thoroughly
3. Push to GitHub
4. Streamlit Cloud auto-deploys

### 2. Dependency Updates
1. Update `requirements.txt`
2. Test locally
3. Deploy and verify

### 3. Credential Rotation
1. Generate new credentials
2. Update Streamlit secrets
3. Test functionality
4. Remove old credentials

## 📚 Additional Resources

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Google Cloud Vertex AI](https://cloud.google.com/vertex-ai/docs)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Streamlit Community Cloud](https://share.streamlit.io/)

## 🆘 Getting Help

If you encounter issues:
1. Check the troubleshooting section above
2. Review Streamlit and Google Cloud logs
3. Search existing GitHub issues
4. Create a new issue with detailed information
5. Include error messages and reproduction steps 