from rest_framework import generics, mixins, viewsets
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.contrib.auth import login, logout
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.utils.decorators import method_decorator

from .models import Menu, Reservation, Table
from .serializers import (
    LoginSerializer,
    MenuSerializer,
    RegisterSerializer,
    ReservationSerializer,
    TableSerializer,
    UserSerializer,
)


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        user = request.user
        return (
            getattr(user, "is_authenticated", False)
            and (
                getattr(user, "role", None) in {"staff", "admin"}
                or getattr(user, "is_staff", False)
                or getattr(user, "is_superuser", False)
            )
        )


class MenuViewSet(viewsets.ModelViewSet):
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer
    permission_classes = [IsAdminOrReadOnly]


class StaffOnlyDeletePermission(BasePermission):
    def has_permission(self, request, view):
        if getattr(view, "action", None) != "destroy":
            return True

        user = request.user
        if not getattr(user, "is_authenticated", False):
            return False

        return (
            getattr(user, "role", None) in {"staff", "admin"}
            or getattr(user, "is_staff", False)
            or getattr(user, "is_superuser", False)
        )

class StaffOnlyReadAuthenticatedCreate(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if request.method in {"GET", "HEAD", "OPTIONS"}:
            if not getattr(user, "is_authenticated", False):
                return False
            return (
                getattr(user, "role", None) in {"staff", "admin"}
                or getattr(user, "is_staff", False)
                or getattr(user, "is_superuser", False)
            )
        if request.method == "POST":
            return getattr(user, "is_authenticated", False)
        if not getattr(user, "is_authenticated", False):
            return False
        return (
            getattr(user, "role", None) in {"staff", "admin"}
            or getattr(user, "is_staff", False)
            or getattr(user, "is_superuser", False)
        )


class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all().order_by("-created_at")
    serializer_class = ReservationSerializer
    permission_classes = [StaffOnlyDeletePermission, StaffOnlyReadAuthenticatedCreate]

    def get_queryset(self):
        qs = super().get_queryset()
        user_id = self.request.query_params.get("user_id")
        status_value = self.request.query_params.get("status")

        if user_id:
            try:
                qs = qs.filter(user_id=int(user_id))
            except (TypeError, ValueError):
                return qs.none()

        if status_value:
            qs = qs.filter(status=status_value)

        return qs

    def perform_create(self, serializer):
        reservation = serializer.save(user=self.request.user)
        table = reservation.table
        if table and table.status == Table.Status.AVAILABLE:
            table.status = Table.Status.RESERVED
            table.is_available = False
            table.save(update_fields=["status", "is_available"])

    def perform_update(self, serializer):
        reservation = serializer.save()
        table = reservation.table
        if reservation.status == Reservation.Status.CANCELLED and table and table.status == Table.Status.RESERVED:
            table.status = Table.Status.AVAILABLE
            table.is_available = True
            table.save(update_fields=["status", "is_available"])


class ReservationListCreateView(generics.ListCreateAPIView):
    queryset = Reservation.objects.all().order_by("-created_at")
    serializer_class = ReservationSerializer
    permission_classes = [StaffOnlyReadAuthenticatedCreate]

    def get_queryset(self):
        qs = super().get_queryset()
        user_id = self.request.query_params.get("user_id")
        status_value = self.request.query_params.get("status")

        if user_id:
            try:
                qs = qs.filter(user_id=int(user_id))
            except (TypeError, ValueError):
                return qs.none()

        if status_value:
            qs = qs.filter(status=status_value)

        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MyReservationListView(generics.ListAPIView):
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Reservation.objects.filter(user=self.request.user).order_by("-created_at")
        status_value = self.request.query_params.get("status")
        if status_value:
            qs = qs.filter(status=status_value)
        return qs


class MyReservationCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        reservation = get_object_or_404(Reservation, pk=pk, user=request.user)
        if reservation.status != Reservation.Status.PENDING:
            return Response({"success": False, "message": "Only pending reservations can be cancelled."}, status=400)

        reservation.status = Reservation.Status.CANCELLED
        reservation.save(update_fields=["status"])
        return Response({"success": True, "data": ReservationSerializer(reservation).data})


@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {
                "success": True,
                "message": "Register endpoint is working. Send a POST request with name, email, and password to create an account.",
                "data": {"required": ["name", "email", "password"]},
            }
        )

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "message": "Invalid data", "data": serializer.errors}, status=400)

        user = serializer.save()
        return Response(
            {"success": True, "message": "Registration successful", "user": UserSerializer(user).data},
            status=201,
        )


@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {
                "success": True,
                "message": "Login endpoint is working. Send a POST request with username/email and password to create a session.",
                "data": {"required": ["password"], "optional": ["username", "email"]},
            }
        )

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(
                {"success": False, "message": "Invalid credentials", "data": serializer.errors},
                status=400,
            )

        user = serializer.validated_data["user"]
        login(request, user)

        return Response(
            {
                "success": True,
                "message": "Login successful",
                "user": UserSerializer(user).data,
            }
        )


@method_decorator(csrf_exempt, name='dispatch')
class LogoutView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def _logout(self, request):
        if getattr(request.user, "is_authenticated", False):
            logout(request)
        request.session.flush()
        return Response({"success": True, "message": "Logged out"})

    def get(self, request):
        return self._logout(request)

    def post(self, request):
        return self._logout(request)


class CSRFView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        return Response({"success": True, "message": "CSRF cookie set"})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "success": True,
                "user": UserSerializer(request.user).data,
            }
        )


class TableViewSet(viewsets.ModelViewSet):
    queryset = Table.objects.all()
    serializer_class = TableSerializer
    permission_classes = [StaffOnlyDeletePermission]

    def get_queryset(self):
        qs = super().get_queryset()
        is_available = self.request.query_params.get("is_available")
        date = self.request.query_params.get("date")
        time = self.request.query_params.get("time")
        guests = self.request.query_params.get("guests")

        if guests:
            try:
                qs = qs.filter(capacity__gte=int(guests))
            except (TypeError, ValueError):
                return qs.none()

        if date and time:
            booked_table_ids = Reservation.objects.filter(
                date=date, time=time, status__in=["pending", "confirmed"]
            ).exclude(table__isnull=True).values_list("table_id", flat=True)
            qs = qs.exclude(id__in=booked_table_ids).exclude(status=Table.Status.OCCUPIED)

        if is_available is not None:
            qs = qs.filter(is_available=is_available.lower() == "true")

        return qs