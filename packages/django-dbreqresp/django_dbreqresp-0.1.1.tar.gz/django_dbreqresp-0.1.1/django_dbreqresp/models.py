from django.conf import settings
from django.db import models
from django.utils.timezone import now
import logging

class RequestLog(models.Model):
    created_at= models.DateTimeField(auto_now_add=True)
    method = models.CharField(max_length=10)
    url = models.TextField()
    request_body = models.TextField(blank=True, default="")
    response_status = models.IntegerField()
    response_body = models.TextField(blank=True, default="")
    start = models.DateTimeField()
    end = models.DateTimeField()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, default=None
    )

    def __str__(self):
        return f"{self.method} {self.url} by {self.user} at {self.start}"

    @property
    def duration(self):
        return self.end - self.start

    @classmethod
    def store(cls, request, response, start):
        end = now()

        try:
            user = None
            if request.user.is_authenticated:
                user = request.user

            try:
                request_body = request.body.decode()
            except UnicodeDecodeError:
                request_body = request.body

            try:
                response_body = (response.content or b"").decode()
            except UnicodeDecodeError:
                response_body = response.content or b""

            return cls.objects.create(
                method=request.method,
                url=request.path,
                request_body=request_body,
                response_status=response.status_code,
                response_body=response_body,
                start=start,
                end=end,
                user=user,
            )
        except Exception:
            logging.exception("an error occured while storing data about api call")
        return None
