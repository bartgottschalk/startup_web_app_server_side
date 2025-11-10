from django.db import models
from django.contrib.auth.models import User
#from user.models import Email, Prospect

# Create your models here.
class Configuration(models.Model):
    log_client_events = models.BooleanField(default=True)
    class Meta:
        db_table = 'clientevent_configuration'
    def __str__(self):
        return 'log_client_events: ' + str(self.log_client_events)

class Pageview(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    anonymous_id = models.CharField(max_length=100, null=True)
    url = models.CharField(max_length=1000)
    page_width = models.IntegerField(blank=True, null=True)
    remote_addr = models.CharField(max_length=100, blank=True, null=True)
    http_user_agent = models.CharField(max_length=1000, blank=True, null=True)
    created_date_time = models.DateTimeField()
    def __str__(self):
        return str(self.user_id) + ',' + str(self.anonymous_id) + ',' + str(self.url) + ',' + str(self.remote_addr) + ',' + str(self.created_date_time)
    class Meta:
        db_table = 'clientevent_pageview'

class AJAXError(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    anonymous_id = models.CharField(max_length=100, null=True)
    url = models.CharField(max_length=1000)
    error_id = models.CharField(max_length=100)
    created_date_time = models.DateTimeField()
    def __str__(self):
        return str(self.user_id) + ',' + str(self.anonymous_id) + ',' + str(self.url) + ',' + str(self.error_id) + ',' + str(self.created_date_time)
    class Meta:
        db_table = 'clientevent_ajax_error'

class Buttonclick(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    anonymous_id = models.CharField(max_length=100, null=True)
    url = models.CharField(max_length=1000)
    button_id = models.CharField(max_length=100)
    created_date_time = models.DateTimeField()
    def __str__(self):
        return str(self.user_id) + ',' + str(self.anonymous_id) + ',' + str(self.url) + ',' + str(self.button_id) + ',' + str(self.created_date_time)
    class Meta:
        db_table = 'clientevent_button_click'

class Linkevent(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    prospect = models.ForeignKey('user.Prospect', on_delete=models.SET_NULL, null=True)
    anonymous_id = models.CharField(max_length=100, null=True)
    email = models.ForeignKey('user.Email', on_delete=models.SET_NULL, null=True)
    ad = models.ForeignKey('user.Ad', on_delete=models.SET_NULL, null=True)
    url = models.CharField(max_length=1000)
    created_date_time = models.DateTimeField()
    def __str__(self):
        return "user: " + str(self.user_id) + ', prospect: ' + str(self.prospect) + ', anonymous: ' + str(self.anonymous_id) + ', ' + str(self.url) + ', ' + str(self.created_date_time)
    class Meta:
        db_table = 'clientevent_linkevent'

