# Deployment Guide - Render Cloud

This guide explains how to deploy the Document Classification System to Render cloud platform using native Python deployment.

## Prerequisites

1. **Render Account**: Sign up at [render.com](https://render.com)
2. **GitHub Repository**: Your code should be in a GitHub repository
3. **AWS Credentials** (optional): For full functionality with AWS Textract and Bedrock

## Deployment Steps

### Automatic Deployment via render.yaml (Recommended)

1. **Push to GitHub**: Ensure your code is in a GitHub repository with all the deployment files:
   - `requirements.txt`
   - `render.yaml`

2. **Connect to Render**:
   - Go to [render.com](https://render.com) and sign in
   - Click "New +" → "Blueprint"
   - Connect your GitHub repository
   - Select the repository containing your document classification system

3. **Configure Environment Variables** in Render dashboard:
   ```
   AWS_ACCESS_KEY_ID=your_aws_access_key
   AWS_SECRET_ACCESS_KEY=your_aws_secret_key
   AWS_REGION=us-east-1
   ENVIRONMENT=production
   LOG_LEVEL=INFO
   ```

4. **Deploy**: Render will automatically use the `render.yaml` configuration and deploy your service.

### Alternative: Manual Web Service Setup

1. **Create Web Service**:
   - Go to Render dashboard
   - Click "New +" → "Web Service"
   - Connect your GitHub repository

2. **Configure Build & Deploy Settings**:
   ```
   Name: document-classification-system
   Environment: Python 3
   Region: Oregon (US West)
   Branch: main (or your main branch)
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

3. **Set Environment Variables**:
   - Go to "Environment" tab in your service settings
   - Add the following variables:
     ```
     PYTHONPATH=/opt/render/project/src
     HOST=0.0.0.0
     AWS_ACCESS_KEY_ID=your_aws_access_key
     AWS_SECRET_ACCESS_KEY=your_aws_secret_key
     AWS_REGION=us-east-1
     ENVIRONMENT=production
     LOG_LEVEL=INFO
     ```

4. **Deploy**: Click "Create Web Service"

## Environment Variables Configuration

### Required Variables
- `HOST`: Set to `0.0.0.0` for Render
- `PORT`: Automatically set by Render
- `ENVIRONMENT`: Set to `production`

### AWS Integration (Optional)
If you want full AWS functionality:
- `AWS_ACCESS_KEY_ID`: Your AWS access key
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret key
- `AWS_REGION`: AWS region (default: us-east-1)

### Optional Variables
- `LOG_LEVEL`: Logging level (INFO, DEBUG, WARNING, ERROR)
- `MAX_FILE_SIZE`: Maximum upload file size in bytes (default: 20MB)

## Fallback Mode

If AWS credentials are not provided, the system will run in **fallback mode**:
- Uses PyPDF for text extraction instead of AWS Textract
- Uses rule-based classification instead of AWS Bedrock
- All core functionality remains available

## Health Check

The service includes a health check endpoint at `/health` that Render will use to monitor service status.

## File Persistence

For evaluation data persistence, the service uses Render's disk storage:
- Mount path: `/opt/render/project/src/data`
- Size: 1GB (configurable in render.yaml)

## Custom Domain (Optional)

To use a custom domain:
1. Go to your service settings in Render
2. Navigate to "Custom Domains"
3. Add your domain and follow DNS configuration instructions

## Monitoring and Logs

- **Logs**: Access real-time logs in Render dashboard under "Logs" tab
- **Metrics**: View performance metrics in "Metrics" tab
- **Scaling**: Configure auto-scaling in "Settings" tab

## Deployment URL

After successful deployment, your service will be available at:
```
https://your-service-name.onrender.com
```

## Troubleshooting

### Common Issues

1. **Build Fails**:
   - Check requirements.txt for correct dependencies
   - Ensure Python version compatibility (3.11 recommended)

2. **Service Won't Start**:
   - Verify start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Check environment variables are set correctly

3. **AWS Services Not Working**:
   - Verify AWS credentials in environment variables
   - Check AWS region is correct
   - System will fallback to offline mode if AWS fails

4. **File Upload Issues**:
   - Check MAX_FILE_SIZE setting
   - Ensure python-magic system dependencies are installed (handled by Dockerfile)

### Logs and Debugging

To view detailed logs:
1. Go to Render dashboard
2. Select your service
3. Click "Logs" tab for real-time log streaming

## Cost Estimation

**Render Starter Plan** (recommended for development):
- Free tier available
- $7/month for starter plan
- Includes 512MB RAM, shared CPU
- 500GB bandwidth

**Render Standard Plan** (recommended for production):
- $25/month
- 2GB RAM, dedicated CPU
- Unmetered bandwidth

## Security Considerations

1. **Environment Variables**: Store sensitive data (AWS keys) in Render's encrypted environment variables
2. **HTTPS**: All Render services use HTTPS by default
3. **File Uploads**: Uploads are validated and stored temporarily
4. **AWS Permissions**: Use least-privilege AWS IAM policies

## Support

For deployment issues:
- Check Render documentation: [render.com/docs](https://render.com/docs)
- Render community: [community.render.com](https://community.render.com)
- This project's logs for application-specific issues