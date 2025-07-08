# Fadih.org - Global Corruption Document Exposure Platform

**Fadih** (Arabic for "reveal" or "make apparent") is an anonymous platform for exposing corruption documents worldwide. Citizens and journalists can upload evidence of corruption, which is reviewed by administrators and made searchable by anyone globally.

## Features

- **Anonymous Document Upload**: Secure, anonymous submission of corruption evidence
- **Admin Review System**: Document approval workflow with admin dashboard
- **Global Search**: Search corruption documents by country, keyword, organization
- **Country Statistics**: View corruption document distribution worldwide
- **Secure Storage**: Documents stored securely on Exoscale S3
- **Responsive Design**: Works on desktop, tablet, and mobile devices

## Stack

- **Frontend**: React + TypeScript with Vite, shadcn/ui components
- **Backend**: FastAPI with SQLAlchemy, MySQL database
- **Storage**: Exoscale S3 for document storage
- **Infrastructure**: Terraform for cloud deployment on Exoscale
- **Authentication**: JWT-based admin authentication
- **Package Managers**: `yarn` (frontend), `uv` (backend)

## Local Development

1. Install dependencies:

```bash
make
```

2. Start the backend and frontend servers in separate terminals:

```bash
make run-backend
make run-frontend
```

The backend server runs on port 8000 and the frontend development server runs on port 5173. The frontend Vite server proxies API requests to the backend on port 8000.

Visit <http://localhost:5173> to view the application.

## Production Deployment

This project is deployed on Exoscale cloud infrastructure using Terraform:

- **Live Site**: http://159.100.250.145
- **API Documentation**: http://159.100.250.145/api/docs
- **Admin Login**: http://159.100.250.145/admin-login-page

### Deployment Commands

```bash
# Deploy to production server
./deploy.sh

# Run locally with production-like setup
./run-local.sh
```

## Environment Variables

Key environment variables needed:

- `DATABASE_URL`: MySQL connection string
- `EXOSCALE_S3_*`: S3 storage credentials
- `JWT_SECRET_KEY`: JWT token signing key
- `ADMIN_EMAIL` / `ADMIN_PASSWORD`: Admin credentials
- `SENDGRID_API_KEY`: Email notifications

See `.env.example` for complete configuration.

## Contributing

Fadih.org is dedicated to fighting corruption through transparency. All contributions that advance this mission are welcome.

## License

This project is open source and available for use in fighting corruption worldwide.
