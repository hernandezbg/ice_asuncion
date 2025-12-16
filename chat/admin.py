from django.contrib import admin
from django.utils.html import format_html
from .models import PhoneVerification, ICEChatSession, ICEChatMessage


class ICEChatMessageInline(admin.TabularInline):
    """Mensajes inline dentro de la sesión"""
    model = ICEChatMessage
    extra = 0
    readonly_fields = ['role', 'message_type', 'content_preview', 'created_at']
    fields = ['role', 'message_type', 'content_preview', 'created_at']
    ordering = ['created_at']
    can_delete = False

    def content_preview(self, obj):
        """Muestra preview del contenido"""
        if len(obj.content) > 100:
            return obj.content[:100] + '...'
        return obj.content
    content_preview.short_description = 'Contenido'

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ICEChatSession)
class ICEChatSessionAdmin(admin.ModelAdmin):
    """Admin para sesiones de chat"""
    list_display = ['session_id_short', 'phone', 'message_count', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['phone', 'session_id']
    readonly_fields = ['session_id', 'created_at', 'updated_at']
    inlines = [ICEChatMessageInline]
    ordering = ['-updated_at']

    def session_id_short(self, obj):
        """Muestra ID de sesión corto"""
        return str(obj.session_id)[:8] + '...'
    session_id_short.short_description = 'Sesión'

    def message_count(self, obj):
        """Cuenta mensajes de la sesión"""
        count = obj.messages.count()
        return format_html('<strong>{}</strong>', count)
    message_count.short_description = 'Mensajes'


@admin.register(ICEChatMessage)
class ICEChatMessageAdmin(admin.ModelAdmin):
    """Admin para mensajes individuales"""
    list_display = ['id', 'session_phone', 'role_badge', 'message_type', 'content_preview', 'created_at']
    list_filter = ['role', 'message_type', 'created_at']
    search_fields = ['content', 'session__phone']
    readonly_fields = ['session', 'role', 'message_type', 'content', 'audio_url', 'created_at']
    ordering = ['-created_at']

    def session_phone(self, obj):
        """Muestra el teléfono de la sesión"""
        return obj.session.phone
    session_phone.short_description = 'Teléfono'

    def role_badge(self, obj):
        """Muestra el rol con color"""
        if obj.role == 'user':
            return format_html('<span style="color: #28a745; font-weight: bold;">Usuario</span>')
        return format_html('<span style="color: #007bff; font-weight: bold;">Malaki</span>')
    role_badge.short_description = 'Rol'

    def content_preview(self, obj):
        """Muestra preview del contenido"""
        if len(obj.content) > 80:
            return obj.content[:80] + '...'
        return obj.content
    content_preview.short_description = 'Contenido'


@admin.register(PhoneVerification)
class PhoneVerificationAdmin(admin.ModelAdmin):
    """Admin para verificaciones de teléfono"""
    list_display = ['phone', 'code', 'verified_badge', 'attempts', 'created_at', 'expires_at', 'is_expired_badge']
    list_filter = ['verified', 'created_at']
    search_fields = ['phone']
    readonly_fields = ['phone', 'code', 'verified', 'attempts', 'created_at', 'expires_at']
    ordering = ['-created_at']

    def verified_badge(self, obj):
        """Muestra estado de verificación con color"""
        if obj.verified:
            return format_html('<span style="color: #28a745;">✓ Verificado</span>')
        return format_html('<span style="color: #dc3545;">✗ Pendiente</span>')
    verified_badge.short_description = 'Estado'

    def is_expired_badge(self, obj):
        """Muestra si el código expiró"""
        if obj.is_expired():
            return format_html('<span style="color: #6c757d;">Expirado</span>')
        return format_html('<span style="color: #28a745;">Válido</span>')
    is_expired_badge.short_description = 'Vigencia'
