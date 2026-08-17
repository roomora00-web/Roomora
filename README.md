# StayMatch - Smart Accommodation and Roommate Matching System

A Django-based backend for a smart accommodation and roommate matching platform built with Python, Django REST Framework, and Neon PostgreSQL.

## Features

- **User Management**: Custom user model with roles (Tenant, Landlord, Admin), profile management, and verification system
- **Property Management**: Comprehensive property listings with amenities, rooms, images, videos, and virtual viewings
- **Booking System**: Full booking workflow with payments, roommate matching, lease agreements, and booking history
- **Review & Feedback**: Property reviews, complaints, property reports, and user feedback system
- **REST API**: Full REST API with JWT authentication using Django REST Framework
- **Admin Panel**: Django admin interface for managing all entities

## Tech Stack

- **Backend**: Django 6.0.6
- **API Framework**: Django REST Framework 3.17.1
- **Authentication**: JWT (djangorestframework-simplejwt 5.5.1)
- **Database**: Neon PostgreSQL
- **Filtering**: django-filter 25.2
- **CORS**: django-cors-headers

## Project Structure

```
staymatch/
├── accounts/          # User management app
│   ├── models.py      # User, UserProfile, Verification models
│   ├── serializers.py # User serializers
│   ├── views.py       # User viewsets
│   └── urls.py        # User API endpoints
├── properties/       # Property management app
│   ├── models.py      # Property, Room, Amenity, Image, Video, Viewing models
│   ├── serializers.py # Property serializers
│   ├── views.py       # Property viewsets
│   └── urls.py        # Property API endpoints
├── bookings/          # Booking management app
│   ├── models.py      # Booking, Payment, RoommateMatch, LeaseAgreement models
│   ├── serializers.py # Booking serializers
│   ├── views.py       # Booking viewsets
│   └── urls.py        # Booking API endpoints
├── feedback/          # Feedback management app
│   ├── models.py      # Review, Complaint, PropertyReport models
│   ├── serializers.py # Feedback serializers
│   ├── views.py       # Feedback viewsets
│   └── urls.py        # Feedback API endpoints
└── staymatch/         # Project settings
    ├── settings.py    # Django settings
    └── urls.py        # Main URL configuration
```

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Neon PostgreSQL account
- Virtual environment (recommended)

### Installation

1. **Clone the repository** (if applicable)
   ```bash
   cd "C:\Users\JUDY\OneDrive\Desktop\New folder"
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install django djangorestframework djangorestframework-simplejwt django-cors-headers django-filter psycopg2-binary
   ```

4. **Configure Neon PostgreSQL**

   Open `staymatch/settings.py` and update the DATABASES section with your Neon PostgreSQL credentials:

   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': 'your_database_name',
           'USER': 'your_username',
           'PASSWORD': 'your_password',
           'HOST': 'your-neon-host.region.aws.neon.tech',
           'PORT': '5432',
       }
   }
   ```

   Replace the placeholder values with your actual Neon PostgreSQL credentials.

5. **Create database migrations**
   ```bash
   python manage.py makemigrations
   ```

6. **Apply migrations**
   ```bash
   python manage.py migrate
   ```

7. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

8. **Run development server**
   ```bash
   python manage.py runserver
   ```

The API will be available at `http://127.0.0.1:8000/`

## API Endpoints

### Authentication
- `POST /api/accounts/token/` - Obtain JWT token
- `POST /api/accounts/token/refresh/` - Refresh JWT token

### Accounts
- `GET/POST /api/accounts/users/` - List/create users
- `GET/PUT/PATCH /api/accounts/users/me/` - Get/update current user
- `GET/POST /api/accounts/profiles/` - List/create user profiles
- `GET/PUT/PATCH /api/accounts/profiles/my_profile/` - Get/update current user profile
- `GET/POST /api/accounts/verifications/` - List/create verifications
- `POST /api/accounts/verifications/{id}/approve/` - Approve verification (admin only)
- `POST /api/accounts/verifications/{id}/reject/` - Reject verification (admin only)

