# Updated version using subscription_id instead of price_id

import stripe
from django.conf import settings
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Subscription
from .serializers import (
    StripeSessionResponseSerializer,
    MessageResponseSerializer,
    ErrorResponseSerializer,
)

stripe.api_key = settings.STRIPE_SECRET_KEY


class CreateCheckoutSessionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Create a Stripe Checkout Session for a subscription.",
        manual_parameters=[
            openapi.Parameter(
                'subscription_id', openapi.IN_QUERY,
                description="Stripe Price ID of the subscription plan",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: StripeSessionResponseSerializer,
            400: ErrorResponseSerializer,
        }
    )
    def post(self, request):
        user = request.user
        price_id = request.query_params.get('subscription_id')

        if not price_id:
            return Response({'error': 'subscription_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        subscription, _ = Subscription.objects.get_or_create(user=user)

        if not subscription.stripe_customer_id:
            customer = stripe.Customer.create(email=user.email)
            subscription.stripe_customer_id = customer.id
            subscription.save()

        try:
            checkout_session = stripe.checkout.Session.create(
                customer=subscription.stripe_customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=f'{settings.FRONTEND_URL}/success?session_id={{CHECKOUT_SESSION_ID}}',
                cancel_url=f'{settings.FRONTEND_URL}/cancel',
            )

            return Response({'sessionId': checkout_session.id}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class StripeWebhookView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Handle Stripe webhook events.",
        responses={
            200: openapi.Response(description="Webhook processed"),
            400: openapi.Response(description="Invalid payload or signature"),
        }
    )
    def post(self, request):
        payload = request.body
        sig_header = request.headers.get('stripe-signature')
        endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        except (ValueError, stripe.error.SignatureVerificationError):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            customer_id = session.get('customer')
            subscription_id = session.get('subscription')

            if customer_id and subscription_id:
                try:
                    subscription = Subscription.objects.get(stripe_customer_id=customer_id)
                    subscription.stripe_subscription_id = subscription_id
                    subscription.is_active = True
                    subscription.current_period_end = timezone.now() + timezone.timedelta(days=30)
                    subscription.save()
                except Subscription.DoesNotExist:
                    pass

        return Response(status=status.HTTP_200_OK)


class CancelSubscriptionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Cancel the current user's active subscription.",
        responses={
            200: MessageResponseSerializer,
            400: ErrorResponseSerializer,
            404: ErrorResponseSerializer
        }
    )
    def post(self, request):
        user = request.user
        try:
            subscription = Subscription.objects.get(user=user, is_active=True)

            if not subscription.stripe_subscription_id:
                return Response({"error": "No active subscription found."}, status=status.HTTP_400_BAD_REQUEST)

            stripe.Subscription.delete(subscription.stripe_subscription_id)

            subscription.is_active = False
            subscription.stripe_subscription_id = None
            subscription.current_period_end = None
            subscription.save()

            return Response({"message": "Subscription cancelled successfully."}, status=status.HTTP_200_OK)

        except Subscription.DoesNotExist:
            return Response({"error": "Subscription not found."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
