from rest_framework import serializers
 
 
from django.contrib.auth import authenticate
from django.utils.text import slugify
 
from datetime import time as time_type, timedelta
 
from django.utils import timezone
 
from .models import Menu, Reservation, User, Table
 
 
class MenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = Menu
        fields = ["id", "name", "price", "description", "category", "is_available"]
 
 
class UserSerializer(serializers.ModelSerializer):
    user_type = serializers.SerializerMethodField()
 
    def get_user_type(self, obj):
        if obj.is_superuser:
            return 'admin'
        if obj.is_staff:
            return 'staff'
        if obj.role in ('staff', 'admin'):
            return obj.role
        return 'member'
 
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "role", "user_type", "is_staff", "is_superuser", "is_active"]
 
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)
 
    def validate(self, attrs):
        username = (attrs.get("username") or "").strip()
        email = (attrs.get("email") or "").strip().lower()
        password = attrs.get("password")
 
        if not password or (not username and not email):
            raise serializers.ValidationError("username/email and password are required")
 
        request = self.context.get("request")
 
        if email and not username:
            try:
                user = User.objects.get(email__iexact=email)
            except User.DoesNotExist:
                raise serializers.ValidationError("Invalid credentials")
            username = user.get_username()
 
        user = authenticate(request=request, username=username, password=password)
        if user is None:
            raise serializers.ValidationError("Invalid credentials")
 
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled")
 
        attrs["user"] = user
        return attrs
 
 
class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
 
    def validate_email(self, value):
        email = (value or "").strip()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("Email already exists")
        return email
 
    def create(self, validated_data):
        name = (validated_data.get("name") or "").strip()
        email = (validated_data.get("email") or "").strip()
        password = validated_data.get("password")
 
        base = slugify(name).replace("-", "_")
        if not base:
            base = slugify(email.split("@", 1)[0]).replace("-", "_") or "user"
 
        username = base[:150]
        suffix = 1
        while User.objects.filter(username=username).exists():
            suffix += 1
            trimmed = base[: (150 - len(str(suffix)) - 1)]
            username = f"{trimmed}_{suffix}"
 
        user = User(username=username, email=email, first_name=name)
        user.set_password(password)
        user.save()
        return user
 
 
class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = [
            "id",
            "name",
            "email",
            "user",
            "phone",
            "table",
            "date",
            "time",
            "guests",
            "notes",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "user", "created_at"]

    def validate(self, attrs):
        table = attrs.get("table")
        date = attrs.get("date")
        time = attrs.get("time")
        guests = attrs.get("guests")

        if table is not None:
            table_obj = table if isinstance(table, Table) else Table.objects.filter(pk=table).first()
            if table_obj is None:
                raise serializers.ValidationError({"table": "Table does not exist."})
            if table_obj.status in [Table.Status.RESERVED, Table.Status.OCCUPIED]:
                raise serializers.ValidationError({"table": "This table is not available."})
            if guests is not None and guests > table_obj.capacity:
                raise serializers.ValidationError({"guests": "Guest count exceeds table capacity."})

        if date and time:
            queryset = Reservation.objects.filter(date=date, time=time, status__in=["pending", "confirmed"])
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError("This time slot is already booked.")
        return attrs

    def create(self, validated_data):
        table = validated_data.get("table")
        reservation = super().create(validated_data)
        if table is not None:
            table_obj = table if isinstance(table, Table) else Table.objects.get(pk=table)
            if table_obj.status != Table.Status.OCCUPIED:
                table_obj.status = Table.Status.RESERVED
                table_obj.is_available = False
                table_obj.save(update_fields=["status", "is_available"])
        return reservation

class TableSerializer(serializers.ModelSerializer):
    table_id = serializers.IntegerField(source="id", read_only=True)
    table_number = serializers.IntegerField()
 
    class Meta:
        model = Table
        fields = ["table_id", "table_number", "capacity", "is_available", "status"]
        read_only_fields = ["table_id"]
 