### Properties
- `GET/POST /api/properties/property-types/` - List/create property types
- `GET/POST /api/properties/amenities/` - List/create amenities
- `GET/POST /api/properties/properties/` - List/create properties
- `POST /api/properties/properties/{id}/increment_views/` - Increment property view count
- `GET /api/properties/properties/{id}/rooms/` - Get property rooms
- `GET /api/properties/properties/{id}/images/` - Get property images
- `GET/POST /api/properties/rooms/` - List/create rooms
- `GET/POST /api/properties/property-images/` - List/create property images
- `GET/POST /api/properties/property-videos/` - List/create property videos
- `GET/POST /api/properties/property-viewings/` - List/create property viewings

### Bookings
- `GET/POST /api/bookings/bookings/` - List/create bookings
- `POST /api/bookings/bookings/{id}/approve/` - Approve booking (admin only)
- `POST /api/bookings/bookings/{id}/cancel/` - Cancel booking
- `GET/POST /api/bookings/payments/` - List/create payments
- `GET/POST /api/bookings/roommate-matches/` - List/create roommate matches
- `POST /api/bookings/roommate-matches/{id}/accept/` - Accept roommate match
- `POST /api/bookings/roommate-matches/{id}/reject/` - Reject roommate match
- `GET/POST /api/bookings/booking-requests/` - List/create booking requests
- `POST /api/bookings/booking-requests/{id}/respond/` - Respond to booking request
- `GET/POST /api/bookings/lease-agreements/` - List/create lease agreements
- `GET /api/bookings/booking-history/` - List booking history

### Feedback
- `GET/POST /api/feedback/reviews/` - List/create reviews
- `POST /api/feedback/reviews/{id}/mark_helpful/` - Mark review as helpful
- `POST /api/feedback/reviews/{id}/respond/` - Respond to review
- `GET/POST /api/feedback/review-images/` - List/create review images
- `GET/POST /api/feedback/review-helpful/` - List helpful votes
- `GET/POST /api/feedback/complaints/` - List/create complaints
- `POST /api/feedback/complaints/{id}/resolve/` - Resolve complaint (admin only)
- `GET/POST /api/feedback/property-reports/` - List/create property reports
- `POST /api/feedback/property-reports/{id}/review/` - Review property report (admin only)
- `GET/POST /api/feedback/user-feedback/` - List/create user feedback

## Admin Panel

Access the Django admin panel at `http://127.0.0.1:8000/admin/` using the superuser credentials.

The admin panel includes:
- User management with profiles and verifications
- Property management with images, videos, and viewings
- Booking management with payments and lease agreements
- Review and complaint management

## User Roles

- **TENANT**: Can browse properties, create bookings, submit reviews
- **LANDLORD**: Can manage properties, respond to booking requests
- **ADMIN**: Full access to all features including verification approval

## JWT Authentication

The API uses JWT tokens for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <access_token>
```

Access tokens expire after 60 minutes. Use the refresh endpoint to obtain a new access token.

## CORS Configuration

CORS is configured to allow requests from:
- `http://localhost:3000`
- `http://127.0.0.1:3000`

Update the `CORS_ALLOWED_ORIGINS` in `staymatch/settings.py` to add your frontend URLs.

## Development Notes

- The project uses `accommodation_property` instead of `property` for foreign key fields to avoid conflicts with Python's built-in `property` decorator
- All models include timestamps (`created_at`, `updated_at`)
- The database connection is configured for Neon PostgreSQL - replace placeholder credentials with actual values

## Next Steps

- Configure actual Neon PostgreSQL credentials in settings
- Apply database migrations
- Implement property search and filtering
- Implement roommate matching algorithm
- Create frontend templates

## License

This project is part of the StayMatch smart accommodation and roommate matching system.
